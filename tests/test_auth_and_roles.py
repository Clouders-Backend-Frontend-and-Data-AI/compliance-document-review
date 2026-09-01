import io
from fastapi.testclient import TestClient
from app.models.base import UserRole, DocumentType

def test_signup_roles(client: TestClient):
    # 1. Signup as Advisor
    res = client.post("/api/v1/auth/signup", json={
        "email": "new_adv@example.com",
        "password": "Password123!",
        "full_name": "New Advisor",
        "role": "advisor"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["role"] == "advisor"
    assert "access_token" in data

    # 2. Signup as Officer
    res = client.post("/api/v1/auth/signup", json={
        "email": "new_off@example.com",
        "password": "Password123!",
        "full_name": "New Officer",
        "role": "officer"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["role"] == "officer"

    # 3. Duplicate email rejected
    res = client.post("/api/v1/auth/signup", json={
        "email": "new_adv@example.com",
        "password": "Password123!",
        "full_name": "Duplicate Advisor",
        "role": "advisor"
    })
    assert res.status_code == 400

def test_unauthenticated_rejected(client: TestClient):
    res = client.get("/api/v1/documents")
    assert res.status_code == 401

def test_role_boundary_advisor_can_upload_officer_cannot(client: TestClient, advisor_headers, officer_headers):
    # Sample file content
    file_bytes = b"Sample financial proposal for client Robert Henderson."
    files = {"file": ("proposal.txt", io.BytesIO(file_bytes), "text/plain")}
    data = {"title": "Test Proposal", "document_type": "proposal_letter"}

    # Advisor uploads -> Success (201)
    res = client.post("/api/v1/documents/upload", headers=advisor_headers, data=data, files=files)
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]

    # Officer attempts to upload -> Forbidden (403)
    files2 = {"file": ("proposal.txt", io.BytesIO(file_bytes), "text/plain")}
    res_officer = client.post("/api/v1/documents/upload", headers=officer_headers, data=data, files=files2)
    assert res_officer.status_code == 403
    assert "Operation not permitted" in res_officer.json()["detail"]

def test_role_boundary_officer_can_review_advisor_cannot(client: TestClient, advisor_headers, officer_headers):
    # Upload doc as advisor
    file_bytes = b"Client Name: Alice. Account: 123456. Conservative portfolio proposal."
    files = {"file": ("proposal.txt", io.BytesIO(file_bytes), "text/plain")}
    res = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "Review Role Test", "document_type": "proposal_letter"},
        files=files
    )
    doc_id = res.json()["document"]["id"]

    # Advisor tries to submit a review decision -> Forbidden (403)
    res_adv_review = client.post(
        f"/api/v1/documents/{doc_id}/review",
        headers=advisor_headers,
        json={"status": "approved", "comment": "Advisor self-approving"}
    )
    assert res_adv_review.status_code == 403
    assert "Operation not permitted" in res_adv_review.json()["detail"]

    # Officer submits review decision -> Success (201)
    res_off_review = client.post(
        f"/api/v1/documents/{doc_id}/review",
        headers=officer_headers,
        json={"status": "approved", "comment": "Approved by compliance"}
    )
    assert res_off_review.status_code == 201
    assert res_off_review.json()["status"] == "approved"

def test_advisor_document_isolation(client: TestClient, advisor_headers, advisor_2_headers, officer_headers):
    # Advisor 1 uploads doc
    file_bytes = b"Advisor 1 confidential client data."
    files = {"file": ("doc1.txt", io.BytesIO(file_bytes), "text/plain")}
    res = client.post(
        "/api/v1/documents/upload",
        headers=advisor_headers,
        data={"title": "Advisor 1 Doc", "document_type": "other"},
        files=files
    )
    doc_id = res.json()["document"]["id"]

    # Advisor 2 attempts to view Advisor 1 doc -> Forbidden (403)
    res_adv2 = client.get(f"/api/v1/documents/{doc_id}", headers=advisor_2_headers)
    assert res_adv2.status_code == 403

    # Officer can view any doc -> Success (200)
    res_officer = client.get(f"/api/v1/documents/{doc_id}", headers=officer_headers)
    assert res_officer.status_code == 200
