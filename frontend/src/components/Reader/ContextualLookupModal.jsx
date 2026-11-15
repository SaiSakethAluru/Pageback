import { useEffect, useState } from "react";
import * as api from "../../services/api";

export default function ContextualLookupModal({
  bookId,
  term,
  positionChar = 0,
  positionCfi = null,
  isOpen,
  onClose,
}) {
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose?.();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen || !term || !bookId) {
      return;
    }

    let isCancelled = false;
    setLoading(true);
    setError("");
    setResult(null);
    setCopied(false);

    api
      .lookupContextual(bookId, term, positionChar, positionCfi)
      .then((data) => {
        if (!isCancelled) {
          setResult(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setError(err.message || "Failed to search book context.");
          setLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [bookId, term, positionChar, positionCfi, isOpen]);

  if (!isOpen || !term) {
    return null;
  }

  async function handleCopy() {
    try {
      const textToCopy = result?.explanation
        ? `${term}: ${result.explanation}`
        : term;
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  }

  return (
    <div style={backdropStyle} onClick={onClose}>
      <style>{`
        @keyframes pagebackSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pagebackFadeIn {
          from { opacity: 0; transform: scale(0.97); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>
      <div
        style={dialogStyle}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`Contextual lookup for ${term}`}
      >
        <div style={headerStyle}>
          <div style={headerLeftStyle}>
            <div style={badgeRowStyle}>
              <span style={badgeStyle}>Book Lore & Character</span>
              <span style={spoilerBadgeStyle}>🛡️ Spoiler-safe</span>
            </div>
            <h3 style={termTitleStyle}>{term}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={closeButtonStyle}
            aria-label="Close contextual lookup"
          >
            ✕
          </button>
        </div>

        <div style={bodyStyle}>
          {loading ? (
            <div style={loadingStyle}>
              <div style={spinnerStyle} />
              <p style={loadingTextStyle}>
                Scanning read chapters for "{term}"...
              </p>
            </div>
          ) : null}

          {!loading && error ? (
            <div style={errorContainerStyle}>
              <p style={errorTextStyle}>{error}</p>
              <button
                type="button"
                onClick={() => {
                  setLoading(true);
                  setError("");
                  api
                    .lookupContextual(bookId, term, positionChar, positionCfi)
                    .then((data) => {
                      setResult(data);
                      setLoading(false);
                    })
                    .catch((err) => {
                      setError(err.message || "Failed to search book context.");
                      setLoading(false);
                    });
                }}
                style={retryButtonStyle}
              >
                Try again
              </button>
            </div>
          ) : null}

          {!loading && result ? (
            <div style={contentContainerStyle}>
              <p style={explanationTextStyle}>{result.explanation}</p>
              {!result.grounded ? (
                <div style={noticeBoxStyle}>
                  💡 <strong>Reading Note:</strong> No mentions of this term
                  were found in the portions of the book you have read so far.
                  Keep reading to uncover more!
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        <div style={footerStyle}>
          <button
            type="button"
            onClick={handleCopy}
            disabled={loading || Boolean(error)}
            style={secondaryButtonStyle}
          >
            {copied ? "✓ Copied" : "Copy explanation"}
          </button>
          <button type="button" onClick={onClose} style={doneButtonStyle}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

const backdropStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(23, 28, 34, 0.45)",
  backdropFilter: "blur(4px)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 95,
  padding: "1rem",
  overflowY: "auto",
};

const dialogStyle = {
  width: "min(520px, 94vw)",
  maxHeight: "82vh",
  display: "flex",
  flexDirection: "column",
  borderRadius: "20px",
  background: "#fbf8f3",
  color: "#211d19",
  boxShadow: "0 24px 60px rgba(20, 25, 31, 0.32)",
  border: "1px solid rgba(115, 98, 74, 0.2)",
  overflow: "hidden",
  animation: "pagebackFadeIn 0.15s ease-out",
};

const headerStyle = {
  padding: "1.2rem 1.4rem 0.9rem",
  borderBottom: "1px solid rgba(115, 98, 74, 0.12)",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  background: "#f6f1e8",
  flexShrink: 0,
};

const headerLeftStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.35rem",
};

const badgeRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.5rem",
  flexWrap: "wrap",
};

const badgeStyle = {
  fontSize: "0.72rem",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "#8c6541",
};

const spoilerBadgeStyle = {
  fontSize: "0.72rem",
  fontWeight: 600,
  color: "#2b5e3b",
  background: "#e4efe7",
  padding: "0.15rem 0.5rem",
  borderRadius: "6px",
};

const termTitleStyle = {
  fontSize: "1.4rem",
  margin: 0,
  fontFamily: "Georgia, serif",
  fontWeight: 700,
  color: "#1c1712",
};

const closeButtonStyle = {
  background: "none",
  border: "none",
  fontSize: "1.1rem",
  cursor: "pointer",
  color: "#7a6e60",
  padding: "0.2rem 0.5rem",
  borderRadius: "8px",
};

const bodyStyle = {
  padding: "1.2rem 1.4rem",
  overflowY: "auto",
  flex: 1,
};

const loadingStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "2.5rem 1rem",
};

const spinnerStyle = {
  width: "32px",
  height: "32px",
  border: "3px solid #e0d7c7",
  borderTopColor: "#8c6541",
  borderRadius: "50%",
  animation: "pagebackSpin 0.8s linear infinite",
};

const loadingTextStyle = {
  margin: "0.75rem 0 0",
  color: "#6e6255",
  fontSize: "0.92rem",
};

const errorContainerStyle = {
  padding: "1.5rem 0",
  textAlign: "center",
};

const errorTextStyle = {
  color: "#8a2424",
  fontSize: "0.95rem",
  margin: "0 0 1rem",
};

const retryButtonStyle = {
  fontSize: "0.85rem",
  color: "#8c6541",
  background: "#f6f1e8",
  border: "1px solid rgba(140, 101, 65, 0.3)",
  padding: "0.45rem 0.9rem",
  borderRadius: "8px",
  cursor: "pointer",
};

const contentContainerStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
};

const explanationTextStyle = {
  margin: 0,
  fontSize: "1rem",
  lineHeight: "1.65",
  color: "#28221c",
  whiteSpace: "pre-wrap",
};

const noticeBoxStyle = {
  background: "#f1ede4",
  border: "1px solid rgba(115, 98, 74, 0.15)",
  borderRadius: "10px",
  padding: "0.75rem 1rem",
  fontSize: "0.88rem",
  lineHeight: "1.5",
  color: "#5c5042",
};

const footerStyle = {
  padding: "0.85rem 1.4rem",
  borderTop: "1px solid rgba(115, 98, 74, 0.12)",
  background: "#f6f1e8",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "0.5rem",
  flexShrink: 0,
};

const secondaryButtonStyle = {
  background: "none",
  border: "1px solid rgba(115, 98, 74, 0.25)",
  padding: "0.45rem 0.9rem",
  borderRadius: "10px",
  fontSize: "0.85rem",
  cursor: "pointer",
  color: "#4a4237",
};

const doneButtonStyle = {
  background: "#3e3223",
  color: "#f6f1e8",
  border: "none",
  padding: "0.45rem 1.1rem",
  borderRadius: "10px",
  fontSize: "0.85rem",
  fontWeight: 600,
  cursor: "pointer",
};
