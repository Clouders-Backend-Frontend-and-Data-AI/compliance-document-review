import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.ai_analysis import AIAnalysis, ComplianceFlag
from app.models.base import FlagSeverity, DocumentStatus
from app.services.pii_masker import PIIMasker
from app.services.vector_engine import VectorEngine

logger = logging.getLogger(__name__)

class AIAssistService:
    """
    AI Compliance Assist generation service.
    Coordinates PII masking -> Vector Retrieval -> LLM Generation -> Unmasking.
    Caches analysis per document and handles graceful degradation.
    """

    @classmethod
    def generate_or_get_analysis(
        cls,
        db: Session,
        document: Document,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves cached analysis or performs new analysis.
        Guarantees that document loading NEVER fails even if AI is unavailable.
        """
        existing_analysis = db.query(AIAnalysis).filter(AIAnalysis.document_id == document.id).first()
        if existing_analysis and not force_regenerate:
            return cls._format_analysis_response(db, document, existing_analysis)

        # 1. Server-side PII Masking (Mask both title and extracted text)
        raw_text = document.extracted_text or "No text could be extracted from this document."
        full_raw = f"Title: {document.title}\n\n{raw_text}"
        masked_full, pii_mappings = PIIMasker.mask_text(
            full_raw,
            document_id=document.id,
            db=db,
            replace_mappings=True,
        )

        # Split masked title and masked text
        masked_lines = masked_full.split("\n\n", 1)
        masked_title = masked_lines[0].replace("Title: ", "") if masked_lines else document.title
        masked_text = masked_lines[1] if len(masked_lines) > 1 else masked_full

        # 2. Vector Retrieval: prefer data_engineering pgvector when enabled
        from app.services.de_bridge import (
            retrieve_missing_disclosures_via_de,
            retrieve_precedents_via_de,
            retrieve_rules_via_de,
        )

        chunks = VectorEngine.chunk_text(masked_text)
        relevant_rules = retrieve_rules_via_de(document.id)
        if relevant_rules is None:
            relevant_rules = VectorEngine.retrieve_relevant_rules(
                db, chunks, top_k=settings.RULE_RETRIEVAL_TOP_K
            )

        missing_disclosures = retrieve_missing_disclosures_via_de(document.id)
        if missing_disclosures is None:
            missing_disclosures = VectorEngine.detect_missing_disclosures(
                db, chunks, document_type=document.document_type
            )

        precedents = retrieve_precedents_via_de(document.id)
        if precedents is None:
            precedents = VectorEngine.search_precedents(
                db, masked_text, top_k=settings.PRECEDENT_TOP_K
            )

        # 3. Snapshot the exact outbound payload sent to AI (for privacy verification)
        outbound_payload_snapshot = json.dumps({
            "document_title": masked_title,
            "document_type": document.document_type.value,
            "masked_text": masked_text,
            "retrieved_rules": relevant_rules,
            "detected_missing_disclosures": missing_disclosures
        }, indent=2)

        # 4. Generate Analysis via LLM API or Graceful Rule-Based Degradation Fallback
        summary, flags_data, analysis_status, model_name = cls._run_llm_or_fallback(
            masked_text=masked_text,
            doc_title=masked_title,
            doc_type=document.document_type.value,
            rules=relevant_rules,
            missing_disclosures=missing_disclosures
        )

        # 5. Unmask placeholders in summary and flags for officer display
        unmasked_summary = PIIMasker.unmask_text(summary, pii_mappings)
        for flag in flags_data:
            flag["passage_excerpt"] = PIIMasker.unmask_text(flag.get("passage_excerpt", ""), pii_mappings)
            flag["explanation"] = PIIMasker.unmask_text(flag.get("explanation", ""), pii_mappings)
            if flag.get("suggested_fix"):
                flag["suggested_fix"] = PIIMasker.unmask_text(flag["suggested_fix"], pii_mappings)

        # 6. Save or Update AIAnalysis in Database
        if existing_analysis:
            existing_analysis.summary = unmasked_summary
            existing_analysis.outbound_payload_masked = outbound_payload_snapshot
            existing_analysis.status = analysis_status
            existing_analysis.model_used = model_name
            db.query(ComplianceFlag).filter(ComplianceFlag.analysis_id == existing_analysis.id).delete()
            analysis_record = existing_analysis
        else:
            analysis_record = AIAnalysis(
                document_id=document.id,
                summary=unmasked_summary,
                outbound_payload_masked=outbound_payload_snapshot,
                status=analysis_status,
                model_used=model_name
            )
            db.add(analysis_record)
            db.flush()

        # Add compliance flags
        for f_item in flags_data:
            sev_str = f_item.get("severity", "medium").lower()
            try:
                sev = FlagSeverity(sev_str)
            except ValueError:
                sev = FlagSeverity.MEDIUM

            flag_obj = ComplianceFlag(
                analysis_id=analysis_record.id,
                passage_excerpt=f_item.get("passage_excerpt", "General Document"),
                matched_rule_id=f_item.get("matched_rule_id"),
                matched_rule_title=f_item.get("matched_rule_title"),
                matched_rule_text=f_item.get("matched_rule_text"),
                explanation=f_item.get("explanation", "Potential compliance concern detected."),
                severity=sev,
                suggested_fix=f_item.get("suggested_fix")
            )
            db.add(flag_obj)

        db.commit()
        db.refresh(analysis_record)

        return cls._format_analysis_response(db, document, analysis_record, precedents)

    @classmethod
    def _run_llm_or_fallback(
        cls,
        masked_text: str,
        doc_title: str,
        doc_type: str,
        rules: List[Dict[str, Any]],
        missing_disclosures: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]], str, str]:
        """
        Attempts to call Google Gemini API.
        If unavailable or no API key, executes high-quality heuristic & vector-backed rule verification.
        """
        if settings.GEMINI_API_KEY:
            try:
                summary, flags = cls._call_gemini_api(
                    masked_text, doc_title, doc_type, rules, missing_disclosures
                )
                return summary, flags, "completed", f"gemini-{settings.GEMINI_MODEL}"
            except Exception as e:
                logger.error(f"Gemini API execution error: {e}. Executing graceful fallback engine.")

        summary, flags = cls._generate_fallback_analysis(
            masked_text, doc_title, doc_type, rules, missing_disclosures
        )
        return summary, flags, "degraded", "local-rule-engine-fallback"

    @classmethod
    def _call_gemini_api(
        cls,
        masked_text: str,
        doc_title: str,
        doc_type: str,
        rules: List[Dict[str, Any]],
        missing_disclosures: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Calls Gemini API with strict structured compliance review prompt"""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )
        headers = {
            "x-goog-api-key": settings.GEMINI_API_KEY or "",
            "Content-Type": "application/json",
        }

        prompt = f"""You are a professional Compliance Assist AI for financial marketing materials.
Review the following masked document text against the retrieved compliance rules and missing disclosures.

DOCUMENT TITLE: {doc_title}
DOCUMENT TYPE: {doc_type}

MASKED DOCUMENT CONTENT:
\"\"\"
{masked_text[:4000]}
\"\"\"

RETRIEVED COMPLIANCE RULES:
{json.dumps(rules, indent=2)}

MISSING DISCLOSURES DETECTED BY VECTOR ABSENCE:
{json.dumps(missing_disclosures, indent=2)}

INSTRUCTIONS:
1. Provide a concise summary (2-3 sentences) explaining what the document is and its target audience.
2. Identify compliance issues:
   - For any missing disclosures, create a flag with severity 'high' or 'critical'.
   - Check for promissory/guaranteed return language (e.g. 'guaranteed', 'risk-free', '100% safe', 'will make you rich').
   - Check for unapproved or out-of-date performance claims without time periods or benchmarks.
   - For every flag, you MUST include:
     * passage_excerpt: the exact sentence or passage from the document (or 'Entire Document' if missing disclosure).
     * matched_rule_id: rule code / id.
     * matched_rule_title: title of the rule.
     * explanation: a clear 1-line reason explaining the conflict.
     * severity: critical, high, medium, or low.
     * suggested_fix: concrete suggestion to make the text compliant.
3. NEVER make a final review decision (do not state approved/rejected).

Respond ONLY with valid JSON matching this exact structure:
{{
  "summary": "Document summary string...",
  "flags": [
    {{
      "passage_excerpt": "...",
      "matched_rule_id": "...",
      "matched_rule_title": "...",
      "explanation": "...",
      "severity": "critical|high|medium|low",
      "suggested_fix": "..."
    }}
  ]
}}
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        with httpx.Client(timeout=float(settings.AI_TIMEOUT_SECONDS)) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f"Gemini API responded with status {response.status_code}: {response.text}")
            
            res_data = response.json()
            raw_text_out = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if raw_text_out.startswith("```json"):
                raw_text_out = raw_text_out[7:]
            if raw_text_out.endswith("```"):
                raw_text_out = raw_text_out[:-3]
            
            parsed = json.loads(raw_text_out.strip())
            return parsed.get("summary", ""), parsed.get("flags", [])

    @classmethod
    def _generate_fallback_analysis(
        cls,
        masked_text: str,
        doc_title: str,
        doc_type: str,
        rules: List[Dict[str, Any]],
        missing_disclosures: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Deterministic, robust fallback compliance analyzer.
        Evaluates heuristic patterns and vector absence matches.
        """
        word_count = len(masked_text.split())
        summary = (
            f"This is a {doc_type.replace('_', ' ')} titled '{doc_title}' containing approximately {word_count} words. "
            f"The content presents financial concepts and advisory communications intended for clients/investors."
        )

        flags: List[Dict[str, Any]] = []

        # 1. Add missing disclosure flags from vector absence detection
        for md in missing_disclosures:
            flags.append({
                "passage_excerpt": "Document Footers / Disclosures Section",
                "matched_rule_id": md["rule_code"],
                "matched_rule_title": md["title"],
                "matched_rule_text": md["standard_disclosure"],
                "explanation": f"Missing mandatory regulatory disclosure: '{md['title']}'. No matching disclosure was detected in vector search.",
                "severity": "high",
                "suggested_fix": f"Add the approved disclaimer text: \"{md['standard_disclosure']}\""
            })

        # 2. Check for prohibited promissory / guaranteed return claims
        prohibited_terms = [
            ("guaranteed return", "Guaranteed return claims are strictly prohibited under SEC Rule 206(4)-1 and FINRA Rule 2210.", "critical"),
            ("risk-free", "No investment can be characterized as 'risk-free' or without potential loss.", "critical"),
            ("100% safe", "Absolute safety claims mislead investors regarding market risk.", "high"),
            ("can't lose", "Claims implying zero downside violate fair balance standards.", "critical"),
            ("highest returns in the market", "Superlative performance claims require verifiable independent documentation.", "medium"),
            ("double your money", "Exaggerated return projections violate promotional communication rules.", "critical")
        ]

        text_lower = masked_text.lower()
        for term, explanation, severity in prohibited_terms:
            if term in text_lower:
                idx = text_lower.find(term)
                start = max(0, masked_text.rfind(".", 0, idx) + 1)
                end = masked_text.find(".", idx)
                if end == -1:
                    end = len(masked_text)
                passage = masked_text[start:end].strip()

                flags.append({
                    "passage_excerpt": passage or term,
                    "matched_rule_id": "SEC-PROH-01",
                    "matched_rule_title": "Prohibition of Misleading and Promissory Statements",
                    "matched_rule_text": "Advertisements may not include untrue statements of material fact or promissory return guarantees.",
                    "explanation": explanation,
                    "severity": severity,
                    "suggested_fix": "Remove or rephrase promissory language to emphasize market risk and potential fluctuation."
                })

        # 3. Check for performance presentation without required time horizon
        if any(w in text_lower for w in ["annual return", "generated", "yield", "past performance"]):
            if not any(d in text_lower for d in ["1-year", "5-year", "10-year", "net of fees", "gross"]):
                flags.append({
                    "passage_excerpt": "Performance presentation section",
                    "matched_rule_id": "PERF-STD-02",
                    "matched_rule_title": "Performance Presentation Standards",
                    "matched_rule_text": "Performance claims must include standard 1, 5, and 10-year periods and reflect net of fees.",
                    "explanation": "Performance figures mentioned without standardized multi-period disclosure (1/5/10 yr) or net-of-fees clarification.",
                    "severity": "medium",
                    "suggested_fix": "Provide 1-year, 5-year, and 10-year standardized returns net of advisory fees."
                })

        return summary, flags

    @classmethod
    def _format_analysis_response(
        cls,
        db: Session,
        document: Document,
        analysis: AIAnalysis,
        precedents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Formats the unified AI assist response including precedent matches"""
        if precedents is None:
            # Remask in-memory only — do not rewrite persisted PII mappings
            raw_text = document.extracted_text or ""
            full_raw = f"Title: {document.title}\n\n{raw_text}"
            masked_full, _ = PIIMasker.mask_text(full_raw)
            masked_lines = masked_full.split("\n\n", 1)
            masked_text = masked_lines[1] if len(masked_lines) > 1 else masked_full
            precedents = VectorEngine.search_precedents(
                db, masked_text, top_k=settings.PRECEDENT_TOP_K
            )

        flags_out = []
        for f in analysis.flags:
            flags_out.append({
                "id": f.id,
                "analysis_id": f.analysis_id,
                "passage_excerpt": f.passage_excerpt,
                "matched_rule_id": f.matched_rule_id,
                "matched_rule_title": f.matched_rule_title,
                "matched_rule_text": f.matched_rule_text,
                "explanation": f.explanation,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "suggested_fix": f.suggested_fix
            })

        return {
            "id": analysis.id,
            "document_id": analysis.document_id,
            "summary": analysis.summary,
            "status": analysis.status,
            "model_used": analysis.model_used,
            "generated_at": analysis.generated_at,
            "flags": flags_out,
            "precedent_matches": precedents or []
        }
