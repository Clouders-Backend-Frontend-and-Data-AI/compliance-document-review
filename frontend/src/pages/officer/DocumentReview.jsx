import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDocument, submitReview } from "../../api/client";
import StatusPill from "../../components/StatusPill";
import AssistPanel from "../../components/AssistPanel";
import AuditTrail from "../../components/AuditTrail";
import DocumentPreview from "../../components/DocumentPreview";
import { getErrorMessage } from "../../api/errorMessage";

const DECISIONS = [
  { value: "approved", label: "Approve" },
  { value: "needs_revision", label: "Send back for revision" },
  { value: "rejected", label: "Reject" },
];

export default function DocumentReview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [decision, setDecision] = useState("approved");
  const [comment, setComment] = useState("");
  const [error, setError] = useState(null);

  const { data: doc, isLoading } = useQuery({
    queryKey: ["document", id],
    queryFn: () => getDocument(id),
  });

  const review = useMutation({
    mutationFn: () => submitReview(id, decision, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document", id] });
      queryClient.invalidateQueries({ queryKey: ["documents", "queue"] });
      navigate("/officer");
    },
    onError: (err) => {
      setError(getErrorMessage(err, "Couldn't record the decision. Try again."));
    },
  });

  function handleSubmit(e) {
    e.preventDefault();
    if (!comment.trim() || comment.trim().length < 3) {
      setError("Add a comment (at least 3 characters) explaining the decision.");
      return;
    }
    setError(null);
    review.mutate();
  }

  if (isLoading) return <p className="text-sm text-slate">Loading document…</p>;
  if (!doc) return <p className="text-sm text-rust">Document not found.</p>;

  return (
    <div>
      <Link to="/officer" className="text-sm text-slate underline underline-offset-2 mb-4 inline-block">
        ← Back to queue
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl mb-1">{doc.title || `Document ${doc.id}`}</h1>
          <p className="text-sm text-slate">
            Submitted by {doc.advisor?.full_name || doc.advisor_id} · v{doc.version_number || 1}
          </p>
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

          <form onSubmit={handleSubmit} className="border border-hairline bg-white p-5 space-y-4">
            <h3 className="text-sm font-medium text-ink">Record your decision</h3>
            <div className="grid grid-cols-3 gap-2">
              {DECISIONS.map((d) => (
                <button
                  type="button"
                  key={d.value}
                  onClick={() => setDecision(d.value)}
                  className={`text-sm px-3 py-2 border ${
                    decision === d.value
                      ? "border-signal text-signal bg-paper"
                      : "border-hairline text-slate"
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
            <div>
              <label className="block text-sm text-ink mb-1" htmlFor="comment">
                Comment
              </label>
              <textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={4}
                placeholder="Explain the decision — this is what the advisor will see."
                className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
              />
            </div>
            {error && <p className="text-sm text-rust bg-rustBg px-3 py-2">{error}</p>}
            <button
              type="submit"
              disabled={review.isPending}
              className="bg-signal text-white text-sm px-5 py-2.5 disabled:opacity-60"
            >
              {review.isPending ? "Recording…" : "Submit decision"}
            </button>
          </form>
        </div>

        <div className="space-y-6">
          <AssistPanel documentId={id} />
          <AuditTrail documentId={id} thread />
        </div>
      </div>
    </div>
  );
}
