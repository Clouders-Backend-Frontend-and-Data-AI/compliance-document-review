"""
Bridge between the FastAPI app and the data_engineering public API.

Public surface (from data_engineering/__init__.py / pipeline/__init__.py):
  - ingest_document
  - RuleRetriever
  - DisclosureRetriever
  - PrecedentRetriever
  - unmask_text

When DATABASE_URL is Postgres and USE_DATA_ENGINEERING=true, uses the full
pgvector pipeline. Otherwise uses DE extraction/masking/chunking components
with the app's SQLAlchemy models (SQLite-safe clean checkout).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


def data_engineering_pg_enabled() -> bool:
    url = (settings.DATABASE_URL or "").lower()
    return bool(settings.USE_DATA_ENGINEERING and url.startswith("postgresql"))


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Use DE extractors (PDF/DOCX/XLSX). Raises ValueError on empty/unsupported."""
    from data_engineering.extraction.router import extract_text

    result = extract_text(file_bytes, filename)
    text = (result.raw_text or "").strip()
    if not text:
        raise ValueError(f"Document '{filename}' yielded no extractable text.")
    return text


def mask_text_de(text: str) -> Tuple[str, Dict[str, str], Dict[str, int]]:
    """
    Run DE PII masker.
    Returns (masked_text, placeholder->original, entity_counts_by_label).
    """
    from data_engineering.masking.masker import PIIMasker

    result = PIIMasker().mask(text or "")
    counts = {getattr(k, "value", str(k)): v for k, v in (result.entity_counts or {}).items()}
    return result.masked_text, result.mapping, counts


def unmask_text_de(masked_text: str, mapping: Dict[str, str]) -> str:
    from data_engineering.masking.unmasker import unmask_text

    return unmask_text(masked_text, mapping)


def chunk_masked_text(masked_text: str) -> List[str]:
    from data_engineering.chunking.chunker import TextChunker

    return [c.text for c in TextChunker().chunk(masked_text)]


def try_ingest_document(document_id: str, file_bytes: bytes, filename: str) -> Optional[dict]:
    """Full DE ingest (extract→mask→chunk→embed→store) when pgvector is enabled."""
    if not data_engineering_pg_enabled():
        return None
    try:
        from data_engineering import ingest_document

        return ingest_document(document_id, file_bytes, filename)
    except Exception as exc:
        logger.exception("data_engineering.ingest_document failed: %s", exc)
        raise


def retrieve_rules_via_de(document_id: str) -> Optional[List[Dict[str, Any]]]:
    if not data_engineering_pg_enabled():
        return None
    from data_engineering import RuleRetriever

    return RuleRetriever().retrieve_for_document(document_id)


def retrieve_missing_disclosures_via_de(document_id: str) -> Optional[List[Dict[str, Any]]]:
    if not data_engineering_pg_enabled():
        return None
    from data_engineering import DisclosureRetriever

    results = DisclosureRetriever().check_document(document_id)
    missing = []
    for r in results:
        if getattr(r, "is_present", True):
            continue
        missing.append(
            {
                "rule_id": getattr(r, "disclosure_id", None),
                "rule_code": getattr(r, "disclosure_code", None),
                "title": getattr(r, "title", None),
                "standard_disclosure": getattr(r, "title", None),
                "max_similarity_found": round(float(getattr(r, "best_similarity", 0.0)), 4),
                "threshold": None,
                "reason": f"Required disclosure '{getattr(r, 'title', '')}' not found by vector absence check.",
            }
        )
    return missing


def retrieve_precedents_via_de(document_id: str) -> Optional[List[Dict[str, Any]]]:
    if not data_engineering_pg_enabled():
        return None
    from data_engineering import PrecedentRetriever

    results = PrecedentRetriever().retrieve(document_id)
    return [
        {
            "id": getattr(r, "document_id", None),
            "title": "",
            "document_type": "other",
            "masked_text_snippet": "",
            "decision": getattr(r, "decision", None),
            "officer_comment": getattr(r, "officer_comment", None),
            "similarity_score": round(float(getattr(r, "similarity", 0.0)), 4),
        }
        for r in results
    ]


def persist_pii_mappings(
    db: Session,
    document_id: str,
    mapping: Dict[str, str],
    *,
    replace: bool = False,
) -> None:
    """
    Persist placeholder mappings without wiping unrelated history by default.
    When replace=True (first analysis / force regenerate), clear then insert.
    When replace=False, upsert by placeholder.
    """
    from app.models.pii_mapping import PIIMapping

    if replace:
        db.query(PIIMapping).filter(PIIMapping.document_id == document_id).delete()
        db.flush()

    existing = {
        row.placeholder: row
        for row in db.query(PIIMapping).filter(PIIMapping.document_id == document_id).all()
    }

    label_map = {
        "CLIENT": "name",
        "EMAIL": "email",
        "PHONE": "phone",
        "ADDRESS": "address",
        "ACCOUNT": "account",
        "SSN": "ssn",
        "AMOUNT": "amount",
    }

    for placeholder, original in mapping.items():
        entity_type = "unknown"
        for label, etype in label_map.items():
            if placeholder.startswith(f"[{label}_"):
                entity_type = etype
                break
        if placeholder in existing:
            existing[placeholder].original_value = original
            existing[placeholder].entity_type = entity_type
        else:
            db.add(
                PIIMapping(
                    document_id=document_id,
                    placeholder=placeholder,
                    original_value=original,
                    entity_type=entity_type,
                )
            )
    db.commit()
