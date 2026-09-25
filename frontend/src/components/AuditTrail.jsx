import { useQuery } from "@tanstack/react-query";
import { getAudit } from "../api/client";

const ACTION_LABELS = {
  submitted: "submitted the document",
  viewed: "viewed the document",
  analysis_generated: "AI analysis generated",
  decided: "recorded a decision",
  resubmitted: "resubmitted a revision",
  downloaded: "downloaded the file",
};

export default function AuditTrail({ documentId, thread = false }) {
  const { data, isLoading } = useQuery({
    queryKey: ["audit", documentId, thread],
    queryFn: () => getAudit(documentId, thread),
  });

  const events = data || [];

  return (
    <div className="border border-hairline bg-white p-5">
      <h3 className="text-sm font-medium text-ink mb-3">Audit trail</h3>
      {isLoading && <p className="text-sm text-slate">Loading…</p>}
      {!isLoading && events.length === 0 && (
        <p className="text-sm text-slate">No recorded events yet.</p>
      )}
      <ul className="space-y-2">
        {events.map((e) => (
          <li key={e.id} className="text-sm flex items-baseline justify-between gap-3">
            <span className="text-ink">
              <span className="text-slate">{e.actor_name || e.actor_id}</span>{" "}
              {ACTION_LABELS[e.action] || e.action}
            </span>
            <span className="text-xs text-slate whitespace-nowrap">
              {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
