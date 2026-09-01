import io
from fastapi.testclient import TestClient

def test_audit_trail_and_in_app_notifications(
    client: TestClient,
    advisor_headers,
    officer_headers
):
    # 1. Advisor uploads document
    files = {"file": ("audit_test.txt", io.BytesIO(b"Audit test content"), "text/plain")}
    res_upload = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "Audit Test Document", "document_type": "social_post"},
        files=files
    )
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["document"]["id"]

    # 2. Officer views document
    res_view = client.get(f"/api/v1/documents/{doc_id}", headers=officer_headers)
    assert res_view.status_code == 200

    # 3. Officer records decision
    res_review = client.post(
        f"/api/v1/documents/{doc_id}/review",
        headers=officer_headers,
        json={"status": "approved", "comment": "Audit trail review passed"}
    )
    assert res_review.status_code == 201

    # 4. Query audit trail
    res_audit = client.get(f"/api/v1/documents/{doc_id}/audit", headers=officer_headers)
    assert res_audit.status_code == 200
    events = res_audit.json()
    actions = [e["action"] for e in events]
    assert "submitted" in actions
    assert "viewed" in actions
    assert "decided" in actions

    # 5. Check in-app notification for the advisor
    res_notif = client.get("/api/v1/notifications", headers=advisor_headers)
    assert res_notif.status_code == 200
    notif_data = res_notif.json()
    assert notif_data["unread_count"] >= 1
    assert len(notif_data["notifications"]) >= 1
    first_notif = notif_data["notifications"][0]
    assert "Audit trail review passed" in first_notif["message"]

    # 6. Mark notification as read
    notif_id = first_notif["id"]
    res_mark = client.post(f"/api/v1/notifications/{notif_id}/read", headers=advisor_headers)
    assert res_mark.status_code == 200
    assert res_mark.json()["is_read"] is True

    # 7. Check unread count after marking read
    res_notif_after = client.get("/api/v1/notifications", headers=advisor_headers)
    assert res_notif_after.json()["unread_count"] == 0
