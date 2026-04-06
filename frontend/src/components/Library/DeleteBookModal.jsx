import { useEffect, useState } from "react";

import * as api from "../../services/api";

export default function DeleteBookModal({ book, isOpen, onClose, onDeleted }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    function handleEscape(event) {
      if (event.key === "Escape" && !isDeleting) {
        onClose?.();
      }
    }

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isDeleting, isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setError("");
    setIsDeleting(false);
  }, [book, isOpen]);

  if (!isOpen || !book) {
    return null;
  }

  const title = book.title || "Untitled book";

  async function handleDelete() {
    setIsDeleting(true);
    setError("");

    try {
      await api.deleteBook(book.id);
      onDeleted?.(book.id);
      onClose?.();
    } catch (deleteError) {
      setError(deleteError.message);
      setIsDeleting(false);
    }
  }

  return (
    <div style={backdropStyle} onClick={isDeleting ? undefined : onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-book-title"
        aria-describedby="delete-book-description"
        style={dialogStyle}
        onClick={(event) => event.stopPropagation()}
      >
        <div style={headerStyle}>
          <div>
            <p style={eyebrowStyle}>Delete Book</p>
            <h2 id="delete-book-title" style={titleStyle}>
              Remove &quot;{title}&quot;?
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            style={closeButtonStyle}
            aria-label="Close delete confirmation dialog"
          >
            x
          </button>
        </div>

        <div style={contentStyle}>
          <p id="delete-book-description" style={bodyStyle}>
            This will permanently remove the uploaded file, any AI indexing data, and the saved reading position for
            this book.
          </p>

          <div style={warningPanelStyle}>
            <p style={warningTitleStyle}>This action can&apos;t be undone.</p>
            <p style={warningBodyStyle}>
              If you still want the book later, you&apos;ll need to upload it again and rebuild its progress.
            </p>
          </div>

          {error ? <p style={errorStyle}>{error}</p> : null}

          <div style={actionsStyle}>
            <button type="button" onClick={onClose} disabled={isDeleting} style={secondaryButtonStyle}>
              Cancel
            </button>
            <button type="button" onClick={handleDelete} disabled={isDeleting} style={dangerButtonStyle}>
              {isDeleting ? "Deleting..." : "Delete Book"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const backdropStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(23, 28, 34, 0.52)",
  backdropFilter: "blur(8px)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "1.5rem",
  zIndex: 40,
};

const dialogStyle = {
  width: "min(520px, 100%)",
  borderRadius: 28,
  background: "#f6f1e8",
  boxShadow: "0 32px 90px rgba(20, 25, 31, 0.22)",
  border: "1px solid rgba(115, 98, 74, 0.16)",
  overflow: "hidden",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: "1rem",
  padding: "1.5rem 1.75rem 1rem",
  borderBottom: "1px solid rgba(115, 98, 74, 0.12)",
};

const eyebrowStyle = {
  margin: 0,
  fontSize: "0.8rem",
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  color: "#9c3028",
};

const titleStyle = {
  margin: "0.35rem 0 0",
  fontSize: "1.5rem",
  color: "#1f2930",
  textWrap: "balance",
};

const closeButtonStyle = {
  border: "1px solid rgba(115, 98, 74, 0.18)",
  background: "#fff9f2",
  color: "#4b4037",
  borderRadius: 999,
  width: 40,
  height: 40,
  fontSize: "1rem",
  flexShrink: 0,
};

const contentStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
  padding: "1.35rem 1.75rem 1.75rem",
};

const bodyStyle = {
  margin: 0,
  color: "#5f584f",
  lineHeight: 1.6,
};

const warningPanelStyle = {
  padding: "1rem 1.05rem",
  borderRadius: 18,
  background: "#fff2ef",
  border: "1px solid #efc7c1",
};

const warningTitleStyle = {
  margin: 0,
  fontWeight: 700,
  color: "#6d221d",
};

const warningBodyStyle = {
  margin: "0.45rem 0 0",
  color: "#7a4a45",
  lineHeight: 1.5,
};

const errorStyle = {
  margin: 0,
  color: "#a11d1d",
};

const actionsStyle = {
  display: "flex",
  justifyContent: "flex-end",
  gap: "0.75rem",
  marginTop: "0.25rem",
};

const secondaryButtonStyle = {
  border: "1px solid #d5c9ba",
  borderRadius: 999,
  padding: "0.8rem 1rem",
  background: "#fff8ef",
  color: "#3c312a",
  fontWeight: 600,
};

const dangerButtonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.8rem 1.05rem",
  background: "#8c241d",
  color: "#fff7f5",
  fontWeight: 700,
};
