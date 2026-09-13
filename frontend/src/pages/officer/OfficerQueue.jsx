import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "../../api/client";
import StatusPill from "../../components/StatusPill";

const FILTERS = [
  { value: "", label: "All" },
  { value: "pending_review", label: "Pending review" },
  { value: "needs_revision", label: "Needs revision" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

export default function OfficerQueue() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["documents", "queue", status],
    queryFn: () => listDocuments(status ? { status } : undefined),
  });

  const allDocuments = data || [];
  const query = search.trim().toLowerCase();
  const documents = query
    ? allDocuments.filter((doc) => (doc.title || "").toLowerCase().includes(query))
    : allDocuments;

  return (
    <div>
      <h1 className="text-2xl mb-6">Review queue</h1>

      <div className="flex items-center justify-between gap-4 mb-5">
        <div className="flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatus(f.value)}
              className={`text-sm px-3 py-1.5 border ${
                status === f.value
                  ? "border-signal text-signal bg-white"
                  : "border-hairline text-slate"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title…"
          className="w-56 border border-hairline px-3 py-1.5 text-sm bg-white focus:outline-none focus:border-signal"
        />
      </div>

      {isLoading && <p className="text-sm text-slate">Loading the queue…</p>}
      {isError && (
        <p className="text-sm text-rust bg-rustBg px-3 py-2">
          Couldn't load the queue. Try refreshing the page.
        </p>
      )}

      {!isLoading && !isError && documents.length === 0 && (
        <div className="border border-hairline bg-white px-6 py-10 text-center">
          <p className="text-ink mb-1">Nothing here</p>
          <p className="text-sm text-slate">
            {query
              ? `No documents match "${search}".`
              : "No documents match this filter right now."}
          </p>
        </div>
      )}

      {documents.length > 0 && (
        <table className="w-full text-sm bg-white border border-hairline">
          <thead>
            <tr className="border-b border-hairline text-left text-slate">
              <th className="px-4 py-3 font-medium">Title</th>
              <th className="px-4 py-3 font-medium">Advisor</th>
              <th className="px-4 py-3 font-medium">Version</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Submitted</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className="border-b border-hairline last:border-b-0 hover:bg-paper">
                <td className="px-4 py-3">
                  <Link to={`/officer/documents/${doc.id}`} className="text-ink hover:text-signal">
                    {doc.title || `Document ${doc.id}`}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate">{doc.advisor?.full_name || doc.advisor_id}</td>
                <td className="px-4 py-3 text-slate">v{doc.version_number || 1}</td>
                <td className="px-4 py-3">
                  <StatusPill status={doc.status} />
                </td>
                <td className="px-4 py-3 text-slate">
                  {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
