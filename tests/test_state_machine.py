import io
from fastapi.testclient import TestClient

def test_full_document_lifecycle_and_revision_threading(
    client: TestClient,
    advisor_headers,
    officer_headers
):
    # Step 1: Advisor uploads initial document (v1)
    file_bytes_v1 = b"Initial draft of Q4 Marketing Brochure. Missing risk disclaimers."
    files_v1 = {"file": ("brochure_v1.txt", io.BytesIO(file_bytes_v1), "text/plain")}
    res_upload_v1 = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "Q4 Market Strategy Brochure", "document_type": "brochure"},
        files=files_v1
    )
    assert res_upload_v1.status_code == 201
    doc_v1 = res_upload_v1.json()["document"]
    assert doc_v1["status"] == "pending_review"
    assert doc_v1["version_number"] == 1
    thread_id = doc_v1["thread_id"]
    doc_v1_id = doc_v1["id"]

    # Step 2: Officer reviews v1 and marks 'needs_revision'
    res_review_v1 = client.post(
        f"/api/v1/documents/{doc_v1_id}/review",
        headers=officer_headers,
        json={
            "status": "needs_revision",
            "comment": "Please add the standard SEC risk of loss disclosure in the footer."
        }
    )
    assert res_review_v1.status_code == 201
    assert res_review_v1.json()["status"] == "needs_revision"

    # Verify status changed on doc
    res_get_v1 = client.get(f"/api/v1/documents/{doc_v1_id}", headers=advisor_headers)
    assert res_get_v1.json()["status"] == "needs_revision"

    # Step 3: Advisor submits revised version (v2)
    file_bytes_v2 = b"Revised Q4 Marketing Brochure. Past performance is not indicative of future results."
    files_v2 = {"file": ("brochure_v2.txt", io.BytesIO(file_bytes_v2), "text/plain")}
    res_revise = client.post(
        f"/api/v1/documents/{doc_v1_id}/revise",
        headers=advisor_headers,
        data={"title": "Q4 Market Strategy Brochure (Revised)", "document_type": "brochure"},
        files=files_v2
    )
    assert res_revise.status_code == 201
    doc_v2 = res_revise.json()["document"]
    assert doc_v2["status"] == "pending_review"
    assert doc_v2["version_number"] == 2
    assert doc_v2["thread_id"] == thread_id
    assert doc_v2["parent_document_id"] == doc_v1_id
    doc_v2_id = doc_v2["id"]

    # Step 4: Advisor cannot revise a document that is in 'pending_review'
    files_invalid = {"file": ("brochure_v3.txt", io.BytesIO(b"v3"), "text/plain")}
    res_invalid_rev = client.post(
        f"/api/v1/documents/{doc_v2_id}/revise",
        headers=advisor_headers,
        data={"title": "Invalid Rev", "document_type": "brochure"},
        files=files_invalid
    )
    assert res_invalid_rev.status_code == 400

    # Step 5: Officer reviews v2 and marks 'approved'
    res_review_v2 = client.post(
        f"/api/v1/documents/{doc_v2_id}/review",
        headers=officer_headers,
        json={
            "status": "approved",
            "comment": "Approved. Required disclaimers are now properly included."
        }
    )
    assert res_review_v2.status_code == 201
    assert res_review_v2.json()["status"] == "approved"

    # Step 6: Verify full thread history
    res_thread = client.get(f"/api/v1/documents/{doc_v2_id}/thread", headers=officer_headers)
    assert res_thread.status_code == 200
    thread_data = res_thread.json()
    assert thread_data["thread_id"] == thread_id
    assert thread_data["total_versions"] == 2
    assert thread_data["documents"][0]["version_number"] == 1
    assert thread_data["documents"][0]["status"] == "needs_revision"
    assert thread_data["documents"][1]["version_number"] == 2
    assert thread_data["documents"][1]["status"] == "approved"
