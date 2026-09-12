import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getDocument,
  getDocumentThread,
  getOutboundPayload,
  reviseDocument,
} from "../../api/client";
import StatusPill from "../../components/StatusPill";
import AuditTrail from "../../components/AuditTrail";
import DocumentPreview from "../../components/DocumentPreview";

export default function DocumentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showPayload, setShowPayload] = useState(false);
  const [file, setFile] = useState(null);
  const [reviseTitle, setReviseTitle] = useState("");
  const [error, setError] = useState(null);

  const { data: doc, isLoading } = useQuery({
    queryKey: ["document", id],
    queryFn: () => getDocument(id),
  });

  const { data: thread } = useQuery({
    queryKey: ["thread", id],
    queryFn: () => getDocumentThread(id),
  });

  const { data: payload } = useQuery({
    queryKey: ["outbound-payload", id],
    queryFn: () => getOutboundPayload(id),
    enabled: showPayload,
  });

  const revise = useMutation({
    mutationFn: (formData) => reviseDocument(id, formData),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["documents", "mine"] });
      navigate(`/advisor/documents/${result.document.id}`);
    },
    onError: (err) => setError(err.response?.data?.detail || "Couldn't submit the revision."),
  });

  function handleRevise(e) {
    e.preventDefault();
    if (!file) {
      setError("Choose a revised file first.");
      return;
    }
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", reviseTitle || doc.title);
    formData.append("document_type", doc.document_type);
    revise.mutate(formData);
  }

  if (isLoading) return <p className="text-sm text-slate">Loading document…</p>;
  if (!doc) return <p className="text-sm text-rust">Document not found.</p>;

  // The document detail includes the full decision history for this version;
  // the most recent one (if any) is what the advisor sees as the reviewer's comment.
  const decisions = doc.review_decisions || [];
  const latestDecision = decisions[decisions.length - 1];
  const threadDocs = thread?.documents || [];

  return (
    <div>
      <Link to="/advisor" className="text-sm text-slate underline underline-offset-2 mb-4 inline-block">
        ← Back to my submissions
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl mb-1">{doc.title || `Document ${doc.id}`}</h1>
          <p className="text-sm text-slate">v{doc.version_number || 1}</p>
        </div>
        <StatusPill status={doc.status} />
      </div>

      <div className="grid grid-cols-2 gap-6 items-start">
        <div className="space-y-6">
          <div className="border border-hairline bg-white p-5">
            <h3 className="text-sm font-medium text-ink mb-3">Document</h3>
            <DocumentPreview
              documentId={id}
              mimeType={doc.mime_type}
              fileName={doc.file_name}
              extractedText={doc.extracted_text}
            />
          </div>

          <div className="border border-hairline bg-white p-5">
            <h3 className="text-sm font-medium text-ink mb-2">Latest reviewer comment</h3>
            <p className="text-sm text-slate">
              {latestDecision?.comment ||
                "No comment recorded yet — this document hasn't been decided on."}
            </p>
          </div>

          {doc.status === "needs_revision" && (
            <form onSubmit={handleRevise} className="border border-hairline bg-white p-5 space-y-3">
              <h3 className="text-sm font-medium text-ink">Submit a revision</h3>
              <input
                type="text"
                placeholder={doc.title}
                value={reviseTitle}
                onChange={(e) => setReviseTitle(e.target.value)}
                className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
              />
              <input
                type="file"
                accept=".pdf,.docx,.xlsx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="text-sm"
              />
              {error && <p className="text-sm text-rust bg-rustBg px-3 py-2">{error}</p>}
              <button
                type="submit"
                disabled={revise.isPending}
                className="bg-signal text-white text-sm px-5 py-2.5 disabled:opacity-60"
              >
                {revise.isPending ? "Submitting…" : "Submit revision"}
              </button>
            </form>
          )}

          {threadDocs.length > 1 && (
            <div className="border border-hairline bg-white p-5">
              <h3 className="text-sm font-medium text-ink mb-3">Revision history</h3>
              <ul className="space-y-2">
                {threadDocs.map((t) => (
                  <li key={t.id} className="text-sm flex items-center justify-between">
                    <Link
                      to={`/advisor/documents/${t.id}`}
                      className={`hover:text-signal ${
                        String(t.id) === id ? "text-ink font-medium" : "text-slate"
                      }`}
                    >
                      v{t.version_number}
                    </Link>
                    <StatusPill status={t.status} />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="border border-hairline bg-white p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-ink">What the AI reviewer sees</h3>
              <button
                onClick={() => setShowPayload((s) => !s)}
                className="text-xs text-signal underline underline-offset-2"
              >
                {showPayload ? "Hide" : "Show"}
              </button>
            </div>
            <p className="text-sm text-slate mb-2">
              Client names, emails, phone numbers, and account details are replaced before
              anything leaves the app.
            </p>
            {showPayload && (
              <pre className="text-xs bg-paper p-3 whitespace-pre-wrap max-h-64 overflow-y-auto">
                {payload?.masked_payload || "Loading…"}
              </pre>
            )}
          </div>

          <AuditTrail documentId={id} />
        </div>
      </div>
    </div>
  );
}
