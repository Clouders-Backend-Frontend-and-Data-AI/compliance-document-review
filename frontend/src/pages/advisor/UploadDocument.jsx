import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadDocument } from "../../api/client";
import { getErrorMessage } from "../../api/errorMessage";

const MAX_SIZE_MB = 10;
const ACCEPTED = [".pdf", ".docx", ".xlsx"];

const DOCUMENT_TYPES = [
  { value: "proposal_letter", label: "Proposal letter" },
  { value: "marketing_email", label: "Marketing email" },
  { value: "brochure", label: "Brochure" },
  { value: "social_post", label: "Social post" },
  { value: "meeting_notes", label: "Meeting notes" },
];

export default function UploadDocument() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0].value);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function handleFileChange(e) {
    const f = e.target.files?.[0];
    setError(null);
    if (!f) return;

    const ext = "." + f.name.split(".").pop().toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported file type. Use ${ACCEPTED.join(", ")}.`);
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File is over the ${MAX_SIZE_MB}MB limit.`);
      return;
    }
    setFile(f);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setError("Choose a file to submit.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title || file.name);
      formData.append("document_type", documentType);
      const result = await uploadDocument(formData);
      navigate(`/advisor/documents/${result.document.id}`);
    } catch (err) {
      setError(getErrorMessage(err, "Upload failed. Try again."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl mb-1">Submit a document</h1>
      <p className="text-sm text-slate mb-8">
        PDF, DOCX, or XLSX, up to {MAX_SIZE_MB}MB. A compliance officer will review it and
        you'll see the decision on your submissions page.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm text-ink mb-1" htmlFor="title">
            Title
          </label>
          <input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Henderson Retirement Strategy 2024"
            className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
          />
        </div>

        <div>
          <label className="block text-sm text-ink mb-1" htmlFor="documentType">
            Document type
          </label>
          <select
            id="documentType"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-ink mb-1">File</label>
          <div className="border border-dashed border-hairline bg-white px-4 py-8 text-center">
            <input
              type="file"
              accept={ACCEPTED.join(",")}
              onChange={handleFileChange}
              className="text-sm"
            />
            {file && (
              <p className="text-sm text-slate mt-3">
                {file.name} · {(file.size / (1024 * 1024)).toFixed(2)}MB
              </p>
            )}
          </div>
        </div>

        {error && <p className="text-sm text-rust bg-rustBg px-3 py-2">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="bg-signal text-white text-sm px-5 py-2.5 disabled:opacity-60"
        >
          {submitting ? "Submitting…" : "Submit for review"}
        </button>
      </form>
    </div>
  );
}
