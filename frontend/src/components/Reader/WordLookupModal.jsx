import { useEffect, useState, useRef } from "react";
import { lookupWord } from "../../services/dictionary";

export default function WordLookupModal({
  word,
  isOpen,
  onClose,
  position = null,
  onContextualLookup = null,
}) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !word) {
      return;
    }

    let isCancelled = false;
    setLoading(true);
    setError("");
    setData(null);
    setCopied(false);

    lookupWord(word)
      .then((result) => {
        if (!isCancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setError(err.message || "Could not look up word.");
          setLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [word, isOpen]);

  if (!isOpen || !word) {
    return null;
  }

  function handlePlayAudio() {
    if (data?.audioUrl) {
      if (!audioRef.current) {
        audioRef.current = new Audio(data.audioUrl);
      } else {
        audioRef.current.src = data.audioUrl;
      }
      audioRef.current.play().catch(() => {});
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(word);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  }

  // Calculate popover positioning if position coords provided
  let containerPositionStyle = {};
  if (position && position.top != null) {
    const spaceBelow = window.innerHeight - position.bottom;
    const placeAbove = spaceBelow < 320 && position.top > 320;
    const top = placeAbove
      ? Math.max(16, position.top - 360)
      : Math.min(window.innerHeight - 380, position.bottom + 12);
    const left = Math.max(
      16,
      Math.min(window.innerWidth - 380, position.left - 100)
    );

    containerPositionStyle = {
      position: "fixed",
      top: `${top}px`,
      left: `${left}px`,
      zIndex: 100,
    };
  }

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div
        style={{ ...dialogStyle, ...containerPositionStyle }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label={`Definition of ${word}`}
      >
        <div style={headerStyle}>
          <div style={headerLeftStyle}>
            <span style={badgeStyle}>Dictionary</span>
            <div style={wordRowStyle}>
              <h3 style={wordTitleStyle}>{data?.word || word}</h3>
              {data?.phonetic ? (
                <span style={phoneticStyle}>{data.phonetic}</span>
              ) : null}
              {data?.audioUrl ? (
                <button
                  type="button"
                  onClick={handlePlayAudio}
                  style={audioButtonStyle}
                  title="Play pronunciation"
                  aria-label="Play pronunciation"
                >
                  🔊
                </button>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={closeButtonStyle}
            aria-label="Close dictionary lookup"
          >
            ✕
          </button>
        </div>

        <div style={bodyStyle}>
          {loading ? (
            <div style={loadingStyle}>
              <div style={spinnerStyle} />
              <p style={{ margin: "0.5rem 0 0", color: "#6e6255" }}>
                Looking up "{word}"...
              </p>
            </div>
          ) : null}

          {!loading && error ? (
            <div style={errorContainerStyle}>
              <p style={errorTextStyle}>{error}</p>
              <div style={fallbackActionsStyle}>
                <a
                  href={`https://en.wiktionary.org/wiki/${encodeURIComponent(
                    word.toLowerCase()
                  )}`}
                  target="_blank"
                  rel="noreferrer"
                  style={externalLinkStyle}
                >
                  Search on Wiktionary ↗
                </a>
                <a
                  href={`https://www.google.com/search?q=define+${encodeURIComponent(
                    word
                  )}`}
                  target="_blank"
                  rel="noreferrer"
                  style={externalLinkStyle}
                >
                  Search Google ↗
                </a>
              </div>
            </div>
          ) : null}

          {!loading && data ? (
            <div style={definitionsContainerStyle}>
              {data.meanings.map((meaning, mIdx) => (
                <div key={mIdx} style={meaningBlockStyle}>
                  <div style={posBadgeStyle}>{meaning.partOfSpeech}</div>
                  <ol style={definitionListStyle}>
                    {meaning.definitions.slice(0, 3).map((def, dIdx) => (
                      <li key={dIdx} style={definitionItemStyle}>
                        <p style={defTextStyle}>{def.definition}</p>
                        {def.example ? (
                          <p style={exampleTextStyle}>"{def.example}"</p>
                        ) : null}
                      </li>
                    ))}
                  </ol>
                  {meaning.synonyms && meaning.synonyms.length > 0 ? (
                    <div style={synonymsRowStyle}>
                      <span style={synonymsLabelStyle}>Synonyms:</span>
                      {meaning.synonyms.slice(0, 5).map((syn, sIdx) => (
                        <span key={sIdx} style={synonymChipStyle}>
                          {syn}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div style={footerStyle}>
          <button
            type="button"
            onClick={handleCopy}
            style={secondaryButtonStyle}
          >
            {copied ? "✓ Copied" : "Copy word"}
          </button>

          {onContextualLookup ? (
            <button
              type="button"
              onClick={() => {
                onClose();
                onContextualLookup(word);
              }}
              style={contextualButtonStyle}
            >
              🔍 Contextual lookup in book
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

const backdropStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(23, 28, 34, 0.42)",
  backdropFilter: "blur(4px)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 90,
  padding: "1rem",
};

const dialogStyle = {
  width: "min(460px, 94vw)",
  maxHeight: "82vh",
  display: "flex",
  flexDirection: "column",
  borderRadius: "20px",
  background: "#fbf8f3",
  color: "#211d19",
  boxShadow: "0 24px 60px rgba(20, 25, 31, 0.28)",
  border: "1px solid rgba(115, 98, 74, 0.2)",
  overflow: "hidden",
};

const headerStyle = {
  padding: "1.1rem 1.25rem 0.8rem",
  borderBottom: "1px solid rgba(115, 98, 74, 0.12)",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  background: "#f6f1e8",
};

const headerLeftStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.25rem",
};

const badgeStyle = {
  fontSize: "0.72rem",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "#8c6541",
};

const wordRowStyle = {
  display: "flex",
  alignItems: "baseline",
  gap: "0.5rem",
  flexWrap: "wrap",
};

const wordTitleStyle = {
  fontSize: "1.35rem",
  margin: 0,
  fontFamily: "Georgia, serif",
  fontWeight: 700,
  color: "#1c1712",
};

const phoneticStyle = {
  fontSize: "0.9rem",
  color: "#7a6e60",
  fontStyle: "italic",
};

const audioButtonStyle = {
  background: "none",
  border: "none",
  cursor: "pointer",
  fontSize: "1rem",
  padding: "0.1rem 0.3rem",
  borderRadius: "6px",
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
  padding: "1rem 1.25rem",
  overflowY: "auto",
  flex: 1,
};

const loadingStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "2rem 1rem",
};

const spinnerStyle = {
  width: "28px",
  height: "28px",
  border: "3px solid #e0d7c7",
  borderTopColor: "#8c6541",
  borderRadius: "50%",
  animation: "spin 0.8s linear infinite",
};

const errorContainerStyle = {
  padding: "1.2rem 0",
  textAlign: "center",
};

const errorTextStyle = {
  color: "#7a6e60",
  fontSize: "0.95rem",
  margin: "0 0 1rem",
};

const fallbackActionsStyle = {
  display: "flex",
  justifyContent: "center",
  gap: "0.75rem",
  flexWrap: "wrap",
};

const externalLinkStyle = {
  fontSize: "0.85rem",
  color: "#8c6541",
  textDecoration: "none",
  border: "1px solid rgba(140, 101, 65, 0.3)",
  padding: "0.4rem 0.8rem",
  borderRadius: "999px",
  background: "#f6f1e8",
};

const definitionsContainerStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
};

const meaningBlockStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.4rem",
};

const posBadgeStyle = {
  alignSelf: "flex-start",
  fontSize: "0.75rem",
  fontStyle: "italic",
  fontWeight: 600,
  color: "#8c6541",
  background: "#ece5d8",
  padding: "0.15rem 0.5rem",
  borderRadius: "6px",
};

const definitionListStyle = {
  margin: "0.25rem 0 0 1.25rem",
  padding: 0,
  display: "flex",
  flexDirection: "column",
  gap: "0.5rem",
};

const definitionItemStyle = {
  fontSize: "0.92rem",
  lineHeight: "1.45",
  color: "#2e2924",
};

const defTextStyle = {
  margin: 0,
};

const exampleTextStyle = {
  margin: "0.2rem 0 0",
  fontSize: "0.85rem",
  fontStyle: "italic",
  color: "#73685c",
};

const synonymsRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.4rem",
  flexWrap: "wrap",
  marginTop: "0.3rem",
};

const synonymsLabelStyle = {
  fontSize: "0.75rem",
  color: "#73685c",
};

const synonymChipStyle = {
  fontSize: "0.75rem",
  background: "#eee7db",
  color: "#4a4237",
  padding: "0.1rem 0.4rem",
  borderRadius: "4px",
};

const footerStyle = {
  padding: "0.75rem 1.25rem",
  borderTop: "1px solid rgba(115, 98, 74, 0.12)",
  background: "#f6f1e8",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "0.5rem",
};

const secondaryButtonStyle = {
  background: "none",
  border: "1px solid rgba(115, 98, 74, 0.25)",
  padding: "0.45rem 0.85rem",
  borderRadius: "10px",
  fontSize: "0.82rem",
  cursor: "pointer",
  color: "#4a4237",
};

const contextualButtonStyle = {
  background: "#3e3223",
  color: "#f6f1e8",
  border: "none",
  padding: "0.45rem 0.95rem",
  borderRadius: "10px",
  fontSize: "0.82rem",
  fontWeight: 600,
  cursor: "pointer",
};
