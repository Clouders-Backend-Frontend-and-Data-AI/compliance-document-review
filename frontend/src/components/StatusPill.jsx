const STYLES = {
  pending_review: "bg-amberBg text-amber",
  approved: "bg-approvedBg text-approved",
  rejected: "bg-rustBg text-rust",
  needs_revision: "bg-amberBg text-amber",
};

const LABELS = {
  pending_review: "Pending review",
  approved: "Approved",
  rejected: "Rejected",
  needs_revision: "Needs revision",
};

export default function StatusPill({ status }) {
  const style = STYLES[status] || "bg-hairline text-slate";
  const label = LABELS[status] || status;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-sm text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}
