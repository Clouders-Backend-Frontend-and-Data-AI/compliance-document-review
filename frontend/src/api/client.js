import axios from "axios";
import { mockApi } from "./mock";

// Set VITE_USE_MOCK=true in .env to run the whole app against in-memory fixtures,
// no backend required — useful for demoing the UI before the real API is ready.
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

// Point this at wherever the FastAPI backend is running.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: BASE_URL });

// Attach the JWT to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cdr_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On a 401, the token is dead — clear it and send the user back to login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("cdr_token");
      localStorage.removeItem("cdr_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ---- Auth ----
// Backend: POST /auth/login { email, password } -> { access_token, token_type, user: UserOut }
export const login = (email, password) =>
  USE_MOCK ? mockApi.login(email, password) : api.post("/auth/login", { email, password }).then((r) => r.data);

// Backend: POST /auth/signup { email, full_name, password, role } -> Token
export const signup = (payload) =>
  USE_MOCK ? mockApi.signup(payload) : api.post("/auth/signup", payload).then((r) => r.data);

export const getMe = () => (USE_MOCK ? mockApi.getMe() : api.get("/auth/me").then((r) => r.data));

// ---- Documents ----
// Backend returns a plain array, not { items }.
export const listDocuments = (params) =>
  USE_MOCK ? mockApi.listDocuments(params) : api.get("/documents", { params }).then((r) => r.data);

export const getDocument = (id) =>
  USE_MOCK ? mockApi.getDocument(id) : api.get(`/documents/${id}`).then((r) => r.data);

// Backend wraps the created document: { document, message }. Callers should read `.document`.
export const uploadDocument = (formData) =>
  USE_MOCK
    ? mockApi.uploadDocument(formData)
    : api
        .post("/documents/upload", formData, { headers: { "Content-Type": "multipart/form-data" } })
        .then((r) => r.data);

// Backend requires title + document_type + file, same as upload — not file alone.
// Also wraps the response the same way: { document, message }.
export const reviseDocument = (id, formData) =>
  USE_MOCK
    ? mockApi.reviseDocument(id, formData)
    : api
        .post(`/documents/${id}/revise`, formData, { headers: { "Content-Type": "multipart/form-data" } })
        .then((r) => r.data);

// Backend: { thread_id, total_versions, current_version, documents: [...] }
export const getDocumentThread = (id) =>
  USE_MOCK ? mockApi.getDocumentThread(id) : api.get(`/documents/${id}/thread`).then((r) => r.data);

// Backend: { document_id, masked_payload, pii_entities_masked_count, note }
export const getOutboundPayload = (id) =>
  USE_MOCK ? mockApi.getOutboundPayload(id) : api.get(`/documents/${id}/outbound-payload`).then((r) => r.data);

export const getDownloadUrl = (id) => (USE_MOCK ? "#" : `${BASE_URL}/documents/${id}/download`);

// Fetches the raw file bytes (with the JWT attached) for in-app preview rendering.
// Mock mode has no real underlying file, so this deliberately throws there —
// callers should catch it and fall back to showing extracted_text instead.
export const downloadDocumentBlob = (id) => {
  if (USE_MOCK) {
    return Promise.reject(new Error("No file bytes available in mock mode."));
  }
  return api.get(`/documents/${id}/download`, { responseType: "blob" }).then((r) => r.data);
};

// ---- Review / AI assist ----
// Backend: AIAnalysisOut — { id, document_id, summary, status: "completed"|"degraded", model_used,
// generated_at, flags: [...], precedent_matches: [...] }
export const getAssist = (id) =>
  USE_MOCK ? mockApi.getAssist(id) : api.get(`/documents/${id}/assist`).then((r) => r.data);

export const retryAssist = (id) =>
  USE_MOCK ? mockApi.retryAssist(id) : api.post(`/documents/${id}/assist/retry`).then((r) => r.data);

// Backend expects { status, comment } — status is one of approved/rejected/needs_revision.
// Returns the ReviewDecisionOut, not the document.
export const submitReview = (id, status, comment) =>
  USE_MOCK
    ? mockApi.submitReview(id, status, comment)
    : api.post(`/documents/${id}/review`, { status, comment }).then((r) => r.data);

// ---- Audit ----
// Backend returns a plain array of AuditEventOut, using `created_at`.
export const getAudit = (id, thread = false) =>
  USE_MOCK ? mockApi.getAudit(id, thread) : api.get(`/documents/${id}/audit`, { params: { thread } }).then((r) => r.data);

// ---- Notifications ----
// Backend: { unread_count, notifications: [...] }, each with `is_read`.
export const getNotifications = () =>
  USE_MOCK ? mockApi.getNotifications() : api.get("/notifications").then((r) => r.data);

export const markNotificationRead = (id) =>
  USE_MOCK ? mockApi.markNotificationRead(id) : api.post(`/notifications/${id}/read`).then((r) => r.data);

export const markAllNotificationsRead = () =>
  USE_MOCK ? mockApi.markAllNotificationsRead() : api.post("/notifications/read-all").then((r) => r.data);

// ---- Corpus ----
export const getRules = () => (USE_MOCK ? mockApi.getRules() : api.get("/corpus/rules").then((r) => r.data));

export const getPrecedents = () =>
  USE_MOCK ? mockApi.getPrecedents() : api.get("/corpus/precedents").then((r) => r.data);
