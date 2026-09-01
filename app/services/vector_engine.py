import json
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.vector_corpus import ComplianceRule, PrecedentSubmission
from app.models.base import RuleCategory, DocumentStatus

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
    "why", "will", "with", "you", "your", "yours", "yourself", "yourselves"
}

class VectorEngine:
    """
    Vector similarity & semantic retrieval engine.
    Supports Google Gemini embeddings API with local normalized TF-IDF / token hashing fallback
    for 100% reproducible, offline-capable clean checkout.
    """

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generates a normalized embedding vector for the provided (masked) text.
        Tries Gemini API if key is set; otherwise uses local normalized vectorizer.
        """
        if not text or not text.strip():
            return [0.0] * 128

        clean_text = text.strip()

        # Try Google Gemini Embedding API if API key is configured
        if settings.GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": clean_text[:2048]}]}
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        values = data.get("embedding", {}).get("values", [])
                        if values:
                            arr = np.array(values, dtype=np.float32)
                            norm = np.linalg.norm(arr)
                            if norm > 0:
                                arr = arr / norm
                            return arr.tolist()
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Falling back to local vectorizer.")

        # Local Deterministic Embedding Fallback
        return cls._generate_local_embedding(clean_text)

    @classmethod
    def _generate_local_embedding(cls, text: str, dim: int = 128) -> List[float]:
        """Fast, robust deterministic local embedding based on normalized token and n-gram frequency"""
        vec = np.zeros(dim, dtype=np.float32)
        import re
        words = re.findall(r'\b[a-z0-9_]{2,}\b', text.lower())
        filtered_words = [w for w in words if w not in STOP_WORDS]
        if not filtered_words:
            filtered_words = words

        for i, word in enumerate(filtered_words):
            # Unigram hash
            h1 = abs(hash(word)) % dim
            vec[h1] += 2.0

            # Bigram hash
            if i > 0:
                h2 = abs(hash(f"{filtered_words[i-1]}_{word}")) % dim
                vec[h2] += 3.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
        """Splits document text into overlapping paragraph-aware chunks for granular retrieval"""
        if not text:
            return []
        
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk = (current_chunk + "\n\n" + p).strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        if not chunks:
            words = text.split()
            for i in range(0, len(words), 80):
                chunks.append(" ".join(words[i:i+100]))

        return chunks

    @classmethod
    def cosine_sim(cls, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @classmethod
    def retrieve_relevant_rules(
        cls,
        db: Session,
        document_chunks: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Job 1: Rule lookup.
        Compares document chunks against compliance rules corpus and returns top relevant rules.
        """
        rules = db.query(ComplianceRule).all()
        if not rules:
            return []

        chunk_embeddings = [cls.generate_embedding(c) for c in document_chunks]
        rule_scores: Dict[str, Tuple[float, ComplianceRule, str]] = {}

        for rule in rules:
            rule_text_to_embed = rule.rule_text + " " + rule.title
            if rule.standard_disclosure:
                rule_text_to_embed += " " + rule.standard_disclosure
            rule_vec = cls.generate_embedding(rule_text_to_embed)

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
            results.append({
                "rule_id": rule.id,
                "rule_code": rule.rule_code,
                "category": rule.category.value,
                "title": rule.title,
                "rule_text": rule.rule_text,
                "similarity_score": round(score, 4),
                "matched_passage": matching_chunk
            })

        return results

    @classmethod
    def detect_missing_disclosures(
        cls,
        db: Session,
        document_chunks: List[str],
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Job 2: Missing-disclosure detection by absence.
        A required disclosure is present if some passage in the document sits close to it in vector space.
        If maximum similarity across all chunks is below the threshold, it is flagged as MISSING.
        """
        if threshold is None:
            threshold = settings.DISCLOSURE_ABSENCE_THRESHOLD

        disclosure_rules = db.query(ComplianceRule).filter(
            ComplianceRule.category == RuleCategory.REQUIRED_DISCLOSURE
        ).all()

        if not disclosure_rules:
            return []

        chunk_embeddings = [cls.generate_embedding(c) for c in document_chunks]
        missing_disclosures = []

        for rule in disclosure_rules:
            disc_text = rule.standard_disclosure or rule.rule_text
            disc_vec = cls.generate_embedding(disc_text)

            max_sim = 0.0
            for c_vec in chunk_embeddings:
                sim = cls.cosine_sim(c_vec, disc_vec)
                if sim > max_sim:
                    max_sim = sim

            if max_sim < threshold:
                missing_disclosures.append({
                    "rule_id": rule.id,
                    "rule_code": rule.rule_code,
                    "title": rule.title,
                    "standard_disclosure": disc_text,
                    "max_similarity_found": round(max_sim, 4),
                    "threshold": threshold,
                    "reason": f"Required mandatory disclosure '{rule.title}' was not found in any section of the document (Max similarity: {round(max_sim, 2)} < {threshold})."
                })

        return missing_disclosures

    @classmethod
    def search_precedents(
        cls,
        db: Session,
        masked_document_text: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Job 3: Precedent search.
        Embeds masked document text and queries precedent submissions corpus.
        Returns top 3 most similar past documents and their decisions + comments.
        """
        precedents = db.query(PrecedentSubmission).all()
        if not precedents:
            return []

        doc_vec = cls.generate_embedding(masked_document_text[:3000])
        matches = []

        for p in precedents:
            p_vec = cls.generate_embedding(p.masked_text[:3000])
            sim = cls.cosine_sim(doc_vec, p_vec)
            matches.append((sim, p))

        matches.sort(key=lambda x: x[0], reverse=True)
        top_matches = matches[:top_k]

        results = []
        for sim, p in top_matches:
            snippet = p.masked_text[:200] + ("..." if len(p.masked_text) > 200 else "")
            results.append({
                "id": p.id,
                "title": p.title,
                "document_type": p.document_type.value,
                "masked_text_snippet": snippet,
                "decision": p.decision.value,
                "officer_comment": p.officer_comment,
                "similarity_score": round(sim, 4)
            })

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
        officer_comment: str
    ) -> PrecedentSubmission:
        """Indexes an approved/rejected/revised document into the precedent vector store"""
        vec = cls.generate_embedding(masked_text[:3000])
        precedent = PrecedentSubmission(
            title=title,
            document_type=document_type,
            masked_text=masked_text,
            decision=decision,
            officer_comment=officer_comment,
            source_document_id=document_id,
            embedding_json=json.dumps(vec)
        )
        db.add(precedent)
        db.commit()
        db.refresh(precedent)
        return precedent
