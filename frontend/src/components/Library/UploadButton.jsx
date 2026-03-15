import { useRef, useState } from "react";

import * as api from "../../services/api";

export default function UploadButton({ onUploadComplete }) {
  const inputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  async function handleChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setError("");
    setIsUploading(true);

    try {
      const upload = await api.uploadBook(file);

      let status = upload.status;
      while (status === "pending" || status === "processing") {
        await new Promise((resolve) => window.setTimeout(resolve, 3000));
        const next = await api.getBookStatus(upload.book_id);
        status = next.status;
      }

      if (status === "failed") {
        throw new Error("Ingestion failed");
      }

      await onUploadComplete?.();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".epub"
        hidden
        onChange={handleChange}
      />
      <button type="button" onClick={() => inputRef.current?.click()} style={buttonStyle}>
        {isUploading ? "Uploading..." : "Upload Book"}
      </button>
      {error ? <p style={{ color: "#a11d1d", marginTop: "0.5rem" }}>{error}</p> : null}
    </div>
  );
  // TODO: add .pdf to accept attribute once PDF support is implemented
}

const buttonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.8rem 1.1rem",
  background: "#17313e",
  color: "#fff",
  fontWeight: 600,
};
