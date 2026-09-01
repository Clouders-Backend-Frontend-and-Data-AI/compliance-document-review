import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db_session
from app.main import app
from app.models.user import User
from app.models.base import UserRole
from app.core.security import get_password_hash, create_access_token
from scripts.seed_corpus import seed_database

# Use in-memory SQLite for testing
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def init_db():
    Base.metadata.create_all(bind=test_engine)
    # Seed rules and precedents in test db
    db = TestingSessionLocal()
    try:
        from scripts.seed_corpus import RULES_DATA
        import json
        from app.models.vector_corpus import ComplianceRule, PrecedentSubmission
        from app.services.vector_engine import VectorEngine
        from app.models.base import DocumentStatus, DocumentType
        
        for r_data in RULES_DATA:
            vec = VectorEngine.generate_embedding(r_data["rule_text"] + " " + r_data["title"])
            rule = ComplianceRule(
                rule_code=r_data["rule_code"],
                category=r_data["category"],
                title=r_data["title"],
                description=r_data["description"],
                rule_text=r_data["rule_text"],
                standard_disclosure=r_data.get("standard_disclosure"),
                embedding_json=json.dumps(vec)
            )
            db.add(rule)
        
        # Add sample precedent
        prec_vec = VectorEngine.generate_embedding("Sample approved market brochure with disclosures")
        prec = PrecedentSubmission(
            title="Sample Test Precedent",
            document_type=DocumentType.BROCHURE,
            masked_text="Sample approved market brochure with disclosures",
            decision=DocumentStatus.APPROVED,
            officer_comment="Approved clean document",
            embedding_json=json.dumps(prec_vec)
        )
        db.add(prec)
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    # Also override for direct import deps
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def test_advisor(db):
    user = User(
        email="test_advisor@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Alice Advisor",
        role=UserRole.ADVISOR
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_advisor_2(db):
    user = User(
        email="test_advisor_2@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Bob Advisor",
        role=UserRole.ADVISOR
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_officer(db):
    user = User(
        email="test_officer@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Oliver Officer",
        role=UserRole.OFFICER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def advisor_headers(test_advisor):
    token = create_access_token(subject=test_advisor.id, role=test_advisor.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def advisor_2_headers(test_advisor_2):
    token = create_access_token(subject=test_advisor_2.id, role=test_advisor_2.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def officer_headers(test_officer):
    token = create_access_token(subject=test_officer.id, role=test_officer.role.value)
    return {"Authorization": f"Bearer {token}"}
