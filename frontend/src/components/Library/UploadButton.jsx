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

      await onUploadComplete?.();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  return (
    <div style={containerStyle}>
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
      <p style={error ? errorStyle : errorPlaceholderStyle}>{error || "\u00A0"}</p>
    </div>
  );
  // TODO: add .pdf to accept attribute once PDF support is implemented
}

const containerStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
};

const buttonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.8rem 1.1rem",
  background: "#17313e",
  color: "#fff",
  fontWeight: 600,
};

const errorStyle = {
  color: "#a11d1d",
  margin: "0.5rem 0 0",
  maxWidth: 320,
};

// Keeps header actions aligned even when there's no error.
const errorPlaceholderStyle = {
  ...errorStyle,
  color: "transparent",
};
