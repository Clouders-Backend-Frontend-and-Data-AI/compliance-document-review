# Compliance Review — Frontend

React + Vite frontend for the Compliance Document Review App, built against the real
`compliance-document-review` FastAPI backend schemas (verified against
`app/schemas/*.py` and `app/api/v1/*.py` in the backend repo, not just its README).

## Stack
- React Router — role-gated routing (`/advisor/*`, `/officer/*`)
- TanStack Query — data fetching, caching, and the AI assist panel's loading/error/retry states
- Zustand — auth state (JWT + role), persisted to localStorage
- Tailwind CSS — styling

## Setup
```bash
npm install
cp .env.example .env
npm run dev
```

## Running without a backend (mock mode)
Set `VITE_USE_MOCK=true` in `.env` to run the entire app against in-memory fixtures —
no backend, no network calls. The mock data uses the exact same field names as the real
API (verified against the backend's Pydantic schemas), so it's a faithful preview, not a
simplified stand-in.

Demo logins in mock mode:
- Advisor: `advisor@example.com` / `Advisor123!`
- Officer: `officer@example.com` / `Officer123!`

Switch `VITE_USE_MOCK=false` (and set `VITE_API_BASE_URL`) once the real backend is
running — no other code changes needed.

## API contract notes (things that are easy to get wrong)
- `GET /documents` and `GET /documents/{id}/audit` return **plain arrays**, not `{ items }`.
- Upload and revise responses are wrapped: `{ document, message }` — read `.document`.
- **Revise requires `title` and `document_type` in the form data, not just the file.**
- A document's version is `version_number`, not `version`.
- The advisor on a document is a nested object: `doc.advisor.full_name`, not `advisor_name`.
- `POST /documents/{id}/review` expects `{ status, comment }` (not `decision`/`comments`),
  and `comment` is required (min 3 chars) on every decision, including approvals.
- The assist endpoint's `status` field is `"completed"` or `"degraded"` (not `"complete"`).
- Precedents come back as `precedent_matches`, each with `officer_comment` (not `comment`).
- The outbound-payload endpoint returns `masked_payload` (not `masked_text`).
- Audit events use `created_at` (not `timestamp`).
- Notifications come back as `{ unread_count, notifications: [...] }`, each with `is_read`.
- Signup needs `full_name` (not `name`).

## Structure
- `src/api/client.js` — every backend endpoint in one place, with the JWT attached
  automatically; routes to `src/api/mock.js` when `VITE_USE_MOCK=true`
- `src/api/mock.js` — in-memory fixtures matching the real schema field-for-field
- `src/auth/` — login/signup logic and the role-gated route wrapper
- `src/components/AssistPanel.jsx` — the AI summary/flags/precedents panel, with a dedicated
  degraded/error state so the review page still works if the AI service is down
- `src/components/AuditTrail.jsx` — renders `GET /documents/{id}/audit`
- `src/pages/advisor/` — submit-and-track dashboard, including the outbound-payload viewer
  and revision upload flow
- `src/pages/officer/` — status-filterable queue and the decision-plus-comment review page

## Known gaps / next steps
- No document preview rendering for DOCX/XLSX — currently shows `extracted_text` if the
  backend returns it, otherwise a download link.
- Precedent click-through (viewing the actual precedent document) isn't wired up yet.
- Haven't tested against a *running* instance of the backend yet — this is aligned against
  the schemas and route code, but worth a real end-to-end pass once the backend is up
  (`uvicorn app.main:app --reload --port 8000` per the backend README) to catch anything
  the static schemas didn't reveal (e.g. actual error response shapes, CORS config).
