import io
from fastapi.testclient import TestClient

def test_graceful_degradation_without_ai_key(
    client: TestClient,
    advisor_headers,
    officer_headers
):
    # Upload document with promissory language and missing disclosures
    doc_content = (
        "High-Growth Fund Pitch\n"
        "Prepared for: Robert Vance\n"
        "We offer a guaranteed return of 18% with zero risk of downside.\n"
        "Sign up today."
    )
    files = {"file": ("pitch.txt", io.BytesIO(doc_content.encode("utf-8")), "text/plain")}
    res_upload = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "High-Growth Fund Pitch", "document_type": "marketing_email"},
        files=files
    )
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["document"]["id"]

    # Fetch AI assist - Even with no Gemini key set, assist endpoint succeeds gracefully
    res_assist = client.get(f"/api/v1/documents/{doc_id}/assist", headers=officer_headers)
    assert res_assist.status_code == 200
    assist_data = res_assist.json()
    assert assist_data["document_id"] == doc_id
    assert len(assist_data["summary"]) > 0
    assert assist_data["status"] in ["completed", "degraded"]
    
    # Flags must contain passage excerpt, matched rule, and explanation
    flags = assist_data["flags"]
    assert len(flags) > 0
    assert any("guaranteed" in f["explanation"].lower() or "missing" in f["explanation"].lower() for f in flags)
    assert flags[0]["passage_excerpt"] is not None
    assert flags[0]["explanation"] is not None

    # Officer can submit review decision without any interruption
    res_decision = client.post(
        f"/api/v1/documents/{doc_id}/review",
        headers=officer_headers,
        json={
            "status": "rejected",
            "comment": "Rejected due to promissory return guarantee and missing risk disclosures."
        }
    )
    assert res_decision.status_code == 201
    assert res_decision.json()["status"] == "rejected"
