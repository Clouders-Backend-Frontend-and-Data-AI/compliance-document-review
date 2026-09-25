// A small in-memory mock of the backend, used when VITE_USE_MOCK=true.
// Field names mirror the real FastAPI schemas exactly, so this stays a faithful
// preview of the real API rather than a made-up shape.

const DELAY = 350;
const wait = (ms = DELAY) => new Promise((r) => setTimeout(r, ms));

const USERS = {
  "advisor@example.com": {
    id: "u_advisor_1",
    full_name: "Jordan Reyes",
    email: "advisor@example.com",
    role: "advisor",
    password: "Advisor123!",
    created_at: "2026-01-10T00:00:00Z",
  },
  "officer@example.com": {
    id: "u_officer_1",
    full_name: "Priya Nandakumar",
    email: "officer@example.com",
    role: "officer",
    password: "Officer123!",
    created_at: "2026-01-10T00:00:00Z",
  },
};

function publicUser(u) {
  const { password, ...rest } = u;
  return rest;
}

let documents = [
  {
    id: "1",
    title: "Henderson Retirement Strategy 2024",
    document_type: "proposal_letter",
    advisor_id: "u_advisor_1",
    advisor: publicUser(USERS["advisor@example.com"]),
    status: "pending_review",
    file_name: "henderson_proposal.docx",
    file_size: 48213,
    mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    thread_id: "t1",
    parent_document_id: null,
    version_number: 1,
    uploaded_at: "2026-09-02T14:20:00Z",
    updated_at: "2026-09-02T14:20:00Z",
    latest_decision: null,
    extracted_text:
      "Dear [CLIENT_1], based on our review of your portfolio [ACCOUNT_1], we recommend a rebalancing " +
      "toward fixed income given your stated retirement timeline. Past performance is not indicative " +
      "of future results...",
    review_decisions: [],
  },
  {
    id: "2",
    title: "Q3 Newsletter — Market Outlook",
    document_type: "marketing_email",
    advisor_id: "u_advisor_1",
    advisor: publicUser(USERS["advisor@example.com"]),
    status: "needs_revision",
    file_name: "q3_newsletter.pdf",
    file_size: 22190,
    mime_type: "application/pdf",
    thread_id: "t2",
    parent_document_id: null,
    version_number: 1,
    uploaded_at: "2026-08-28T09:05:00Z",
    updated_at: "2026-08-28T15:14:00Z",
    latest_decision: {
      id: "rd1",
      document_id: "2",
      officer_id: "u_officer_1",
      status: "needs_revision",
      comment: "Please include the standard SEC-MKT-02 registration disclosure before this goes out.",
      decided_at: "2026-08-28T15:14:00Z",
      officer: publicUser(USERS["officer@example.com"]),
    },
    extracted_text:
      "Markets are set to deliver guaranteed double-digit returns next quarter based on our proprietary " +
      "model. Contact us today to lock in these gains before the window closes...",
    review_decisions: [],
  },
  {
    id: "3",
    title: "Client Onboarding Brochure",
    document_type: "brochure",
    advisor_id: "u_advisor_1",
    advisor: publicUser(USERS["advisor@example.com"]),
    status: "approved",
    file_name: "onboarding_brochure.pdf",
    file_size: 91022,
    mime_type: "application/pdf",
    thread_id: "t3",
    parent_document_id: null,
    version_number: 1,
    uploaded_at: "2026-08-20T11:00:00Z",
    updated_at: "2026-08-21T10:00:00Z",
    latest_decision: {
      id: "rd2",
      document_id: "3",
      officer_id: "u_officer_1",
      status: "approved",
      comment: "Looks good — all disclosures present.",
      decided_at: "2026-08-21T10:00:00Z",
      officer: publicUser(USERS["officer@example.com"]),
    },
    extracted_text: "Welcome to our advisory practice. We tailor every plan to your goals...",
    review_decisions: [],
  },
];

documents.forEach((d) => {
  d.review_decisions = d.latest_decision ? [d.latest_decision] : [];
});

const assistByDoc = {
  1: {
    id: "ai1",
    document_id: "1",
    status: "completed",
    model_used: "gemini-1.5-flash",
    generated_at: "2026-09-02T14:20:40Z",
    summary:
      "A retirement rebalancing proposal for a masked client. Recommends shifting toward fixed " +
      "income. No prohibited claim language detected; one disclosure appears thin.",
    flags: [
      {
        id: "f1",
        analysis_id: "ai1",
        severity: "medium",
        matched_rule_id: "SEC-DISC-14",
        matched_rule_title: "Suitability Disclosure Requirement",
        matched_rule_text: null,
        passage_excerpt: "we recommend a rebalancing toward fixed income given your stated retirement timeline",
        explanation:
          "Personalized investment advice is referenced without a nearby suitability disclosure.",
        suggested_fix: "Add the standard suitability disclaimer immediately after this recommendation.",
      },
    ],
    precedent_matches: [
      { id: "p1", title: "Retirement Rebalancing Letter — March", document_type: "proposal_letter", masked_text_snippet: "...", decision: "approved", officer_comment: "Suitability disclosure present, cleared.", similarity_score: 0.86 },
      { id: "p2", title: "Fixed Income Shift Proposal", document_type: "proposal_letter", masked_text_snippet: "...", decision: "needs_revision", officer_comment: "Missing suitability disclaimer, sent back.", similarity_score: 0.79 },
      { id: "p3", title: "Client Rebalancing Notice", document_type: "proposal_letter", masked_text_snippet: "...", decision: "approved", officer_comment: "Standard language, no issues.", similarity_score: 0.74 },
    ],
  },
  2: {
    id: "ai2",
    document_id: "2",
    status: "completed",
    model_used: "gemini-1.5-flash",
    generated_at: "2026-08-28T09:05:30Z",
    summary:
      "A marketing email promising guaranteed returns. This is a high-severity issue — guaranteed " +
      "performance claims are a common source of regulatory action.",
    flags: [
      {
        id: "f2",
        analysis_id: "ai2",
        severity: "critical",
        matched_rule_id: "SEC-MKT-02",
        matched_rule_title: "Prohibited Guaranteed-Return Claims",
        matched_rule_text: null,
        passage_excerpt: "guaranteed double-digit returns next quarter based on our proprietary model",
        explanation:
          "Guaranteed-return language is prohibited under standard marketing rules. No investment " +
          "return can be guaranteed, and this claim carries no risk disclosure.",
        suggested_fix: "Remove the guarantee language and add a standard risk-of-loss disclosure.",
      },
      {
        id: "f3",
        analysis_id: "ai2",
        severity: "high",
        matched_rule_id: "SEC-MKT-02",
        matched_rule_title: "Prohibited Guaranteed-Return Claims",
        matched_rule_text: null,
        passage_excerpt: "Contact us today to lock in these gains before the window closes",
        explanation:
          "Urgency language paired with a guaranteed-return claim compounds the compliance risk.",
        suggested_fix: "Remove the urgency framing tied to the unverified return claim.",
      },
    ],
    precedent_matches: [
      { id: "p4", title: "Spring Market Update Email", document_type: "marketing_email", masked_text_snippet: "...", decision: "rejected", officer_comment: "Guaranteed-return language, rejected outright.", similarity_score: 0.91 },
      { id: "p5", title: "Quarterly Outlook Newsletter", document_type: "marketing_email", masked_text_snippet: "...", decision: "needs_revision", officer_comment: "Toned down claims, sent back for softer language.", similarity_score: 0.83 },
      { id: "p6", title: "Market Commentary Draft", document_type: "marketing_email", masked_text_snippet: "...", decision: "approved", officer_comment: "Hedged language, no guarantees made.", similarity_score: 0.68 },
    ],
  },
  3: {
    id: "ai3",
    document_id: "3",
    status: "completed",
    model_used: "gemini-1.5-flash",
    generated_at: "2026-08-20T11:05:00Z",
    summary: "A general onboarding brochure. No performance claims, no missing disclosures detected.",
    flags: [],
    precedent_matches: [
      { id: "p7", title: "New Client Welcome Packet", document_type: "brochure", masked_text_snippet: "...", decision: "approved", officer_comment: "Standard onboarding content.", similarity_score: 0.72 },
    ],
  },
};

let auditByDoc = {
  1: [
    { id: "a1", document_id: "1", actor_id: "u_advisor_1", actor_name: "Jordan Reyes", actor_role: "advisor", action: "submitted", details: null, created_at: "2026-09-02T14:20:00Z" },
    { id: "a2", document_id: "1", actor_id: null, actor_name: "System", actor_role: null, action: "analysis_generated", details: null, created_at: "2026-09-02T14:20:40Z" },
  ],
  2: [
    { id: "a3", document_id: "2", actor_id: "u_advisor_1", actor_name: "Jordan Reyes", actor_role: "advisor", action: "submitted", details: null, created_at: "2026-08-28T09:05:00Z" },
    { id: "a4", document_id: "2", actor_id: null, actor_name: "System", actor_role: null, action: "analysis_generated", details: null, created_at: "2026-08-28T09:05:30Z" },
    { id: "a5", document_id: "2", actor_id: "u_officer_1", actor_name: "Priya Nandakumar", actor_role: "officer", action: "viewed", details: null, created_at: "2026-08-28T15:10:00Z" },
    { id: "a6", document_id: "2", actor_id: "u_officer_1", actor_name: "Priya Nandakumar", actor_role: "officer", action: "decided", details: null, created_at: "2026-08-28T15:14:00Z" },
  ],
  3: [
    { id: "a7", document_id: "3", actor_id: "u_advisor_1", actor_name: "Jordan Reyes", actor_role: "advisor", action: "submitted", details: null, created_at: "2026-08-20T11:00:00Z" },
    { id: "a8", document_id: "3", actor_id: "u_officer_1", actor_name: "Priya Nandakumar", actor_role: "officer", action: "decided", details: null, created_at: "2026-08-21T10:00:00Z" },
  ],
};

let notifications = [
  { id: "n1", user_id: "u_advisor_1", document_id: "2", title: "Revision requested", message: "Your Q3 Newsletter was sent back — needs revision.", is_read: false, created_at: "2026-08-28T15:14:00Z" },
  { id: "n2", user_id: "u_advisor_1", document_id: "3", title: "Document approved", message: "Your Client Onboarding Brochure was approved.", is_read: true, created_at: "2026-08-21T10:00:00Z" },
];

let nextDocId = 4;
let currentUser = null;

export const mockApi = {
  async login(email, password) {
    await wait();
    const user = USERS[email];
    if (!user || user.password !== password) {
      const err = new Error("Invalid credentials");
      err.response = { data: { detail: "Incorrect email or password." } };
      throw err;
    }
    currentUser = user;
    return { access_token: "mock-token", token_type: "bearer", user: publicUser(user) };
  },

  async signup(payload) {
    await wait();
    const user = { id: `u_${Date.now()}`, created_at: new Date().toISOString(), ...payload };
    currentUser = user;
    return { access_token: "mock-token", token_type: "bearer", user: publicUser(user) };
  },

  async getMe() {
    await wait();
    return currentUser ? publicUser(currentUser) : null;
  },

  async listDocuments(params) {
    await wait();
    let list = documents;
    if (params?.status) list = list.filter((d) => d.status === params.status);
    return list;
  },

  async getDocument(id) {
    await wait();
    return documents.find((d) => String(d.id) === String(id));
  },

  async uploadDocument(formData) {
    await wait(600);
    const doc = {
      id: String(nextDocId++),
      title: formData.get("title"),
      document_type: formData.get("document_type"),
      advisor_id: currentUser?.id || "u_advisor_1",
      advisor: publicUser(currentUser || USERS["advisor@example.com"]),
      status: "pending_review",
      file_name: formData.get("file")?.name || "document",
      file_size: formData.get("file")?.size || 0,
      mime_type: formData.get("file")?.type || "application/octet-stream",
      thread_id: `t${nextDocId}`,
      parent_document_id: null,
      version_number: 1,
      uploaded_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      latest_decision: null,
      extracted_text: "(Mock) Extracted text would appear here once the backend parses the file.",
      review_decisions: [],
    };
    documents = [doc, ...documents];
    auditByDoc[doc.id] = [
      { id: `a_${doc.id}_1`, document_id: doc.id, actor_id: doc.advisor_id, actor_name: doc.advisor.full_name, actor_role: "advisor", action: "submitted", details: null, created_at: doc.uploaded_at },
    ];
    assistByDoc[doc.id] = {
      id: `ai_${doc.id}`,
      document_id: doc.id,
      status: "completed",
      model_used: "mock",
      generated_at: doc.uploaded_at,
      summary: "(Mock) No AI backend connected — this is placeholder analysis for demo purposes.",
      flags: [],
      precedent_matches: [],
    };
    return { document: doc, message: "Document successfully uploaded and queued for review" };
  },

  async reviseDocument(id, formData) {
    await wait(600);
    const original = documents.find((d) => String(d.id) === String(id));
    const doc = {
      ...original,
      id: String(nextDocId++),
      title: formData.get("title") || original.title,
      version_number: (original.version_number || 1) + 1,
      status: "pending_review",
      uploaded_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      latest_decision: null,
      review_decisions: [],
      parent_document_id: original.id,
    };
    documents = [doc, ...documents];
    return { document: doc, message: `Revision (v${doc.version_number}) successfully submitted and queued for review` };
  },

  async getDocumentThread(id) {
    await wait();
    const doc = documents.find((d) => String(d.id) === String(id));
    if (!doc) return { thread_id: null, total_versions: 0, current_version: 0, documents: [] };
    const threadDocs = documents
      .filter((d) => d.thread_id === doc.thread_id)
      .sort((a, b) => (a.version_number || 1) - (b.version_number || 1));
    const list = threadDocs.length ? threadDocs : [doc];
    return {
      thread_id: doc.thread_id,
      total_versions: list.length,
      current_version: Math.max(...list.map((d) => d.version_number || 1)),
      documents: list,
    };
  },

  async getOutboundPayload(id) {
    await wait();
    const doc = documents.find((d) => String(d.id) === String(id));
    return {
      document_id: id,
      masked_payload: doc?.extracted_text || "",
      pii_entities_masked_count: 3,
      note: "This shows the exact server-side masked payload dispatched to external LLM / embedding endpoints. Zero original PII leaves the app perimeter.",
    };
  },

  async getAssist(id) {
    await wait(700);
    return assistByDoc[id] || { id: null, document_id: id, status: "degraded", model_used: null, generated_at: null, summary: "", flags: [], precedent_matches: [] };
  },

  async retryAssist(id) {
    await wait(700);
    return assistByDoc[id] || { id: null, document_id: id, status: "completed", model_used: "mock", generated_at: new Date().toISOString(), summary: "(Mock) Re-run analysis.", flags: [], precedent_matches: [] };
  },

  async submitReview(id, status, comment) {
    await wait(500);
    const decidedAt = new Date().toISOString();
    const decision = {
      id: `rd_${Date.now()}`,
      document_id: id,
      officer_id: currentUser?.id || "u_officer_1",
      status,
      comment,
      decided_at: decidedAt,
      officer: publicUser(currentUser || USERS["officer@example.com"]),
    };
    documents = documents.map((d) =>
      String(d.id) === String(id)
        ? { ...d, status, latest_decision: decision, review_decisions: [...(d.review_decisions || []), decision], updated_at: decidedAt }
        : d
    );
    auditByDoc[id] = [
      ...(auditByDoc[id] || []),
      { id: `a_${id}_${Date.now()}`, document_id: id, actor_id: decision.officer_id, actor_name: decision.officer.full_name, actor_role: "officer", action: "decided", details: null, created_at: decidedAt },
    ];
    notifications = [
      {
        id: `n_${Date.now()}`,
        user_id: "u_advisor_1",
        document_id: id,
        title: status === "approved" ? "Document approved" : status === "rejected" ? "Document rejected" : "Revision requested",
        message: `Your document was ${status.replace("_", " ")}.`,
        is_read: false,
        created_at: decidedAt,
      },
      ...notifications,
    ];
    return decision;
  },

  async getAudit(id) {
    await wait();
    return auditByDoc[id] || [];
  },

  async getNotifications() {
    await wait();
    return { unread_count: notifications.filter((n) => !n.is_read).length, notifications };
  },

  async markNotificationRead(id) {
    await wait(150);
    notifications = notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n));
    return notifications.find((n) => n.id === id);
  },

  async markAllNotificationsRead() {
    await wait(150);
    const count = notifications.filter((n) => !n.is_read).length;
    notifications = notifications.map((n) => ({ ...n, is_read: true }));
    return { message: `Marked ${count} notifications as read` };
  },

  async getRules() {
    await wait();
    return [];
  },

  async getPrecedents() {
    await wait();
    // Mirrors PrecedentOut from /corpus/precedents — full masked_text, and a
    // source_document_id only where the precedent actually traces back to a
    // real reviewed document (most seeded precedents won't have one).
    return [
      {
        id: "p1",
        title: "Retirement Rebalancing Letter — March",
        document_type: "proposal_letter",
        masked_text:
          "Dear [CLIENT_1], following our quarterly review of [ACCOUNT_1], we recommend " +
          "rebalancing toward fixed income given your stated retirement horizon. This " +
          "recommendation is suitable given your risk tolerance and investment objectives " +
          "as documented in your account file. Past performance is not indicative of future results.",
        decision: "approved",
        officer_comment: "Suitability disclosure present, cleared.",
        source_document_id: null,
        created_at: "2026-03-14T10:00:00Z",
      },
      {
        id: "p4",
        title: "Spring Market Update Email",
        document_type: "marketing_email",
        masked_text:
          "Markets are poised for exceptional gains this quarter based on our analysis. " +
          "Don't miss this opportunity — act now to maximize your returns.",
        decision: "rejected",
        officer_comment: "Guaranteed-return language, rejected outright.",
        source_document_id: "3",
        created_at: "2026-04-02T09:00:00Z",
      },
    ];
  },
};
