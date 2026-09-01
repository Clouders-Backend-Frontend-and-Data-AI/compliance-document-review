from app.services.vector_engine import VectorEngine
from app.models.vector_corpus import ComplianceRule, PrecedentSubmission
from app.models.base import RuleCategory, DocumentStatus, DocumentType

def test_rule_lookup_retrieval(db):
    chunks = [
        "Our strategy delivers exceptional returns and outperforms the general market index.",
        "Please note this does not constitute tax, legal, or accounting advice."
    ]
    rules = VectorEngine.retrieve_relevant_rules(db, chunks, top_k=3)
    assert len(rules) > 0
    assert "rule_code" in rules[0]
    assert "title" in rules[0]
    assert "similarity_score" in rules[0]

def test_disclosure_detection_by_absence(db):
    # Text with NO disclosures at all
    doc_without_disclosures = [
        "This is an aggressive tech stock picking strategy.",
        "We invest in semiconductors, artificial intelligence, and cloud software."
    ]
    missing = VectorEngine.detect_missing_disclosures(db, doc_without_disclosures, threshold=0.50)
    # Should detect missing disclosures
    assert len(missing) > 0
    missing_rule_codes = [m["rule_code"] for m in missing]
    assert any("SEC-MKT-01" in code or "TAX-DISC" in code or "BANK" in code for code in missing_rule_codes)

    # Text WITH risk disclosure
    doc_with_disclosure = [
        "Past performance is not indicative of future results. Investing in securities involves risk of loss that clients should be prepared to bear."
    ]
    # For SEC-MKT-01, since exact/near standard text is present, its max similarity should be high
    missing_with_disc = VectorEngine.detect_missing_disclosures(db, doc_with_disclosure, threshold=0.50)
    # The present disclosure should NOT be reported as missing
    missing_titles = [m["title"] for m in missing_with_disc]
    assert "General Risk of Loss & Past Performance Disclaimer" not in missing_titles

def test_precedent_search(db):
    masked_doc = "Dear [CLIENT_1], here is our market overview and portfolio report for retirement planning."
    precedents = VectorEngine.search_precedents(db, masked_doc, top_k=3)
    assert len(precedents) <= 3
    if precedents:
        assert "title" in precedents[0]
        assert "decision" in precedents[0]
        assert "officer_comment" in precedents[0]
        assert "similarity_score" in precedents[0]
