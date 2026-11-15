import { useEffect, useRef, useState } from "react";
import * as api from "../../services/api";

export default function MetadataEditorModal({ book, isOpen, onClose, onSaved }) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [coverUrl, setCoverUrl] = useState("");
  const [newCoverFile, setNewCoverFile] = useState(null);
  const [pendingOnlineCoverUrl, setPendingOnlineCoverUrl] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  // Online metadata fetch state
  const [isFetchingOnline, setIsFetchingOnline] = useState(false);
  const [onlineResults, setOnlineResults] = useState([]);
  const [onlineSearchOpen, setOnlineSearchOpen] = useState(false);
  const [onlineSearchMessage, setOnlineSearchMessage] = useState("");

  const fileInputRef = useRef(null);
  const previewUrlRef = useRef(null);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    function handleEscape(e) {
      if (e.key === "Escape" && !isSaving) {
        onClose?.();
      }
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, isSaving, onClose]);

  useEffect(() => {
    if (!isOpen || !book) {
      return;
    }
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    setTitle(book.title || "");
    setAuthor(book.author || "");
    setCoverUrl(book.cover_url || "");
    setNewCoverFile(null);
    setPendingOnlineCoverUrl(null);
    setError("");
    setOnlineResults([]);
    setOnlineSearchOpen(false);
    setOnlineSearchMessage("");
  }, [book, isOpen]);

  if (!isOpen || !book) {
    return null;
  }

  function handleFileSelected(event) {
    const file = event.target.files?.[0];
    if (file) {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
      setNewCoverFile(file);
      setPendingOnlineCoverUrl(null);
      const preview = URL.createObjectURL(file);
      previewUrlRef.current = preview;
      setCoverUrl(preview);
    }
  }

  async function handleFetchOnline() {
    const searchTitle = title.trim() || book.title || "";
    if (!searchTitle) {
      setError("Please enter a title before fetching metadata.");
      return;
    }

    setIsFetchingOnline(true);
    setOnlineSearchMessage("");
    setError("");
    setOnlineSearchOpen(true);

    try {
      const results = await api.fetchOnlineBookMetadata(searchTitle, author.trim());
      if (results.length === 0) {
        setOnlineSearchMessage("No matching books found online.");
        setOnlineResults([]);
      } else {
        setOnlineResults(results);
        setOnlineSearchMessage(`Found ${results.length} match${results.length > 1 ? "es" : ""}:`);
      }
    } catch (err) {
      setOnlineSearchMessage("Failed to search OpenLibrary: " + (err.message || "Network error"));
      setOnlineResults([]);
    } finally {
      setIsFetchingOnline(false);
    }
  }

  function handleApplyMatch(match) {
    if (match.title) setTitle(match.title);
    if (match.author) setAuthor(match.author);
    if (match.coverUrl) {
      setCoverUrl(match.coverUrl);
      setPendingOnlineCoverUrl(match.coverUrl);
      setNewCoverFile(null);
    }
    setOnlineSearchOpen(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError("");

    try {
      const updatedMeta = await api.updateBookMetadata(book.id, { title, author });
      let finalCoverUrl = book.cover_url;

      if (newCoverFile) {
        const coverRes = await api.uploadBookCover(book.id, newCoverFile);
        finalCoverUrl = coverRes.cover_url;
      } else if (pendingOnlineCoverUrl) {
        const coverRes = await api.updateBookCoverFromUrl(book.id, pendingOnlineCoverUrl);
        finalCoverUrl = coverRes.cover_url;
      }

      onSaved?.(book.id, {
        ...updatedMeta,
        cover_url: finalCoverUrl,
      });
      onClose?.();
    } catch (saveError) {
      setError(saveError.message || "Failed to save metadata.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={dialogStyle} onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
        <div style={headerStyle}>
          <div>
            <p style={eyebrowStyle}>Edit Metadata & Cover</p>
            <h2 style={titleStyle}>Book details</h2>
            <p style={subtitleStyle}>
              Calibre-style metadata management: edit title/author, upload custom cover art, or auto-fetch from online sources.
            </p>
          </div>
          <button type="button" onClick={onClose} style={closeButtonStyle} aria-label="Close dialog">
            ✕
          </button>
        </div>

        <div style={contentStyle}>
          <div style={previewPanelStyle}>
            <div style={coverFrameStyle}>
              {coverUrl ? (
                <img src={coverUrl} alt="Cover preview" style={coverImageStyle} />
              ) : (
                <div style={coverFallbackStyle}>
                  <span style={coverFallbackTextStyle}>{getInitials(title || book.title)}</span>
                </div>
              )}
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelected}
              accept="image/*"
              style={{ display: "none" }}
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              style={actionOutlineButtonStyle}
            >
              📷 Upload Cover Picture
            </button>

            <button
              type="button"
              onClick={handleFetchOnline}
              disabled={isFetchingOnline}
              style={fetchOnlineButtonStyle}
            >
              {isFetchingOnline ? "🔍 Searching OpenLibrary..." : "🌐 Fetch Metadata Online"}
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

            {onlineSearchOpen ? (
              <div style={onlineResultsBoxStyle}>
                <div style={onlineHeaderStyle}>
                  <span style={onlineTitleStyle}>{onlineSearchMessage}</span>
                  <button
                    type="button"
                    onClick={() => setOnlineSearchOpen(false)}
                    style={smallCloseButtonStyle}
                  >
                    ✕
                  </button>
                </div>
                {onlineResults.map((result, idx) => (
                  <div key={idx} style={matchItemStyle}>
                    {result.coverUrl ? (
                      <img src={result.coverUrl} alt="" style={matchThumbStyle} />
                    ) : (
                      <div style={matchThumbFallbackStyle}>📖</div>
                    )}
                    <div style={matchInfoStyle}>
                      <p style={matchTitleStyle}>{result.title}</p>
                      <p style={matchMetaStyle}>
                        {result.author} {result.firstPublishYear ? `(${result.firstPublishYear})` : ""}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleApplyMatch(result)}
                      style={applyMatchButtonStyle}
                    >
                      Apply
                    </button>
                  </div>
                ))}
              </div>
            ) : null}

            <div style={infoPanelStyle}>
              <p style={infoTitleStyle}>Calibre-Style Library Integration</p>
              <p style={infoBodyStyle}>
                Updates are stored with the book and will reflect across the reader, library tiled grid, and Calibre list views.
              </p>
            </div>

            {error ? <p style={errorStyle}>{error}</p> : null}

            <div style={actionsStyle}>
              <button type="button" onClick={onClose} style={secondaryButtonStyle}>
                Cancel
              </button>
              <button type="submit" disabled={isSaving} style={primaryButtonStyle}>
                {isSaving ? "Saving changes..." : "Save Metadata"}
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
  overflowY: "auto",
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
  maxWidth: 550,
  lineHeight: "1.4",
  fontSize: "0.92rem",
};

const closeButtonStyle = {
  border: "1px solid rgba(115, 98, 74, 0.18)",
  background: "#fff9f2",
  color: "#4b4037",
  borderRadius: 999,
  width: 36,
  height: 36,
  fontSize: "0.95rem",
  flexShrink: 0,
  cursor: "pointer",
};

const contentStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
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
  borderRadius: 20,
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

const actionOutlineButtonStyle = {
  border: "1px solid #d5c9ba",
  background: "#fffdfa",
  color: "#4a3e33",
  borderRadius: 12,
  padding: "0.65rem 0.85rem",
  fontSize: "0.85rem",
  fontWeight: 600,
  cursor: "pointer",
  textAlign: "center",
};

const fetchOnlineButtonStyle = {
  border: "1px solid #c2996d",
  background: "#fbf3e8",
  color: "#7e5229",
  borderRadius: 12,
  padding: "0.65rem 0.85rem",
  fontSize: "0.85rem",
  fontWeight: 600,
  cursor: "pointer",
  textAlign: "center",
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
  padding: "0.85rem 1rem",
  background: "#fffdfa",
  color: "#1f2930",
  fontSize: "1rem",
};

const onlineResultsBoxStyle = {
  border: "1px solid #d5c9ba",
  borderRadius: 16,
  background: "#fcf9f4",
  padding: "0.85rem",
  display: "flex",
  flexDirection: "column",
  gap: "0.65rem",
  maxHeight: "220px",
  overflowY: "auto",
};

const onlineHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
};

const onlineTitleStyle = {
  fontSize: "0.85rem",
  fontWeight: 600,
  color: "#7e5229",
};

const smallCloseButtonStyle = {
  border: "none",
  background: "none",
  color: "#7e5229",
  cursor: "pointer",
  fontSize: "0.85rem",
};

const matchItemStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.75rem",
  background: "#ffffff",
  border: "1px solid #e8ded2",
  borderRadius: 10,
  padding: "0.5rem 0.75rem",
};

const matchThumbStyle = {
  width: "32px",
  height: "44px",
  objectFit: "cover",
  borderRadius: 4,
};

const matchThumbFallbackStyle = {
  width: "32px",
  height: "44px",
  background: "#eee5d7",
  borderRadius: 4,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "1rem",
};

const matchInfoStyle = {
  flex: 1,
  minWidth: 0,
};

const matchTitleStyle = {
  margin: 0,
  fontSize: "0.88rem",
  fontWeight: 600,
  color: "#241f1a",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const matchMetaStyle = {
  margin: "0.15rem 0 0",
  fontSize: "0.78rem",
  color: "#786d62",
};

const applyMatchButtonStyle = {
  border: "1px solid #8b5e3c",
  background: "#fdf8f2",
  color: "#8b5e3c",
  borderRadius: 8,
  padding: "0.35rem 0.7rem",
  fontSize: "0.78rem",
  fontWeight: 600,
  cursor: "pointer",
};

const infoPanelStyle = {
  padding: "0.9rem 1rem",
  borderRadius: 16,
  background: "#fff8ef",
  border: "1px solid #eadcc8",
};

const infoTitleStyle = {
  margin: 0,
  fontWeight: 700,
  fontSize: "0.9rem",
  color: "#3c312a",
};

const infoBodyStyle = {
  margin: "0.35rem 0 0",
  fontSize: "0.85rem",
  color: "#655f57",
  lineHeight: 1.45,
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
  padding: "0.75rem 1.15rem",
  background: "#fff8ef",
  color: "#3c312a",
  fontWeight: 600,
  cursor: "pointer",
};

const primaryButtonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.75rem 1.25rem",
  background: "#193847",
  color: "#fff",
  fontWeight: 700,
  cursor: "pointer",
};
