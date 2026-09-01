import io
import os
from fastapi.testclient import TestClient
from app.services.extractor import DocumentExtractor

def test_multiformat_extraction_service():
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_test_files"))
    docx_path = os.path.join(sample_dir, "sample_compliant_proposal.docx")
    xlsx_path = os.path.join(sample_dir, "sample_performance_sheet.xlsx")
    pdf_path = os.path.join(sample_dir, "sample_noncompliant_promo.pdf")

    if os.path.exists(docx_path):
        docx_txt = DocumentExtractor.extract_text_from_file(docx_path)
        assert "Robert Henderson" in docx_txt or "Executive Summary" in docx_txt

    if os.path.exists(xlsx_path):
        xlsx_txt = DocumentExtractor.extract_text_from_file(xlsx_path)
        assert "Performance" in xlsx_txt or "Core Fixed Income" in xlsx_txt

    if os.path.exists(pdf_path):
        pdf_txt = DocumentExtractor.extract_text_from_file(pdf_path)
        assert "Crypto" in pdf_txt or "Alpha" in pdf_txt or "Guaranteed" in pdf_txt

def test_file_download_endpoint(client: TestClient, advisor_headers):
    file_bytes = b"Document download verification test content."
    files = {"file": ("download_test.txt", io.BytesIO(file_bytes), "text/plain")}
    res_upload = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "Download Test Doc", "document_type": "brochure"},
        files=files
    )
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["document"]["id"]

    # Download file
    res_dl = client.get(f"/api/v1/documents/{doc_id}/download", headers=advisor_headers)
    assert res_dl.status_code == 200
    assert res_dl.content == file_bytes

def test_corpus_endpoints(client: TestClient, officer_headers):
    # Rules endpoint
    res_rules = client.get("/api/v1/corpus/rules", headers=officer_headers)
    assert res_rules.status_code == 200
    rules = res_rules.json()
    assert len(rules) >= 10

    # Filter rules by category
    res_filtered = client.get("/api/v1/corpus/rules?category=required_disclosure", headers=officer_headers)
    assert res_filtered.status_code == 200
    for r in res_filtered.json():
        assert r["category"] == "required_disclosure"

    # Precedents endpoint
    res_prec = client.get("/api/v1/corpus/precedents?limit=10", headers=officer_headers)
    assert res_prec.status_code == 200
    assert len(res_prec.json()) <= 10
