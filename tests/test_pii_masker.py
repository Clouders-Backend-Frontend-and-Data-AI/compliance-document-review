from app.services.pii_masker import PIIMasker

def test_pii_masking_comprehensive():
    raw_document_text = """
    Apex Wealth Management - Private Portfolio Strategy
    Prepared for: Eleanor Vance
    Email: eleanor.vance@techcorp.io
    Phone: (555) 345-6789
    SSN: 123-45-6789
    Account Number: ACCT-998877
    Address: 123 Main Street, Suite 400, Chicago, IL 60601
    Portfolio Value: $2,500,000

    Dear Ms. Vance,
    We are pleased to manage your $2,500,000 portfolio. Please contact us at eleanor.vance@techcorp.io if you have questions.
    """

    masked_text, mappings = PIIMasker.mask_text(raw_document_text)

    # 1. Assert raw PII is NOT in masked text
    assert "eleanor.vance@techcorp.io" not in masked_text
    assert "(555) 345-6789" not in masked_text
    assert "123-45-6789" not in masked_text
    assert "ACCT-998877" not in masked_text
    assert "123 Main Street" not in masked_text
    assert "Eleanor Vance" not in masked_text
    assert "$2,500,000" not in masked_text

    # 2. Assert placeholders are present
    assert "[EMAIL_1]" in masked_text
    assert "[PHONE_1]" in masked_text
    assert "[SSN_1]" in masked_text
    assert "[ACCOUNT_1]" in masked_text
    assert "[ADDRESS_1]" in masked_text
    assert "[CLIENT_1]" in masked_text
    assert "[AMOUNT_1]" in masked_text

    # 3. Assert placeholder stability: repeated occurrences share same placeholder
    assert masked_text.count("[EMAIL_1]") == 2

    # 4. Assert unmasking reproduces original text
    unmasked = PIIMasker.unmask_text(masked_text, mappings)
    assert "eleanor.vance@techcorp.io" in unmasked
    assert "(555) 345-6789" in unmasked
    assert "123-45-6789" in unmasked
    assert "ACCT-998877" in unmasked
    assert "123 Main Street" in unmasked
    assert "Eleanor Vance" in unmasked
    assert "$2,500,000" in unmasked

def test_outbound_payload_privacy_guarantee(client, advisor_headers):
    import io
    doc_content = (
        "Confidential Proposal for Client: Jonathan Sterling\n"
        "Email: j.sterling@sterlingholdings.com\n"
        "Phone: 212-555-0199\n"
        "Account: FOLIO-445566\n"
        "Balance: $5,000,000\n"
        "Strategy details: investing in growth equities."
    )
    files = {"file": ("confidential.txt", io.BytesIO(doc_content.encode("utf-8")), "text/plain")}
    res = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "Jonathan Sterling Proposal", "document_type": "proposal_letter"},
        files=files
    )
    doc_id = res.json()["document"]["id"]

    # Inspect outbound payload
    res_payload = client.get(f"/api/v1/documents/{doc_id}/outbound-payload", headers=advisor_headers)
    assert res_payload.status_code == 200
    data = res_payload.json()
    masked_pl = data["masked_payload"]

    # Ensure zero original PII leaked in the outbound payload snapshot
    assert "Jonathan Sterling" not in masked_pl
    assert "j.sterling@sterlingholdings.com" not in masked_pl
    assert "212-555-0199" not in masked_pl
    assert "FOLIO-445566" not in masked_pl
    assert "$5,000,000" not in masked_pl
    assert "[CLIENT_1]" in masked_pl
    assert "[EMAIL_1]" in masked_pl
    assert data["pii_entities_masked_count"] >= 4
