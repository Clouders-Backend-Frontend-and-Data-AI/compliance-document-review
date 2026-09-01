import re
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.pii_mapping import PIIMapping

class PIIMasker:
    """
    Deterministic regex & heuristic server-side PII masker.
    Replaces sensitive entities with stable, reversible placeholders
    before outbound LLM or embedding API calls.
    """

    # 1. Email Pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        re.IGNORECASE
    )

    # 2. Phone Numbers (US & International formats)
    PHONE_PATTERN = re.compile(
        r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?|\b\d{3}[-.\s])\d{3}[-.\s]?\d{4}\b'
    )

    # 3. SSN / Tax IDs (e.g. 123-45-6789, SSN: 123456789, TIN: 12-3456789)
    SSN_PATTERN = re.compile(
        r'\b(?:\d{3}-\d{2}-\d{4}|(?:SSN|TIN|Tax ID)[\s:#-]*\d{3}[-\s]?\d{2}[-\s]?\d{4})\b',
        re.IGNORECASE
    )

    # 4. Financial Account / Brokerage / IRA Numbers
    ACCOUNT_PATTERN = re.compile(
        r'\b(?:Account(?:\s+(?:Number|No\.?|ID))?|Acct(?:\s*#|\s*ID)?|Portfolio(?:\s*ID)?|Folio|Policy|IRA|401\(?k\)?|Brokerage)[\s#:]*([A-Z0-9\-]{5,20})\b',
        re.IGNORECASE
    )

    # 5. Street & Postal Addresses
    ADDRESS_PATTERN = re.compile(
        r'\b\d{1,5}\s+[A-Za-z0-9\.\s]{2,30}\s+(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Road|Rd\.?|Drive|Dr\.?|Lane|Ln\.?|Way|Court|Ct\.?|Suite|Ste\.?|Apt\.?|Unit)\b(?:[,\s]+[A-Za-z\s]{2,20}[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?)?',
        re.IGNORECASE
    )

    # 6. Specific Client / Person Names via contextual heuristics (Horizontal whitespace only)
    NAME_HEURISTIC_PATTERNS = [
        re.compile(r'(?:Client(?:\s+Name)?|Customer|Investor|Prepared for|Attention|Attn|Account Holder|Beneficiary)[: \t]+([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})'),
        re.compile(r'(?:Dear|Hello|Hi)[ \t]+(?:Mr\.|Mrs\.|Ms\.|Dr\.)?[ \t]*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)?)'),
        re.compile(r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)[ \t]+([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)?)'),
        re.compile(r'(?:Advisor|Representative|Prepared by)[: \t]+([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})')
    ]

    # 7. Personal monetary amounts (e.g. "Portfolio Value: $2,500,000", "Net Worth: $5M")
    PERSONAL_AMOUNT_PATTERN = re.compile(
        r'(?:Balance|Net Worth|Portfolio Value|Contribution|Distribution|Assets|Income|Salary|Investment)[: \t]*(\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|k|thousand|billion|M|B))?)',
        re.IGNORECASE
    )

    NON_ACCOUNT_EXCLUSIONS = {
        "strategy", "management", "proposal", "overview", "portfolio", "performance",
        "advisors", "partners", "wealth", "review", "summary", "report", "growth", "sleeve"
    }

    @classmethod
    def mask_text(
        cls,
        text: str,
        document_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Masks all detected PII in text with stable placeholders.
        Returns:
            - masked_text: Text safe for sending to LLM / embedding API.
            - mappings: List of dictionaries mapping placeholder -> original_value.
        """
        if not text:
            return "", []

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
            "AMOUNT": 1
        }

        def get_or_create_placeholder(val: str, entity_type: str) -> str:
            clean_val = val.strip()
            if not clean_val or clean_val in value_to_placeholder:
                return value_to_placeholder.get(clean_val, "")
            
            idx = entity_counters[entity_type]
            entity_counters[entity_type] += 1
            placeholder = f"[{entity_type}_{idx}]"
            value_to_placeholder[clean_val] = placeholder
            mappings.append({
                "placeholder": placeholder,
                "original_value": clean_val,
                "entity_type": entity_type.lower()
            })
            return placeholder

        # 1. Mask Emails
        for match in cls.EMAIL_PATTERN.finditer(masked_text):
            orig = match.group(0)
            get_or_create_placeholder(orig, "EMAIL")

        # 2. Mask SSNs
        for match in cls.SSN_PATTERN.finditer(masked_text):
            orig = match.group(0)
            get_or_create_placeholder(orig, "SSN")

        # 3. Mask Phones
        for match in cls.PHONE_PATTERN.finditer(masked_text):
            orig = match.group(0)
            digits = re.sub(r'\D', '', orig)
            if len(digits) >= 10:
                get_or_create_placeholder(orig, "PHONE")

        # 4. Mask Accounts
        for match in cls.ACCOUNT_PATTERN.finditer(masked_text):
            if match.group(1):
                orig = match.group(1).strip()
                if orig.lower() not in cls.NON_ACCOUNT_EXCLUSIONS and len(orig) >= 4:
                    get_or_create_placeholder(orig, "ACCOUNT")

        # 5. Mask Addresses
        for match in cls.ADDRESS_PATTERN.finditer(masked_text):
            orig = match.group(0)
            get_or_create_placeholder(orig, "ADDRESS")

        # 6. Mask Personal Amounts
        for match in cls.PERSONAL_AMOUNT_PATTERN.finditer(masked_text):
            if match.group(1):
                orig = match.group(1).strip()
                get_or_create_placeholder(orig, "AMOUNT")

        # 7. Mask Names via heuristics
        for pattern in cls.NAME_HEURISTIC_PATTERNS:
            for match in pattern.finditer(masked_text):
                if match.group(1):
                    name_candidate = match.group(1).strip()
                    if len(name_candidate) > 2 and name_candidate.lower() not in [
                        "the", "all", "investors", "clients", "compliance", "strategy", "management"
                    ]:
                        get_or_create_placeholder(name_candidate, "CLIENT")

        # Apply replacements (sort by longest original value first to avoid substring collision)
        for orig, placeholder in sorted(value_to_placeholder.items(), key=lambda x: len(x[0]), reverse=True):
            masked_text = masked_text.replace(orig, placeholder)

        # If document_id and db are provided, persist mappings
        if document_id and db is not None:
            db.query(PIIMapping).filter(PIIMapping.document_id == document_id).delete()
            for m in mappings:
                db_mapping = PIIMapping(
                    document_id=document_id,
                    placeholder=m["placeholder"],
                    original_value=m["original_value"],
                    entity_type=m["entity_type"]
                )
                db.add(db_mapping)
            db.commit()

        return masked_text, mappings

    @classmethod
    def unmask_text(
        cls,
        masked_text: str,
        mappings: Optional[List[Dict[str, str]]] = None,
        document_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> str:
        """
        Restores placeholders back to original values for compliance officer display.
        Uses either the passed mapping list or loads it securely from the DB.
        """
        if not masked_text:
            return ""

        unmasked = masked_text

        if mappings is None and document_id and db is not None:
            db_mappings = db.query(PIIMapping).filter(PIIMapping.document_id == document_id).all()
            mappings = [{"placeholder": m.placeholder, "original_value": m.original_value} for m in db_mappings]

        if mappings:
            for item in sorted(mappings, key=lambda x: len(x["placeholder"]), reverse=True):
                unmasked = unmasked.replace(item["placeholder"], item["original_value"])

        return unmasked
