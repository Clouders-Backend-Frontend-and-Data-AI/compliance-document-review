# Compliance Document Review App - Backend Architecture & Implementation Plan

## Problem & System Scope
Financial advisors generate client-facing materials (brochures, emails, social posts, meeting notes, proposals) that legally require compliance review before distribution. This project implements a secure, role-governed, privacy-preserving backend with:
1. **Strict Role Boundary Enforcement**: Fixed `advisor` and `officer` roles with server-side 403 access control.
2. **Deterministic Server-Side PII Masker**: Zero client PII (names, emails, phones, SSNs, account numbers, monetary figures) leaves the perimeter in LLM prompts or embeddings.
3. **Multi-Format Ingestion**: Text extraction from PDF, DOCX, and XLSX (10MB upload limit).
4. **Vector Search Engine**:
   - **Rule Retrieval**: Similarity-based lookup against regulatory & firm compliance standards.
   - **Disclosure-by-Absence**: Detection of missing mandatory disclaimers via maximum semantic distance.
   - **Precedent Search**: Top-3 similarity retrieval of historical reviews (masked text + decision + officer commentary).
5. **AI Assist Engine with Graceful Degradation**: Cached summary, flag generation with passage excerpts and rule linkage, with offline fallback so the review queue never gets blocked.
6. **Document State Machine & Revision Threading**: Full lifecycle (`pending_review` -> `approved` | `rejected` | `needs_revision`) with linked resubmission chains.
7. **Append-Only Audit Trail & In-App Notifications**: Immutable logging of submission, viewing, decisions, and in-app alerts.
8. **Corpora Seeding & Clean Checkout**: Scripted seeding of 30+ compliance rules, mandatory disclosures, and ~100 precedent documents, plus automated test suite.

---

## User Review Required

> [!IMPORTANT]
> **Privacy Wall Guarantee**: Document text is never sent to external AI APIs (Gemini/Groq/OpenRouter) or hosted embedding models without first passing through the server-side regex & heuristic PII masker. All placeholder mappings remain isolated in the server database.

> [!NOTE]
> **Clean Checkout & Portability**: The backend is built using **FastAPI + SQLAlchemy + Pydantic** with SQLite as the default zero-dependency database (and optional PostgreSQL/pgvector support via `.env`). The vector similarity engine supports both Gemini API embeddings and an offline deterministic vectorizer, ensuring that all tests and retrieval workflows pass cleanly on any machine out of the box.

---

## Open Questions
- None blocking. We are providing a fully featured, turnkey backend with complete role enforcement, test suite, and seed scripts.

---

## Proposed Changes

### 1. Project Configuration & Dependencies
- `requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, Pydantic, PyJWT, passlib, bcrypt, pypdf, python-docx, openpyxl, httpx, pytest, pytest-asyncio, numpy, scikit-learn.
- `.env.example`: Configurable keys (`SECRET_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, `UPLOAD_DIR`, etc.).
- `README.md`: Complete setup instructions, API documentation, testing instructions, and architecture diagrams.

### 2. Database Models & Schema (`app/models/`)
- `app/models/user.py`: `User` with role enum (`advisor`, `officer`), password hash, created_at.
- `app/models/document.py`: `Document` with status enum (`pending_review`, `approved`, `rejected`, `needs_revision`), thread_id, parent_document_id, version_number, file metadata, extracted_text.
- `app/models/review.py`: `ReviewDecision` with decision status, officer comment, timestamp.
- `app/models/ai_analysis.py`: `AIAnalysis` (cached summary, outbound payload snapshot) and `ComplianceFlag` (passage excerpt, matched rule, explanation, severity).
- `app/models/audit.py`: `AuditEvent` (append-only: `submitted`, `viewed`, `decided`, `resubmitted`, `analysis_generated`, `downloaded`).
- `app/models/notification.py`: `Notification` (in-app alerts, read status).
- `app/models/pii_mapping.py`: `PIIMapping` (isolated server-side placeholder-to-original map).
- `app/models/vector_corpus.py`: `ComplianceRule` (rules & disclosures with vector representations) and `PrecedentSubmission` (past reviewed submissions with vector index).

### 3. Core Security & Authentication (`app/core/` & `app/api/deps.py`)
- `app/core/config.py`: Environment settings (JWT secrets, upload caps, API credentials).
- `app/core/security.py`: Password hashing (bcrypt) and JWT token generation/validation.
- `app/api/deps.py`:
  - `get_db`: Database session dependency.
  - `get_current_user`: Authentication dependency.
  - `require_advisor`: Strictly rejects non-advisors with HTTP 403.
  - `require_officer`: Strictly rejects non-officers with HTTP 403.

### 4. Text Extraction & PII Masking Services (`app/services/`)
- `app/services/extractor.py`: Multi-format text extractor for PDF (`pypdf`), DOCX (`python-docx`), and XLSX (`openpyxl`) with clean normalization.
- `app/services/pii_masker.py`:
  - Regex & heuristic detection for Names, Emails, Phones, SSNs/Tax IDs, Account Numbers, Physical Addresses, and Person-tied Monetary Figures.
  - Deterministic placeholder generation (`[CLIENT_1]`, `[ACCOUNT_1]`, `[EMAIL_1]`, etc.).
  - Database mapping storage.
  - `mask_text(text, doc_id, db)` and `unmask_text(masked_text, doc_id, db)`.
  - Outbound payload inspector method for verification and auditing.

### 5. Vector Engine & Retrieval (`app/services/vector_engine.py`)
- Embedding computation (Gemini API with fallback cosine-vectorizer).
- **Rule Retrieval**: Chunk document and match top relevant compliance rules.
- **Disclosure-by-Absence**: Evaluate semantic distance against required disclosures. If maximum similarity < threshold, generate a missing disclosure flag.
- **Precedent Search**: Retrieve top-3 most similar reviewed submissions with decisions and officer feedback.

### 6. AI Assist Service (`app/services/ai_assist.py`)
- Orchestrates Masking -> Retrieval -> LLM Generation -> Unmasking.
- Caches analysis result in DB (generated once per submission/retry).
- Graceful degradation: Fallback analysis when API key is missing or offline.
- Rule: AI never modifies document review status.

### 7. Document Lifecycle & Threading (`app/services/document_service.py`)
- Submission handling with 10MB limit.
- Resubmission / Revision linking (inherits `thread_id`, increments `version_number`, links `parent_document_id`).
- Officer decision recording (updates document status, logs audit event, triggers in-app notification, updates precedent index).

### 8. API Endpoints (`app/api/v1/`)
- `auth.py`: `POST /signup`, `POST /login`, `GET /me`.
- `documents.py`:
  - `POST /documents/upload` (Advisor only).
  - `GET /documents` (Advisor sees own; Officer sees queue/all with status filters).
  - `GET /documents/{id}` (Details, extracted text, metadata, triggers 'viewed' audit event).
  - `GET /documents/{id}/thread` (Entire revision history for the document thread).
  - `POST /documents/{id}/revise` (Advisor only - submits revision for 'needs_revision' document).
  - `GET /documents/{id}/download` (Download uploaded binary file).
- `reviews.py`:
  - `POST /documents/{id}/review` (Officer only - records approved/rejected/needs_revision decision + comment).
  - `GET /documents/{id}/assist` (Retrieve cached AI summary, flags, precedent matches, or trigger analysis).
  - `POST /documents/{id}/assist/retry` (Officer only - retry analysis).
  - `GET /documents/{id}/outbound-payload` (Inspect exact masked payload sent to AI).
- `audit.py`:
  - `GET /documents/{id}/audit` (Retrieve immutable audit trail for document/thread).
- `notifications.py`:
  - `GET /notifications` (User's in-app notifications with unread count).
  - `POST /notifications/{id}/read` (Mark notification as read).
  - `POST /notifications/read-all` (Mark all as read).
- `corpus.py`:
  - `GET /corpus/rules` (View compliance rule catalogue).
  - `GET /corpus/precedents` (View precedent library).

### 9. Seed Scripts & Data Generation (`scripts/`)
- `scripts/seed_corpus.py`:
  - Populates 30+ compliance rules & required disclosures (FINRA/SEC style marketing rules, prohibited promises, required disclaimers).
  - Populates 100+ synthetic precedent submissions with varied outcomes and officer feedback.
- `scripts/generate_sample_files.py`:
  - Generates sample PDF, DOCX, and XLSX files with realistic marketing text, disclosures, and synthetic PII for testing.

### 10. Test Suite (`tests/`)
- `test_auth_and_roles.py`: Role boundary enforcement (advisor vs officer endpoints).
- `test_pii_masker.py`: PII masking accuracy, placeholder stability, and zero-leak verification.
- `test_state_machine.py`: Document lifecycle, revision linking, and thread ordering.
- `test_vector_retrieval.py`: Rule lookup, missing disclosure detection, top-3 precedents.
- `test_audit_and_notifications.py`: Audit trail append-only behavior and in-app notifications.
- `test_graceful_degradation.py`: Review UI functionality when AI API is unavailable.

---

## Verification Plan

### Automated Tests
- Run `python -m pytest tests/ -v` to execute all unit and integration tests.

### Manual Verification & End-to-End Walkthrough
- Run the FastAPI server (`python main.py` or `uvicorn app.main:app --reload`).
- Execute seeded end-to-end user scenario:
  1. Sign up Advisor (`advisor@example.com`) and Officer (`officer@example.com`).
  2. Upload document as Advisor.
  3. Verify PII masking on the outbound payload.
  4. Fetch AI assist summary, flags, and top-3 precedent matches.
  5. Attempt to submit decision as Advisor -> Confirm 403 Forbidden.
  6. Submit `needs_revision` decision with comment as Officer.
  7. Confirm Advisor receives in-app notification.
  8. Advisor submits revised document -> verify revision thread link and version increment.
  9. Officer approves revision -> verify status and precedent index update.
  10. Retrieve complete thread audit trail showing all actions and timestamps.
