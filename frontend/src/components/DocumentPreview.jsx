import { useEffect, useRef, useState } from "react";
import { downloadDocumentBlob, getDownloadUrl } from "../api/client";

function isPdf(mimeType, fileName) {
  return mimeType?.includes("pdf") || fileName?.toLowerCase().endsWith(".pdf");
}
function isWord(mimeType, fileName) {
  return (
    mimeType?.includes("wordprocessingml") ||
    mimeType?.includes("msword") ||
    fileName?.toLowerCase().endsWith(".docx")
  );
}
function isExcel(mimeType, fileName) {
  return (
    mimeType?.includes("spreadsheetml") ||
    mimeType?.includes("ms-excel") ||
    fileName?.toLowerCase().endsWith(".xlsx")
  );
}

export default function DocumentPreview({ documentId, mimeType, fileName, extractedText }) {
  const [state, setState] = useState({ status: "loading" }); // loading | pdf | html | unsupported
  const objectUrlRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: "loading" });

      let blob;
      try {
        blob = await downloadDocumentBlob(documentId);
      } catch {
        // No real file bytes available (mock mode, or a fetch failure) —
        // fall back to whatever extracted text the document record has.
        if (!cancelled) setState({ status: "unsupported" });
        return;
      }

      if (cancelled) return;

      if (isPdf(mimeType, fileName)) {
        const url = URL.createObjectURL(blob);
        objectUrlRef.current = url;
        setState({ status: "pdf", url });
        return;
      }

      if (isWord(mimeType, fileName)) {
        try {
          const mammoth = await import("mammoth");
          const arrayBuffer = await blob.arrayBuffer();
          const result = await mammoth.convertToHtml({ arrayBuffer });
          if (!cancelled) setState({ status: "html", html: result.value });
        } catch {
          if (!cancelled) setState({ status: "unsupported" });
        }
        return;
      }

      if (isExcel(mimeType, fileName)) {
        try {
          const XLSX = await import("xlsx");
          const arrayBuffer = await blob.arrayBuffer();
          const workbook = XLSX.read(arrayBuffer, { type: "array" });
          const firstSheetName = workbook.SheetNames[0];
          const html = XLSX.utils.sheet_to_html(workbook.Sheets[firstSheetName]);
          if (!cancelled) setState({ status: "html", html });
        } catch {
          if (!cancelled) setState({ status: "unsupported" });
        }
        return;
      }

      // Unrecognized file type — fall back to extracted text.
      if (!cancelled) setState({ status: "unsupported" });
    }

    load();

    return () => {
      cancelled = true;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId, mimeType, fileName]);

  return (
    <div>
      {state.status === "loading" && (
        <p className="text-sm text-slate py-8 text-center">Loading document preview…</p>
      )}

      {state.status === "pdf" && (
        <iframe
          title={fileName || "Document preview"}
          src={state.url}
          className="w-full h-[520px] border border-hairline"
        />
      )}

      {state.status === "html" && (
        <div
          className="text-sm text-ink leading-relaxed max-h-[520px] overflow-y-auto border border-hairline p-4 bg-white [&_p]:mb-3 [&_h1]:text-lg [&_h1]:font-serif [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-serif [&_h2]:mb-2 [&_table]:text-xs [&_table]:border-collapse [&_td]:border [&_td]:border-hairline [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:border-hairline [&_th]:px-2 [&_th]:py-1 [&_th]:bg-paper"
          dangerouslySetInnerHTML={{ __html: state.html }}
        />
      )}

      {state.status === "unsupported" && (
        <p className="text-sm text-slate whitespace-pre-line leading-relaxed max-h-96 overflow-y-auto">
          {extractedText || "Preview not available for this file — download to view the original."}
        </p>
      )}

      <a
        href={getDownloadUrl(documentId)}
        className="text-sm text-signal underline underline-offset-2 mt-3 inline-block"
      >
        Download original file
      </a>
    </div>
  );
}
