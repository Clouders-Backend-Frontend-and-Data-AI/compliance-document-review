import hashlib
import logging
import math
import re
from typing import List

from data_engineering.config import get_settings

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", "should",
    "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "you", "your", "yours", "yourself", "yourselves",
}


def _stable_token_hash(token: str, dim: int) -> int:
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest, 16) % dim


def local_embed(text: str, dim: int = 768) -> List[float]:
    """Deterministic offline embedding (stable across processes)."""
    vec = [0.0] * dim
    words = re.findall(r"\b[a-z0-9_]{2,}\b", (text or "").lower())
    filtered = [w for w in words if w not in STOP_WORDS] or words
    if not filtered:
        return vec

    for i, word in enumerate(filtered):
        h1 = _stable_token_hash(word, dim)
        vec[h1] += 2.0
        if i > 0:
            h2 = _stable_token_hash(f"{filtered[i - 1]}_{word}", dim)
            vec[h2] += 3.0

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class EmbeddingClient:
    """
    Gemini embedding API with deterministic local fallback.
    Always returns vectors of `embedding_dimension` length.
    """

    def __init__(self):
        settings = get_settings()
        self._model = settings.embedding_model
        self._batch_size = settings.embedding_batch_size
        self._dimension = settings.embedding_dimension
        self._api_key = (settings.gemini_api_key or "").strip()
        self._genai = None
        if self._api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._api_key)
                self._genai = genai
            except Exception as exc:
                logger.warning("Gemini embedding SDK unavailable: %s", exc)
                self._genai = None

    def _embed_batch_gemini(self, texts: List[str]) -> List[List[float]]:
        assert self._genai is not None
        result = self._genai.embed_content(
            model=self._model,
            content=texts,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=self._dimension,
        )
        embeddings = result["embedding"]
        if isinstance(embeddings[0], float):
            embeddings = [embeddings]
        for emb in embeddings:
            if len(emb) != self._dimension:
                raise ValueError(
                    f"Unexpected embedding dimension: got {len(emb)}, expected {self._dimension}"
                )
        return embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed texts. IMPORTANT: callers must pass masked text only."""
        if not texts:
            return []

        if not self._genai:
            return [local_embed(t, self._dimension) for t in texts]

        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            try:
                all_embeddings.extend(self._embed_batch_gemini(batch))
            except Exception as exc:
                logger.warning("Gemini embed failed (%s); using local fallback for batch", exc)
                all_embeddings.extend(local_embed(t, self._dimension) for t in batch)
        return all_embeddings

    def embed_single(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]
