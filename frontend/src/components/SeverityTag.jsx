const STYLES = {
  critical: "text-rust border-rust",
  high: "text-rust border-rust",
  medium: "text-amber border-amber",
  low: "text-slate border-hairline",
};

export default function SeverityTag({ severity }) {
  const style = STYLES[severity] || "text-slate border-hairline";
  return (
    <span
      className={`inline-block px-1.5 py-0.5 border rounded-sm text-[11px] font-medium tracking-wide ${style}`}
    >
      {severity}
    </span>
  );
}
