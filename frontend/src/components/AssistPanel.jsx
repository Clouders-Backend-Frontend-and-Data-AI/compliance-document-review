import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAssist, retryAssist } from "../api/client";
import SeverityTag from "./SeverityTag";

export default function AssistPanel({ documentId }) {
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["assist", documentId],
    queryFn: () => getAssist(documentId),
    retry: false,
  });

  const retry = useMutation({
    mutationFn: () => retryAssist(documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["assist", documentId] }),
  });

  if (isLoading) {
    return (
      <div className="border border-hairline bg-white p-5">
        <p className="text-sm text-slate">Reading the document and checking it against the rule corpus…</p>
      </div>
    );
  }

  const flags = data?.flags || [];
  const precedents = data?.precedent_matches || [];
  const isDegraded = data?.status === "degraded";
  // A hard failure means the request itself errored, the backend reports a genuine
  // error status, or there's simply no data at all — as opposed to "degraded", which
  // still comes with real fallback-engine content worth showing.
  const isHardFailure =
    isError || !data || data?.status === "error" || data?.status === "failed";

  if (isHardFailure) {
    return (
      <div className="border border-hairline bg-white p-5">
        <h3 className="text-sm font-medium text-ink mb-1">AI assist unavailable</h3>
        <p className="text-sm text-slate mb-4">
          The compliance assist couldn't run for this document. You can still read the
          document and record a decision — the assist just isn't there to help this time.
        </p>
        <button
          onClick={() => retry.mutate()}
          disabled={retry.isPending}
          className="text-sm text-signal underline underline-offset-2 disabled:opacity-60"
        >
          {retry.isPending ? "Retrying…" : "Retry analysis"}
        </button>
      </div>
    );
  }

  return (
    <div className="border border-hairline bg-white divide-y divide-hairline">
      {isDegraded && (
        <div className="px-5 py-2.5 bg-amberBg text-amber text-xs flex items-center justify-between">
          <span>Running in degraded mode — no AI key configured, using the local fallback engine.</span>
          <button
            onClick={() => retry.mutate()}
            disabled={retry.isPending}
            className="underline underline-offset-2 shrink-0 ml-3"
          >
            {retry.isPending ? "Retrying…" : "Retry"}
          </button>
        </div>
      )}

      <div className="p-5">
        <h3 className="text-sm font-medium text-ink mb-2">Summary</h3>
        <p className="text-sm text-slate leading-relaxed">
          {data?.summary || "No summary available."}
        </p>
      </div>

      <div className="p-5">
        <h3 className="text-sm font-medium text-ink mb-3">
          Flags {flags.length > 0 && <span className="text-slate">({flags.length})</span>}
        </h3>
        {flags.length === 0 && (
          <p className="text-sm text-slate">No compliance issues flagged.</p>
        )}
        <ul className="space-y-4">
          {flags.map((flag) => (
            <li key={flag.id} className="border-l-2 border-hairline pl-3">
              <div className="flex items-center gap-2 mb-1">
                <SeverityTag severity={flag.severity} />
                {flag.matched_rule_id && (
                  <span className="text-xs text-slate">Rule {flag.matched_rule_id}</span>
                )}
              </div>
              <p className="text-sm text-ink italic mb-1">"{flag.passage_excerpt}"</p>
              <p className="text-sm text-slate">{flag.explanation}</p>
              {flag.suggested_fix && (
                <p className="text-sm text-slate mt-1">
                  <span className="text-ink">Suggested fix:</span> {flag.suggested_fix}
                </p>
              )}
            </li>
          ))}
        </ul>
      </div>

      {precedents.length > 0 && (
        <div className="p-5">
          <h3 className="text-sm font-medium text-ink mb-3">Similar past decisions</h3>
          <ul className="space-y-3">
            {precedents.map((p) => (
              <li key={p.id} className="text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-ink">{p.title || `Document ${p.id}`}</span>
                  <span className="text-xs text-slate capitalize">{p.decision}</span>
                </div>
                {p.officer_comment && <p className="text-slate mt-0.5">{p.officer_comment}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="px-5 py-3">
        <button
          onClick={() => retry.mutate()}
          disabled={retry.isPending}
          className="text-xs text-slate underline underline-offset-2 disabled:opacity-60"
        >
          {retry.isPending ? "Re-running…" : "Re-run analysis"}
        </button>
      </div>
    </div>
  );
}
