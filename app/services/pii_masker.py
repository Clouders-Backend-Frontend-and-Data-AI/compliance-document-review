import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.pii_mapping import PIIMapping


class PIIMasker:
    """
    Deterministic server-side PII masker.
    Prefers data_engineering.masking when available; falls back to local patterns.
    Does not wipe existing mappings unless replace_mappings=True.
    """

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        re.IGNORECASE,
    )
    PHONE_PATTERN = re.compile(
        r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?|\b\d{3}[-.\s])\d{3}[-.\s]?\d{4}\b"
    )
    SSN_PATTERN = re.compile(
        r"\b(?:\d{3}-\d{2}-\d{4}|(?:SSN|TIN|Tax ID)[\s:#-]*\d{3}[-\s]?\d{2}[-\s]?\d{4})\b",
        re.IGNORECASE,
    )
    ACCOUNT_PATTERN = re.compile(
        r"\b(?:Account(?:\s+(?:Number|No\.?|ID))?|Acct(?:\s*#|\s*ID)?|Portfolio(?:\s*ID)?|"
        r"Folio|Policy|IRA|401\(?k\)?|Brokerage|ACCT)[\s#:]*([A-Z0-9\-]{5,20})\b",
        re.IGNORECASE,
    )
    ADDRESS_PATTERN = re.compile(
        r"\b\d{1,5}\s+[A-Za-z0-9.\s]{2,30}\s+"
        r"(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Road|Rd\.?|Drive|Dr\.?|"
        r"Lane|Ln\.?|Way|Court|Ct\.?|Suite|Ste\.?|Apt\.?|Unit)\b"
        r"(?:[,\s]+[A-Za-z\s]{2,20}[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?)?",
        re.IGNORECASE,
    )
    NAME_HEURISTIC_PATTERNS = [
        re.compile(
            r"(?:Client(?:\s+Name)?|Customer|Investor|Prepared for|Attention|Attn|"
            r"Account Holder|Beneficiary|Title)[: \t]+([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})"
        ),
        re.compile(
            r"(?:Dear|Hello|Hi)[ \t]+(?:Mr\.|Mrs\.|Ms\.|Dr\.)?[ \t]*"
            r"([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)?)"
        ),
        re.compile(r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)[ \t]+([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)?)"),
        re.compile(
            r"(?:Advisor|Representative|Prepared by)[: \t]+"
            r"([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})"
        ),
        # Title Case full names (aggressive; privacy > recall)
        re.compile(r"\b([A-Z][a-z]{1,20}(?:[ \t]+[A-Z][a-z]{1,20}){1,2})\b"),
    ]
    PERSONAL_AMOUNT_PATTERN = re.compile(
        r"(?:Balance|Net Worth|Portfolio Value|Contribution|Distribution|Assets|Income|"
        r"Salary|Investment)[: \t]*(\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?"
        r"(?:\s*(?:million|k|thousand|billion|M|B))?)",
        re.IGNORECASE,
    )
    BARE_AMOUNT_PATTERN = re.compile(
        r"\$\s*\d{1,3}(?:,\d{3})+(?:\.\d{2})?(?:\s*(?:million|k|thousand|billion|M|B))?",
        re.IGNORECASE,
    )

    NON_ACCOUNT_EXCLUSIONS = {
        "strategy", "management", "proposal", "overview", "portfolio", "performance",
        "advisors", "partners", "wealth", "review", "summary", "report", "growth", "sleeve",
    }
    NAME_EXCLUSIONS = {
        "the", "all", "investors", "clients", "compliance", "strategy", "management",
        "past", "performance", "market", "outlook", "united", "states", "form", "adv",
        "not", "fdic", "insured", "may", "lose", "value", "bank", "guaranteed",
    }

    @classmethod
    def mask_text(
        cls,
        text: str,
        document_id: Optional[str] = None,
        db: Optional[Session] = None,
        replace_mappings: bool = False,
    ) -> Tuple[str, List[Dict[str, str]]]:
        if not text:
            return "", []

        # Prefer data_engineering masker (shared privacy wall)
        try:
            from app.services.de_bridge import mask_text_de, persist_pii_mappings

            masked_text, mapping_dict, _counts = mask_text_de(text)
            mappings = [
                {
                    "placeholder": ph,
                    "original_value": orig,
                    "entity_type": cls._entity_type_from_placeholder(ph),
                }
                for ph, orig in mapping_dict.items()
            ]
            if document_id and db is not None:
                persist_pii_mappings(
                    db, document_id, mapping_dict, replace=replace_mappings
                )
            return masked_text, mappings
        except Exception:
            pass

        return cls._mask_local(text, document_id=document_id, db=db, replace_mappings=replace_mappings)

    @classmethod
    def _entity_type_from_placeholder(cls, placeholder: str) -> str:
        for label, etype in [
            ("CLIENT", "name"),
            ("EMAIL", "email"),
            ("PHONE", "phone"),
            ("ADDRESS", "address"),
            ("ACCOUNT", "account"),
            ("SSN", "ssn"),
            ("AMOUNT", "amount"),
        ]:
            if placeholder.startswith(f"[{label}_"):
                return etype
        return "unknown"

    @classmethod
    def _mask_local(
        cls,
        text: str,
        document_id: Optional[str] = None,
        db: Optional[Session] = None,
        replace_mappings: bool = False,
    ) -> Tuple[str, List[Dict[str, str]]]:
        masked_text = text
        mappings: List[Dict[str, str]] = []
        value_to_placeholder: Dict[str, str] = {}
        entity_counters: Dict[str, int] = {
            "CLIENT": 1,
            "EMAIL": 1,
            "PHONE": 1,
            "SSN": 1,
            "ACCOUNT": 1,
            "ADDRESS": 1,
            "AMOUNT": 1,
        }

        def get_or_create_placeholder(val: str, entity_type: str) -> str:
            clean_val = val.strip()
            if not clean_val:
                return ""
            if clean_val in value_to_placeholder:
                return value_to_placeholder[clean_val]
            idx = entity_counters[entity_type]
            entity_counters[entity_type] += 1
            placeholder = f"[{entity_type}_{idx}]"
            value_to_placeholder[clean_val] = placeholder
            mappings.append(
                {
                    "placeholder": placeholder,
                    "original_value": clean_val,
                    "entity_type": entity_type.lower(),
                }
            )
            return placeholder

        for match in cls.EMAIL_PATTERN.finditer(masked_text):
            get_or_create_placeholder(match.group(0), "EMAIL")
        for match in cls.SSN_PATTERN.finditer(masked_text):
            get_or_create_placeholder(match.group(0), "SSN")
        for match in cls.PHONE_PATTERN.finditer(masked_text):
            orig = match.group(0)
            if len(re.sub(r"\D", "", orig)) >= 10:
                get_or_create_placeholder(orig, "PHONE")
        for match in cls.ACCOUNT_PATTERN.finditer(masked_text):
            if match.group(1):
                orig = match.group(1).strip()
                if orig.lower() not in cls.NON_ACCOUNT_EXCLUSIONS and len(orig) >= 4:
                    get_or_create_placeholder(orig, "ACCOUNT")
        for match in cls.ADDRESS_PATTERN.finditer(masked_text):
            get_or_create_placeholder(match.group(0), "ADDRESS")
        for match in cls.PERSONAL_AMOUNT_PATTERN.finditer(masked_text):
            if match.group(1):
                get_or_create_placeholder(match.group(1).strip(), "AMOUNT")
        for match in cls.BARE_AMOUNT_PATTERN.finditer(masked_text):
            get_or_create_placeholder(match.group(0).strip(), "AMOUNT")
        for pattern in cls.NAME_HEURISTIC_PATTERNS:
            for match in pattern.finditer(masked_text):
                name_candidate = (match.group(1) if match.lastindex else match.group(0)).strip()
                tokens = name_candidate.lower().split()
                if (
                    len(name_candidate) > 2
                    and not any(t in cls.NAME_EXCLUSIONS for t in tokens)
                    and name_candidate.lower() not in cls.NAME_EXCLUSIONS
                ):
                    get_or_create_placeholder(name_candidate, "CLIENT")

        for orig, placeholder in sorted(
            value_to_placeholder.items(), key=lambda x: len(x[0]), reverse=True
        ):
            masked_text = masked_text.replace(orig, placeholder)

        if document_id and db is not None:
            if replace_mappings:
                db.query(PIIMapping).filter(PIIMapping.document_id == document_id).delete()
                db.flush()
            existing = {
                row.placeholder: row
                for row in db.query(PIIMapping)
                .filter(PIIMapping.document_id == document_id)
                .all()
            }
            for m in mappings:
                if m["placeholder"] in existing:
                    existing[m["placeholder"]].original_value = m["original_value"]
                    existing[m["placeholder"]].entity_type = m["entity_type"]
                else:
                    db.add(
                        PIIMapping(
                            document_id=document_id,
                            placeholder=m["placeholder"],
                            original_value=m["original_value"],
                            entity_type=m["entity_type"],
                        )
                    )
            db.commit()

        return masked_text, mappings

    @classmethod
    def unmask_text(
        cls,
        masked_text: str,
        mappings: Optional[List[Dict[str, str]]] = None,
        document_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> str:
        if not masked_text:
            return ""

        unmasked = masked_text
        if mappings is None and document_id and db is not None:
            db_mappings = (
                db.query(PIIMapping).filter(PIIMapping.document_id == document_id).all()
            )
            mappings = [
                {"placeholder": m.placeholder, "original_value": m.original_value}
                for m in db_mappings
            ]

        if mappings:
            for item in sorted(mappings, key=lambda x: len(x["placeholder"]), reverse=True):
                unmasked = unmasked.replace(item["placeholder"], item["original_value"])
        return unmasked
