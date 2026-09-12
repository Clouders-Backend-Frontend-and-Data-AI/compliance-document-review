import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "../../api/client";
import StatusPill from "../../components/StatusPill";

export default function AdvisorHome() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["documents", "mine"],
    queryFn: () => listDocuments(),
  });

  const documents = data || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl">My submissions</h1>
        <Link
          to="/advisor/upload"
          className="bg-signal text-white text-sm px-4 py-2"
        >
          Submit a document
        </Link>
      </div>

      {isLoading && <p className="text-sm text-slate">Loading your submissions…</p>}

      {isError && (
        <p className="text-sm text-rust bg-rustBg px-3 py-2">
          Couldn't load your submissions. Try refreshing the page.
        </p>
      )}

      {!isLoading && !isError && documents.length === 0 && (
        <div className="border border-hairline bg-white px-6 py-10 text-center">
          <p className="text-ink mb-1">No submissions yet</p>
          <p className="text-sm text-slate mb-4">
            Submit a proposal, brochure, or client email for compliance review.
          </p>
          <Link to="/advisor/upload" className="text-signal underline underline-offset-2 text-sm">
            Submit your first document
          </Link>
        </div>
      )}

      {documents.length > 0 && (
        <table className="w-full text-sm bg-white border border-hairline">
          <thead>
            <tr className="border-b border-hairline text-left text-slate">
              <th className="px-4 py-3 font-medium">Title</th>
              <th className="px-4 py-3 font-medium">Version</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Submitted</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr
                key={doc.id}
                className="border-b border-hairline last:border-b-0 hover:bg-paper cursor-pointer"
              >
                <td className="px-4 py-3">
                  <Link to={`/advisor/documents/${doc.id}`} className="text-ink hover:text-signal">
                    {doc.title || doc.file_name || `Document ${doc.id}`}
                  </Link>
                </td>
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
