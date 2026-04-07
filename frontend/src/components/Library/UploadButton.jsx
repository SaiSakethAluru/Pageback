import { useRef, useState } from "react";

import * as api from "../../services/api";

export default function UploadButton({
  onUploadComplete,
  children,
  renderTrigger,
  buttonStyle: buttonStyleOverride,
  containerStyle: containerStyleOverride,
  errorStyle: errorStyleOverride,
  ariaLabel = "Upload book",
}) {
  const inputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  function openFilePicker() {
    inputRef.current?.click();
  }

  async function handleChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setError("");
    setIsUploading(true);

    try {
      await api.uploadBook(file);
      await onUploadComplete?.();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  return (
    <div style={{ ...containerStyle, ...containerStyleOverride }}>
      <input
        ref={inputRef}
        type="file"
        accept=".epub"
        hidden
        onChange={handleChange}
      />
      {renderTrigger ? (
        renderTrigger({ openFilePicker, isUploading, error })
      ) : (
        <button
          type="button"
          aria-label={ariaLabel}
          onClick={openFilePicker}
          style={{ ...buttonStyle, ...buttonStyleOverride }}
        >
          {children || (isUploading ? "Uploading..." : "Upload Book")}
        </button>
      )}
      {error ? <p style={{ ...errorStyle, ...errorStyleOverride }}>{error}</p> : null}
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
  cursor: "pointer",
};

const errorStyle = {
  color: "#a11d1d",
  margin: "0.5rem 0 0",
  maxWidth: 320,
};
