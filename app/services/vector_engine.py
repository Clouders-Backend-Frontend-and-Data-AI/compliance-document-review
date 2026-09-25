import hashlib
import json
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.base import DocumentStatus, DocumentType, RuleCategory
from app.models.vector_corpus import ComplianceRule, PrecedentSubmission

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

# Disclosure applicability by document type (reduces false "missing" flags)
DISCLOSURE_APPLICABILITY: Dict[str, set] = {
    "BANK-DISC-01": {
        DocumentType.BROCHURE,
        DocumentType.PROPOSAL_LETTER,
        DocumentType.MARKETING_EMAIL,
        DocumentType.OTHER,
    },
    "SOCIAL-DISC-01": {DocumentType.SOCIAL_POST, DocumentType.MARKETING_EMAIL},
    "SEC-TEST-01": {DocumentType.SOCIAL_POST, DocumentType.MARKETING_EMAIL, DocumentType.BROCHURE},
}


def _stable_hash(token: str, dim: int) -> int:
    return int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim


class VectorEngine:
    """Vector similarity & semantic retrieval with a single embedding space."""

    EMBED_DIM = None  # resolved from settings

    @classmethod
    def embed_dim(cls) -> int:
        return int(getattr(settings, "EMBEDDING_DIMENSION", 768) or 768)

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        dim = cls.embed_dim()
        if not text or not text.strip():
            return [0.0] * dim

        clean_text = text.strip()
        api_key = (settings.GEMINI_API_KEY or "").strip()

        if api_key:
            try:
                # Prefer header auth; avoid putting the key in the URL/query string
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    "text-embedding-004:embedContent"
                )
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": clean_text[:2048]}]},
                    "outputDimensionality": dim,
                }
                headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        values = data.get("embedding", {}).get("values", [])
                        if values:
                            return cls._normalize_to_dim(values, dim)
            except Exception as exc:
                logger.warning("Gemini embedding failed: %s. Using local vectorizer.", exc)

        return cls._generate_local_embedding(clean_text, dim=dim)

    @classmethod
    def _normalize_to_dim(cls, values: List[float], dim: int) -> List[float]:
        arr = np.array(values, dtype=np.float32)
        if arr.size < dim:
            arr = np.pad(arr, (0, dim - arr.size))
        elif arr.size > dim:
            arr = arr[:dim]
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()

    @classmethod
    def _generate_local_embedding(cls, text: str, dim: int = 768) -> List[float]:
        vec = np.zeros(dim, dtype=np.float32)
        words = re.findall(r"\b[a-z0-9_]{2,}\b", text.lower())
        filtered = [w for w in words if w not in STOP_WORDS] or words
        for i, word in enumerate(filtered):
            vec[_stable_hash(word, dim)] += 2.0
            if i > 0:
                vec[_stable_hash(f"{filtered[i - 1]}_{word}", dim)] += 3.0
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
        """Overlapping character windows with paragraph preference."""
        if not text:
            return []

        # Prefer DE chunker when available (token-aware + overlap)
        try:
            from app.services.de_bridge import chunk_masked_text

            de_chunks = chunk_masked_text(text)
            if de_chunks:
                return de_chunks
        except Exception as exc:
            logger.debug("DE chunker unavailable: %s", exc)

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        # Sliding windows over joined text to honor overlap
        joined = "\n\n".join(paragraphs)
        if len(joined) <= chunk_size:
            return [joined]

        step = max(1, chunk_size - overlap)
        chunks = []
        for start in range(0, len(joined), step):
            piece = joined[start : start + chunk_size].strip()
            if piece:
                chunks.append(piece)
            if start + chunk_size >= len(joined):
                break
        return chunks or [joined]

    @classmethod
    def cosine_sim(cls, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        dim = min(len(vec1), len(vec2))
        if dim == 0:
            return 0.0
        v1 = np.array(vec1[:dim], dtype=np.float32)
        v2 = np.array(vec2[:dim], dtype=np.float32)
        norm1 = float(np.linalg.norm(v1))
        norm2 = float(np.linalg.norm(v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @classmethod
    def _load_embedding(cls, embedding_json: Optional[str], fallback_text: str) -> List[float]:
        if embedding_json:
            try:
                values = json.loads(embedding_json)
                if isinstance(values, list) and values:
                    return cls._normalize_to_dim(values, cls.embed_dim())
            except Exception:
                pass
        return cls.generate_embedding(fallback_text)

    @classmethod
    def retrieve_relevant_rules(
        cls,
        db: Session,
        document_chunks: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        rules = db.query(ComplianceRule).all()
        if not rules:
            return []

        chunk_embeddings = [cls.generate_embedding(c) for c in document_chunks]
        rule_scores: Dict[str, Tuple[float, ComplianceRule, str]] = {}

        for rule in rules:
            rule_text_to_embed = rule.rule_text + " " + rule.title
            if rule.standard_disclosure:
                rule_text_to_embed += " " + rule.standard_disclosure
            rule_vec = cls._load_embedding(rule.embedding_json, rule_text_to_embed)

            max_score = 0.0
            best_chunk = ""
            for idx, c_vec in enumerate(chunk_embeddings):
                sim = cls.cosine_sim(c_vec, rule_vec)
                if sim > max_score:
                    max_score = sim
                    best_chunk = document_chunks[idx]
            rule_scores[rule.id] = (max_score, rule, best_chunk)

        sorted_rules = sorted(rule_scores.values(), key=lambda x: x[0], reverse=True)
        results = []
        for score, rule, matching_chunk in sorted_rules[:top_k]:
            results.append(
                {
                    "rule_id": rule.id,
                    "rule_code": rule.rule_code,
                    "category": rule.category.value,
                    "title": rule.title,
                    "rule_text": rule.rule_text,
                    "similarity_score": round(score, 4),
                    "matched_passage": matching_chunk,
                }
            )
        return results

    @classmethod
    def detect_missing_disclosures(
        cls,
        db: Session,
        document_chunks: List[str],
        threshold: Optional[float] = None,
        document_type: Optional[DocumentType] = None,
    ) -> List[Dict[str, Any]]:
        if threshold is None:
            threshold = settings.DISCLOSURE_ABSENCE_THRESHOLD

        disclosure_rules = (
            db.query(ComplianceRule)
            .filter(ComplianceRule.category == RuleCategory.REQUIRED_DISCLOSURE)
            .all()
        )
        if not disclosure_rules:
            return []

        chunk_embeddings = [cls.generate_embedding(c) for c in document_chunks]
        joined_lower = " ".join(document_chunks).lower()
        missing = []

        for rule in disclosure_rules:
            applicable = DISCLOSURE_APPLICABILITY.get(rule.rule_code)
            if document_type is not None and applicable is not None and document_type not in applicable:
                continue

            disc_text = rule.standard_disclosure or rule.rule_text
            # Lexical short-circuit: near-verbatim disclosure counts as present
            # (local hash embeddings can under-score exact paraphrases).
            disc_lower = (disc_text or "").lower().strip()
            if disc_lower and (
                disc_lower in joined_lower
                or cls._token_overlap_ratio(disc_lower, joined_lower) >= 0.72
            ):
                continue

            disc_vec = cls._load_embedding(rule.embedding_json, disc_text)
            max_sim = 0.0
            for c_vec in chunk_embeddings:
                max_sim = max(max_sim, cls.cosine_sim(c_vec, disc_vec))

            if max_sim < threshold:
                missing.append(
                    {
                        "rule_id": rule.id,
                        "rule_code": rule.rule_code,
                        "title": rule.title,
                        "standard_disclosure": disc_text,
                        "max_similarity_found": round(max_sim, 4),
                        "threshold": threshold,
                        "reason": (
                            f"Required mandatory disclosure '{rule.title}' was not found "
                            f"(Max similarity: {round(max_sim, 2)} < {threshold})."
                        ),
                    }
                )
        return missing

    @staticmethod
    def _token_overlap_ratio(needle: str, haystack: str) -> float:
        stop = STOP_WORDS
        n_tokens = {t for t in re.findall(r"[a-z0-9]+", needle) if t not in stop and len(t) > 2}
        if not n_tokens:
            return 0.0
        h_tokens = set(re.findall(r"[a-z0-9]+", haystack))
        return len(n_tokens & h_tokens) / len(n_tokens)

    @classmethod
    def search_precedents(
        cls,
        db: Session,
        masked_document_text: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        # Prefer final decisions for precedent quality
        precedents = (
            db.query(PrecedentSubmission)
            .filter(
                PrecedentSubmission.decision.in_(
                    [DocumentStatus.APPROVED, DocumentStatus.REJECTED]
                )
            )
            .all()
        )
        if not precedents:
            precedents = db.query(PrecedentSubmission).all()
        if not precedents:
            return []

        doc_vec = cls.generate_embedding(masked_document_text[:3000])
        matches = []
        for p in precedents:
            p_vec = cls._load_embedding(p.embedding_json, p.masked_text[:3000])
            matches.append((cls.cosine_sim(doc_vec, p_vec), p))

        matches.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, p in matches[:top_k]:
            snippet = p.masked_text[:200] + ("..." if len(p.masked_text) > 200 else "")
            results.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "document_type": p.document_type.value,
                    "masked_text_snippet": snippet,
                    "decision": p.decision.value,
                    "officer_comment": p.officer_comment,
                    "similarity_score": round(sim, 4),
                }
            )
        return results

    @classmethod
    def index_reviewed_document_as_precedent(
        cls,
        db: Session,
        document_id: str,
        title: str,
        document_type: Any,
        masked_text: str,
        decision: DocumentStatus,
        officer_comment: str,
    ) -> Optional[PrecedentSubmission]:
        """Index approved/rejected docs once (upsert by source_document_id). Skip needs_revision."""
        if decision == DocumentStatus.NEEDS_REVISION:
            return None

        vec = cls.generate_embedding(masked_text[:3000])
        existing = (
            db.query(PrecedentSubmission)
            .filter(PrecedentSubmission.source_document_id == document_id)
            .first()
        )
        if existing:
            existing.title = title
            existing.document_type = document_type
            existing.masked_text = masked_text
            existing.decision = decision
            existing.officer_comment = officer_comment
            existing.embedding_json = json.dumps(vec)
            db.commit()
            db.refresh(existing)
            return existing

        precedent = PrecedentSubmission(
            title=title,
            document_type=document_type,
            masked_text=masked_text,
            decision=decision,
            officer_comment=officer_comment,
            source_document_id=document_id,
            embedding_json=json.dumps(vec),
        )
        db.add(precedent)
        db.commit()
        db.refresh(precedent)
        return precedent
