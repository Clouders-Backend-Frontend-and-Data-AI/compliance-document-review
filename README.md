# 🛡️ Compliance Document Review System — Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg?style=flat)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed%20%E2%9C%93-brightgreen.svg?style=flat)](tests/)
[![Privacy Perimeter](https://img.shields.io/badge/Privacy-Zero%20Client%20PII%20Leakage-success.svg?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg?style=flat)](LICENSE)

An enterprise-grade, privacy-preserving compliance document review and vector-assisted decision platform built with **FastAPI**, **SQLAlchemy**, and **Pydantic**.

This system bridges the gap between **Financial Advisors** (who need rapid turnaround on client proposals and marketing materials) and **Compliance Officers** (who must enforce strict SEC, FINRA, and banking regulations). It combines **deterministic server-side PII sanitization**, **multi-format text extraction (PDF/DOCX/XLSX)**, **3-way semantic vector intelligence**, **document revision threading**, and an **immutable audit trail**—with a strict human-in-the-loop governance model.

---

## 📑 Table of Contents

- [The Problem \& Why We Built This](#-the-problem--why-we-built-this)
- [System Architecture \& Data Flow](#-system-architecture--data-flow)
- [Core Highlights \& Guarantees](#-core-highlights--guarantees)
  - [1. Deterministic Server-Side PII Masking](#1-deterministic-server-side-pii-masking)
  - [2. Strict Role Boundaries (RBAC)](#2-strict-role-boundaries-rbac)
  - [3. Triple-Engine Vector Intelligence](#3-triple-engine-vector-intelligence)
  - [4. AI Compliance Assist with Graceful Fallback](#4-ai-compliance-assist-with-graceful-fallback)
  - [5. Document Revision Threading](#5-document-revision-threading)
  - [6. Immutable Audit Trail \& In-App Alerts](#6-immutable-audit-trail--in-app-alerts)
- [Quickstart Guide](#-quickstart-guide)
  - [Prerequisites](#prerequisites)
  - [1. Clone \& Setup Environment](#1-clone--setup-environment)
  - [2. Configure Settings (.env)](#2-configure-settings-env)
  - [3. Initialize \& Seed Database](#3-initialize--seed-database)
  - [4. Launch the Server](#4-launch-the-server)
- [Interactive API Walkthrough (Step-by-Step curl Guide)](#-interactive-api-walkthrough-step-by-step-curl-guide)
- [API Reference Matrix](#-api-reference-matrix)
- [Project Directory Structure](#-project-directory-structure)
- [Running Automated Tests](#-running-automated-tests)
- [Configuration \& Production Hardening](#-configuration--production-hardening)
- [Frequently Asked Questions (FAQ)](#-frequently-asked-questions-faq)

---

## 💡 The Problem & Why We Built This

In wealth management and financial services, client-facing documents (proposals, performance tear sheets, marketing pitch decks) must pass rigorous regulatory scrutiny before distribution. 

1. **The Compliance Bottleneck**: Compliance teams spend hours manually cross-checking documents against hundreds of regulatory requirements (e.g., missing disclaimers, promissory returns, improper disclosures).
2. **The LLM Privacy Dilemma**: Handing client proposals to public LLMs (ChatGPT, Claude, Gemini) risks leaking sensitive **PII** (names, account numbers, net worth, portfolio holdings, contact info) directly into third-party servers.
3. **The "AI Replacing Humans" Risk**: Fully automated approval bots create massive regulatory liability.

### Our Solution
- **Privacy First**: All PII is identified, hashed, and substituted with synthetic placeholders (`[CLIENT_1]`, `[ACCOUNT_1]`) on the local server **before** any vector search or AI prompt execution.
- **Human-in-the-Loop**: The AI never approves or rejects documents. It acts strictly as an **augmented copilot** for the Compliance Officer, highlighting matched rules, missing disclosures, and relevant historical precedents.
- **Total Auditability**: Every view, download, AI suggestion, and approval decision is logged in an append-only ledger for regulatory audits.

---

## 🏛️ System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Advisor Space
        ADV[Financial Advisor] -->|1. Uploads PDF/DOCX/XLSX| UPLOAD[Document Ingestion API]
    end

    subgraph Privacy Perimeter (Local Server)
        UPLOAD --> EXTRACT[Text Extractor Engine\nPDF / Word / Excel]
        EXTRACT --> MASK[Deterministic PII Masker]
        MASK -->|Stores Local Vault| PII_DB[(pii_mappings Table)]
        MASK -->|2. Sanitized Clean Text Only| VECTOR[Vector Engine]
        
        AUDIT[Append-Only Audit Log]
        NOTIF[In-App Notification Dispatcher]
    end

    subgraph Vector Retrieval Engine
        VECTOR --> V1[Engine 1: Regulatory Rule Matching]
        VECTOR --> V2[Engine 2: Missing Disclosure by Absence]
        VECTOR --> V3[Engine 3: Top-3 Historical Precedents]
    end

    subgraph AI Intelligence Layer
        V1 & V2 & V3 --> AI_SVC[AI Assist Engine\nGemini 1.5 Flash OR Local Heuristic Fallback]
        AI_SVC -->|3. Structured Flags & Explanations| CACHE[(ai_analyses & compliance_flags)]
    end

    subgraph Officer Space
        OFF[Compliance Officer] -->|4. Inspects Traceable Flags & Precedents| REVIEW_UI[Review Queue]
        CACHE -.-> REVIEW_UI
        OFF -->|5. Submits Final Decision| DECISION[State Machine]
        DECISION -->|Approved / Rejected / Needs Revision| DOC_DB[(documents Table)]
        DECISION -->|Logs Action| AUDIT
        DECISION -->|Alerts Advisor| NOTIF
        DECISION -->|Indexes as New Precedent| VECTOR
    end
```

---

## ✨ Core Highlights & Guarantees

### 1. Deterministic Server-Side PII Masking
Documents never leave the server perimeter unmasked. Our deterministic regex and heuristic pipeline identifies and replaces:
- **Client & Executive Names**: Replaced with `[CLIENT_1]`, `[CLIENT_2]`, etc.
- **Email Addresses**: Replaced with `[EMAIL_1]`, `[EMAIL_2]`
- **Phone Numbers**: Formatted phone numbers become `[PHONE_1]`
- **Social Security / Tax IDs**: Replaced with `[SSN_1]`
- **Account & Portfolio IDs**: Patterns like `ACCT-XXXX` become `[ACCOUNT_1]`
- **Street & Postal Addresses**: Replaced with `[ADDRESS_1]`
- **Specific Account Balances**: Client-tied balances are replaced with `[AMOUNT_1]`

> 🔒 **Verify it yourself**: Call `GET /api/v1/documents/{id}/outbound-payload` to see the exact text sent to the AI service. Zero client PII ever reaches external endpoints.

#### Masking Example:
```text
Raw Text:
"Dear Robert Henderson, your portfolio ACCT-982341 has a balance of $1,500,000. Contact robert.henderson@examplecorp.com at (555) 234-5678."

Masked Payload:
"Dear [CLIENT_1], your portfolio [ACCOUNT_1] has a balance of [AMOUNT_1]. Contact [EMAIL_1] at [PHONE_1]."
```

---

### 2. Strict Role Boundaries (RBAC)
User roles are fixed at registration (`advisor` vs `officer`) and enforced at the route dependency layer:

| User Role | Document Upload | Revisions | Review Queue | Approve / Reject | Audit Trail |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Advisor** | ✅ Yes | ✅ Yes (on `needs_revision`) | ❌ Isolated to own docs | ❌ 403 Forbidden | ✅ Own documents |
| **Officer** | ❌ 403 Forbidden | ❌ No | ✅ Full unified queue | ✅ Yes | ✅ All documents |

- Advisors can never view documents belonging to other advisors.
- Unauthenticated requests immediately receive `401 Unauthorized`.

---

### 3. Triple-Engine Vector Intelligence
When a document is analyzed, the backend triggers three distinct vector search jobs:

1. **Regulatory Rule Matching**: Chunks the document and retrieves the most relevant SEC / FINRA compliance rules from the pre-seeded regulatory corpus.
2. **Missing-Disclosure Detection by Absence**: Evaluates document similarity against mandatory required disclosures (e.g., *Past Performance Disclaimer*, *Not FDIC Insured Notice*, *Tax Advice Disclaimer*). If semantic similarity across all chunks falls below `DISCLOSURE_ABSENCE_THRESHOLD = 0.60`, a missing disclosure flag is automatically raised.
3. **Precedent Retrieval**: Queries 100+ historical compliance cases to surface the **Top 3 most similar past submissions**, showing how past officers ruled and why.

---

### 4. AI Compliance Assist with Graceful Fallback
- **Structured Findings**: Generates an executive summary and pinpointed flags containing:
  - Exact document passage excerpt
  - Matched regulatory rule ID
  - Severity level (`high`, `medium`, `low`, `info`)
  - Clear explanation of the violation
  - Concrete suggested remediation
- **Graceful Fallback Mode**: If the Google Gemini API key is not supplied, rate-limited, or network-blocked, the system automatically falls back to an internal heuristic and vector-backed analysis engine (`status: "degraded"`). **The compliance review pipeline never grinds to a halt.**

---

### 5. Document Revision Threading
When an officer marks a document as `needs_revision`:
- The advisor uploads a corrected version via `POST /documents/{id}/revise`.
- The new document automatically inherits the same `thread_id`.
- The version counter increments ($v1 \to v2 \to v3$).
- The `parent_document_id` links backward, preserving the entire revision history.
- The entire thread history is inspectable via `GET /documents/{id}/thread`.

```mermaid
stateDiagram-v2
    [*] --> pending_review: Advisor Uploads v1
    pending_review --> approved: Officer Approves
    pending_review --> rejected: Officer Rejects
    pending_review --> needs_revision: Officer Requests Changes
    needs_revision --> pending_review: Advisor Uploads v2 (Revises)
    approved --> [*]
    rejected --> [*]
```

---

### 6. Immutable Audit Trail & In-App Alerts
- **Tamper-Evident Event Logging**: Every lifecycle event (`submitted`, `viewed`, `analysis_generated`, `decided`, `resubmitted`, `downloaded`) is captured in the `audit_events` table with timestamps, user IDs, roles, and event metadata.
- **In-App Notification Dispatcher**: As soon as an officer makes a review decision, an in-app alert is generated for the submitting advisor. Advisors can fetch unread counts and mark notifications as read.

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.10+** (Tested through Python 3.14)
- **Git**

### 1. Clone & Setup Environment

```bash
# 1. Clone the repository
git clone https://github.com/Clouders-Backend-Frontend-and-Data-AI/-Document-Review-App-Backend.git
cd -Document-Review-App-Backend

# 2. Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

---

### 2. Configure Settings (`.env`)

Copy the template `.env.example` to create your local `.env`:

```bash
# Windows:
copy .env.example .env
# Linux / macOS:
cp .env.example .env
```

Here is what `.env` contains:

```ini
# Application Secrets
PROJECT_NAME="Compliance Document Review API"
SECRET_KEY="super-secret-key-for-jwt-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database & Storage
DATABASE_URL="sqlite:///./compliance_app.db"
UPLOAD_DIR="./uploads"
MAX_UPLOAD_SIZE_MB=10

# AI Configuration (Optional: Gemini 1.5 Flash)
# Leave blank to use built-in offline heuristic fallback
GEMINI_API_KEY=""
GEMINI_MODEL="gemini-1.5-flash"
AI_TIMEOUT_SECONDS=30

# Vector Engine Thresholds
DISCLOSURE_ABSENCE_THRESHOLD=0.60
PRECEDENT_TOP_K=3
RULE_RETRIEVAL_TOP_K=5
```

> 💡 **No API Key? No Problem!** If you do not have a Gemini API key, the system functions seamlessly using local TF-IDF and heuristic compliance rules.

---

### 3. Initialize & Seed Database

Run the seed scripts to populate 25+ regulatory rules, 100+ historical precedents, default test accounts, and realistic sample documents:

```bash
# Seed rules, precedents, and default accounts
python scripts/seed_corpus.py

# Generate sample PDF, DOCX, and XLSX files in sample_test_files/
python scripts/generate_sample_files.py
```

#### Pre-Configured Demo Accounts:
| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Financial Advisor** | `advisor@example.com` | `Advisor123!` | Upload & Revise Proposals |
| **Compliance Officer** | `officer@example.com` | `Officer123!` | Review Queue & Decisions |

---

### 4. Launch the Server

Start the FastAPI application using `uvicorn`:

```bash
uvicorn app.main:app --reload --port 8000
```

- 🌐 **API Base URL**: `http://localhost:8000`
- 📚 **Interactive Swagger UI Docs**: `http://localhost:8000/docs`
- 📖 **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 🛠️ Interactive API Walkthrough (Step-by-Step `curl` Guide)

Follow this complete lifecycle demonstration using `curl` or your favorite API client.

### Step 1: Login as Financial Advisor
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "advisor@example.com", "password": "Advisor123!"}'
```
*Response returns your JWT bearer token (`ADVISOR_TOKEN`).*

---

### Step 2: Upload a Proposal (DOCX / PDF / XLSX)
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <ADVISOR_TOKEN>" \
  -F "file=@sample_test_files/sample_compliant_proposal.docx" \
  -F "title=Henderson Retirement Strategy 2024" \
  -F "document_type=marketing_presentation"
```
*Response returns document ID (e.g. `doc_123`), version 1, and `pending_review` status.*

---

### Step 3: Verify Zero PII Leakage (Outbound Payload Inspection)
```bash
curl -X GET http://localhost:8000/api/v1/documents/<DOC_ID>/outbound-payload \
  -H "Authorization: Bearer <ADVISOR_TOKEN>"
```
*Notice how client names, accounts, emails, and balances are converted to `[CLIENT_1]`, `[ACCOUNT_1]`, etc.*

---

### Step 4: Login as Compliance Officer
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "officer@example.com", "password": "Officer123!"}'
```
*Response returns the officer's JWT bearer token (`OFFICER_TOKEN`).*

---

### Step 5: Fetch AI Compliance Findings & Precedents
```bash
curl -X GET http://localhost:8000/api/v1/documents/<DOC_ID>/assist \
  -H "Authorization: Bearer <OFFICER_TOKEN>"
```
*Returns executive summary, missing disclosure warnings, matched SEC rules, and Top-3 historical precedents.*

---

### Step 6: Submit a Compliance Decision
```bash
curl -X POST http://localhost:8000/api/v1/documents/<DOC_ID>/review \
  -H "Authorization: Bearer <OFFICER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "needs_revision",
    "comments": "Please include standard SEC-MKT-02 registration disclosure on slide 2 before approval."
  }'
```

---

### Step 7: Advisor Checks In-App Notifications
```bash
curl -X GET http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer <ADVISOR_TOKEN>"
```
*Shows instant notification indicating the officer reviewed the document and requested revisions.*

---

### Step 8: Advisor Uploads Revised Version (v2)
```bash
curl -X POST http://localhost:8000/api/v1/documents/<DOC_ID>/revise \
  -H "Authorization: Bearer <ADVISOR_TOKEN>" \
  -F "file=@sample_test_files/sample_compliant_proposal.docx"
```
*Automatically creates version 2 with the same `thread_id` and resets state to `pending_review`.*

---

### Step 9: View the Full Audit Trail
```bash
curl -X GET "http://localhost:8000/api/v1/documents/<DOC_ID>/audit?thread=true" \
  -H "Authorization: Bearer <OFFICER_TOKEN>"
```
*Returns the complete immutable timeline: upload $\to$ view $\to$ AI analysis $\to$ decision $\to$ revision.*

---

## 📋 API Reference Matrix

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/api/v1/auth/signup` | Public | Register new user as `advisor` or `officer` |
| **`POST`** | `/api/v1/auth/login` | Public | Authenticate user and receive JWT token |
| **`GET`** | `/api/v1/auth/me` | Authenticated | Retrieve authenticated user profile |
| **`POST`** | `/api/v1/documents/upload` | **Advisor Only** | Upload document (`.pdf`, `.docx`, `.xlsx` $\le 10$ MB) |
| **`GET`** | `/api/v1/documents` | Authenticated | List documents (Advisor sees own; Officer sees queue) |
| **`GET`** | `/api/v1/documents/{id}` | Authenticated | Get document details & extracted text (logs view audit) |
| **`GET`** | `/api/v1/documents/{id}/thread` | Authenticated | Get full revision history for the document thread |
| **`POST`** | `/api/v1/documents/{id}/revise` | **Advisor Only** | Submit revised file for document in `needs_revision` |
| **`GET`** | `/api/v1/documents/{id}/download` | Authenticated | Download original uploaded binary file |
| **`POST`** | `/api/v1/documents/{id}/review` | **Officer Only** | Submit review decision (`approved`, `rejected`, `needs_revision`) |
| **`GET`** | `/api/v1/documents/{id}/assist` | Authenticated | Get AI summary, traceable flags & top-3 precedents |
| **`POST`** | `/api/v1/documents/{id}/assist/retry` | **Officer Only** | Force re-run AI compliance analysis |
| **`GET`** | `/api/v1/documents/{id}/outbound-payload` | Authenticated | View exact server-side masked payload sent to AI |
| **`GET`** | `/api/v1/documents/{id}/audit` | Authenticated | Retrieve immutable audit events (`?thread=true` supported) |
| **`GET`** | `/api/v1/notifications` | Authenticated | Get in-app alerts with unread counter |
| **`POST`** | `/api/v1/notifications/{id}/read` | Authenticated | Mark individual notification as read |
| **`POST`** | `/api/v1/notifications/read-all` | Authenticated | Mark all notifications as read |
| **`GET`** | `/api/v1/corpus/rules` | Authenticated | Query compliance rules and disclosure catalogue |
| **`GET`** | `/api/v1/corpus/precedents` | Authenticated | Query precedent vector database |

---

## 📂 Project Directory Structure

```text
├── .env.example                    # Template environment configuration
├── .env                            # Local environment configuration
├── requirements.txt                # Python package dependencies
├── README.md                       # Comprehensive documentation & guide
├── compliance_app.db               # SQLite database (auto-created)
├── app/
│   ├── main.py                     # FastAPI app factory, CORS, and startup hooks
│   ├── api/
│   │   ├── deps.py                 # RBAC dependencies (require_advisor, require_officer)
│   │   └── v1/
│   │       ├── auth.py             # Signup and JWT authentication endpoints
│   │       ├── documents.py        # Upload, list, detail, revise, download endpoints
│   │       ├── reviews.py          # Officer decision & AI assist endpoints
│   │       ├── audit.py            # Audit trail querying endpoints
│   │       ├── notifications.py    # In-app notifications endpoints
│   │       ├── corpus.py           # Regulatory rules & precedents endpoints
│   │       └── router.py           # Combined API router aggregator
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings application config
│   │   ├── database.py             # SQLAlchemy session and engine management
│   │   └── security.py             # Password hashing (bcrypt) & JWT tokens
│   ├── models/                     # SQLAlchemy ORM database models
│   │   ├── base.py                 # Enums: DocumentStatus, UserRole, RuleCategory
│   │   ├── user.py                 # User model
│   │   ├── document.py             # Document model (with versioning & thread links)
│   │   ├── review.py               # ReviewDecision model
│   │   ├── ai_analysis.py          # AIAnalysis and ComplianceFlag models
│   │   ├── audit.py                # Append-only AuditEvent model
│   │   ├── notification.py         # In-app Notification model
│   │   ├── pii_mapping.py          # Server-side PIIMapping vault model
│   │   └── vector_corpus.py        # ComplianceRule and PrecedentSubmission models
│   ├── schemas/                    # Pydantic v2 validation & response schemas
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── review.py
│   │   ├── ai_analysis.py
│   │   ├── audit.py
│   │   ├── notification.py
│   │   └── vector_corpus.py
│   └── services/                   # Core business logic services
│       ├── extractor.py            # Multi-format parser (pypdf, docx, openpyxl)
│       ├── pii_masker.py           # Deterministic PII detection & masking engine
│       ├── vector_engine.py        # TF-IDF embeddings & cosine similarity search
│       ├── ai_assist.py            # Gemini integration + heuristic offline engine
│       ├── document_service.py     # Document state machine & version controller
│       ├── audit_service.py        # Append-only audit logger
│       └── notification_service.py # In-app notification dispatcher
├── scripts/
│   ├── seed_corpus.py              # Seeds 25+ rules, 100+ precedents, demo accounts
│   └── generate_sample_files.py    # Generates test PDF, DOCX, and XLSX files
├── sample_test_files/              # Generated test files for quick testing
└── tests/                          # 16-suite automated Pytest test suite
    ├── conftest.py
    ├── test_auth_and_roles.py
    ├── test_pii_masker.py
    ├── test_state_machine.py
    ├── test_vector_retrieval.py
    ├── test_audit_and_notifications.py
    ├── test_graceful_degradation.py
    └── test_extended_coverage.py
```

---

## 🧪 Running Automated Tests

The repository includes a comprehensive test suite covering all critical edge cases:

- **Authentication & RBAC**: Confirms advisors cannot review docs, officers cannot upload docs, and unauthorized users are blocked.
- **PII Masking Integrity**: Verifies zero sensitive client data leaks in the outbound payload.
- **State Machine Transitions**: Tests the full lifecycle from upload $\to$ review $\to$ revision $\to$ approval.
- **Vector Retrieval**: Validates rule lookup accuracy, precedent search, and disclosure-by-absence triggers.
- **Audit Logging**: Asserts all actions trigger tamper-evident audit records.
- **Graceful Fallback**: Verifies the AI assist service functions normally even without a Gemini API key.

Run the test suite with:

```bash
python -m pytest tests/ -v
```

Expected output:
```text
============================= test session starts =============================
collected 16 items

tests/test_audit_and_notifications.py::test_audit_trail_and_in_app_notifications PASSED [  6%]
tests/test_auth_and_roles.py::test_signup_roles PASSED                   [ 12%]
tests/test_auth_and_roles.py::test_unauthenticated_rejected PASSED       [ 18%]
tests/test_auth_and_roles.py::test_role_boundary_advisor_can_upload_officer_cannot PASSED [ 25%]
tests/test_auth_and_roles.py::test_role_boundary_officer_can_review_advisor_cannot PASSED [ 31%]
tests/test_auth_and_roles.py::test_advisor_document_isolation PASSED     [ 37%]
tests/test_extended_coverage.py::test_multiformat_extraction_service PASSED [ 43%]
tests/test_extended_coverage.py::test_file_download_endpoint PASSED      [ 50%]
tests/test_extended_coverage.py::test_corpus_endpoints PASSED            [ 56%]
tests/test_graceful_degradation.py::test_graceful_degradation_without_ai_key PASSED [ 62%]
tests/test_pii_masker.py::test_pii_masking_comprehensive PASSED          [ 68%]
tests/test_pii_masker.py::test_outbound_payload_privacy_guarantee PASSED [ 75%]
tests/test_state_machine.py::test_full_document_lifecycle_and_revision_threading PASSED [ 81%]
tests/test_vector_retrieval.py::test_rule_lookup_retrieval PASSED        [ 87%]
tests/test_vector_retrieval.py::test_disclosure_detection_by_absence PASSED [ 93%]
tests/test_vector_retrieval.py::test_precedent_search PASSED             [100%]

======================== 16 passed in 5.69s ========================
```

---

## ⚙️ Configuration & Production Hardening

### Database Migration (SQLite to PostgreSQL)
To connect to an enterprise PostgreSQL instance, simply update `DATABASE_URL` in `.env`:
```ini
DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/compliance_db"
```

### Tuning Vector Similarity Thresholds
You can fine-tune vector sensitivity directly in `.env`:
- `DISCLOSURE_ABSENCE_THRESHOLD` (Default `0.60`): Raising this to `0.70` makes missing-disclosure detection stricter; lowering it to `0.50` makes it more forgiving.
- `PRECEDENT_TOP_K` (Default `3`): Number of historical precedents surfaced during officer review.
- `RULE_RETRIEVAL_TOP_K` (Default `5`): Maximum regulatory rules paired with document passages.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Q: Does any client PII ever get sent to Gemini or external LLMs?</b></summary>

**No.** The `PIIMasker` runs locally on the application server. It scrubs all names, phone numbers, emails, addresses, account IDs, and monetary balances before any vector embedding calculation or LLM payload generation. The mapping is stored securely in the local `pii_mappings` database table.
</details>

<details>
<summary><b>Q: What happens if the Gemini API key is invalid or rate-limited?</b></summary>

The backend includes a graceful degradation layer (`ai_assist.py`). If the API call fails or times out, it automatically invokes a local heuristic and vector-backed rules engine that identifies promissory language and missing disclosures. The analysis is marked with `status="degraded"` and the review queue remains completely operational.
</details>

<details>
<summary><b>Q: Can an advisor approve their own documents?</b></summary>

**No.** Role permissions are enforced at the API route dependency level via `require_officer`. Any attempt by an advisor to call `POST /documents/{id}/review` results in a hard `403 Forbidden` response.
</details>

<details>
<summary><b>Q: How are revisions linked together?</b></summary>

Every document belongs to a `thread_id`. When an advisor uploads a revised document via `/documents/{id}/revise`, the new document receives `parent_document_id = original_document_id`, inherits the `thread_id`, and increments `version_number` ($v1 \to v2$). Calling `GET /documents/{id}/thread` returns the full chronological chain.
</details>

<details>
<summary><b>Q: What file formats are supported?</b></summary>

The ingestion service supports `.pdf` (via `pypdf`), `.docx` (via `python-docx`), and `.xlsx` (via `openpyxl`) up to 10 MB per file.
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).