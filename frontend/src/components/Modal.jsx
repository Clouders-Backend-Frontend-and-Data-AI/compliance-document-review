export default function Modal({ title, onClose, children }) {
  return (
    <div
      className="fixed inset-0 bg-ink/40 flex items-center justify-center z-50 px-4"
      onClick={onClose}
    >
      <div
        className="bg-white border border-hairline max-w-lg w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-hairline sticky top-0 bg-white">
          <h3 className="text-sm font-medium text-ink">{title}</h3>
          <button
            onClick={onClose}
            className="text-slate hover:text-ink text-lg leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
