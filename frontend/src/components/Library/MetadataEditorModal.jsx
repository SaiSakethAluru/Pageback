import { useEffect, useState } from "react";

import * as api from "../../services/api";

export default function MetadataEditorModal({ book, isOpen, onClose, onSaved }) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isOpen || !book) {
      return;
    }
    setTitle(book.title || "");
    setAuthor(book.author || "");
    setError("");
  }, [book, isOpen]);

  if (!isOpen || !book) {
    return null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError("");
    try {
      const updated = await api.updateBookMetadata(book.id, { title, author });
      onSaved?.(book.id, updated);
      onClose?.();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={dialogStyle} onClick={(event) => event.stopPropagation()}>
        <div style={headerStyle}>
          <div>
            <p style={eyebrowStyle}>Edit Metadata</p>
            <h2 style={titleStyle}>Book details</h2>
            <p style={subtitleStyle}>Clean up missing or messy EPUB metadata before it shows in your library.</p>
          </div>
          <button type="button" onClick={onClose} style={closeButtonStyle} aria-label="Close edit metadata dialog">
            x
          </button>
        </div>

        <div style={contentStyle}>
          <div style={previewPanelStyle}>
            <div style={coverFrameStyle}>
              {book.cover_url ? (
                <img src={book.cover_url} alt="" style={coverImageStyle} />
              ) : (
                <div style={coverFallbackStyle}>
                  <span style={coverFallbackTextStyle}>{getInitials(title || book.title)}</span>
                </div>
              )}
            </div>
            <p style={helperLabelStyle}>Source</p>
            <p style={helperTextStyle}>
              Metadata currently lives on the book record in our `books` table.
            </p>
            <p style={helperLabelStyle}>TODO</p>
            <p style={helperTextStyle}>
              Add online metadata lookup similar to Calibre for auto-fill and cover matching.
            </p>
            <button type="button" disabled style={todoButtonStyle}>
              Fetch Metadata Online (TODO)
            </button>
          </div>

          <form style={formStyle} onSubmit={handleSubmit}>
            <label style={fieldStyle}>
              <span style={labelStyle}>Title</span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Book title"
                style={inputStyle}
              />
            </label>

            <label style={fieldStyle}>
              <span style={labelStyle}>Author</span>
              <input
                value={author}
                onChange={(event) => setAuthor(event.target.value)}
                placeholder="Author name"
                style={inputStyle}
              />
            </label>

            <div style={infoPanelStyle}>
              <p style={infoTitleStyle}>How this works today</p>
              <p style={infoBodyStyle}>
                On upload, we try to read title, author, and cover from the EPUB itself. When those fields are missing
                or wrong, this editor lets you override them for your library.
              </p>
            </div>

            {error ? <p style={errorStyle}>{error}</p> : null}

            <div style={actionsStyle}>
              <button type="button" onClick={onClose} style={secondaryButtonStyle}>
                Cancel
              </button>
              <button type="submit" disabled={isSaving} style={primaryButtonStyle}>
                {isSaving ? "Saving..." : "Save Metadata"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function getInitials(title) {
  const words = (title || "Book")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);
  return words.map((word) => word[0]?.toUpperCase() || "").join("") || "BK";
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
  width: "min(920px, 100%)",
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
  color: "#8b5e3c",
};

const titleStyle = {
  margin: "0.35rem 0 0",
  fontSize: "1.6rem",
  color: "#1f2930",
};

const subtitleStyle = {
  margin: "0.4rem 0 0",
  color: "#6a655e",
  maxWidth: 500,
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
  display: "grid",
  gridTemplateColumns: "260px minmax(0, 1fr)",
  gap: "1.5rem",
  padding: "1.5rem 1.75rem 1.75rem",
};

const previewPanelStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.75rem",
};

const coverFrameStyle = {
  aspectRatio: "3 / 4.35",
  borderRadius: 24,
  overflow: "hidden",
  background: "linear-gradient(160deg, #d4b181 0%, #8f5d3b 55%, #4a2d21 100%)",
  boxShadow: "0 18px 36px rgba(58, 37, 24, 0.2)",
};

const coverImageStyle = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
  display: "block",
};

const coverFallbackStyle = {
  width: "100%",
  height: "100%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "radial-gradient(circle at top, rgba(255,255,255,0.28), transparent 45%)",
};

const coverFallbackTextStyle = {
  fontSize: "3rem",
  fontWeight: 700,
  letterSpacing: "0.08em",
  color: "#fff8ee",
};

const helperLabelStyle = {
  margin: "0.15rem 0 0",
  fontSize: "0.75rem",
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  color: "#8b5e3c",
};

const helperTextStyle = {
  margin: 0,
  color: "#5f584f",
  lineHeight: 1.5,
};

const todoButtonStyle = {
  border: "1px dashed #cebca7",
  background: "#f5ede2",
  color: "#8d7864",
  borderRadius: 14,
  padding: "0.85rem 1rem",
  textAlign: "left",
};

const formStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
};

const fieldStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.45rem",
};

const labelStyle = {
  fontSize: "0.82rem",
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  color: "#756252",
};

const inputStyle = {
  border: "1px solid #d5c9ba",
  borderRadius: 16,
  padding: "0.95rem 1rem",
  background: "#fffdfa",
  color: "#1f2930",
  fontSize: "1rem",
};

const infoPanelStyle = {
  padding: "1rem 1.05rem",
  borderRadius: 18,
  background: "#fff8ef",
  border: "1px solid #eadcc8",
};

const infoTitleStyle = {
  margin: 0,
  fontWeight: 700,
  color: "#3c312a",
};

const infoBodyStyle = {
  margin: "0.45rem 0 0",
  color: "#655f57",
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

const primaryButtonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.8rem 1.05rem",
  background: "#193847",
  color: "#fff",
  fontWeight: 700,
};
