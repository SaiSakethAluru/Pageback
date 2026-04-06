import { useEffect, useRef, useState } from "react";

import { useNavigate } from "react-router-dom";

import * as api from "../../services/api";

export default function BookCard({ book, onDelete, onEditMetadata }) {
  const navigate = useNavigate();
  const menuRef = useRef(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isStartingAI, setIsStartingAI] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    if (!menuOpen) {
      return undefined;
    }

    function handleWindowClick(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    window.addEventListener("mousedown", handleWindowClick);
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("mousedown", handleWindowClick);
      window.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  function handleDeleteClick() {
    setMenuOpen(false);
    onDelete?.(book);
  }

  async function handleEnableAI() {
    setActionError("");
    setMenuOpen(false);
    setIsStartingAI(true);
    try {
      await api.startIngestion(book.id, { background: true });
    } catch (error) {
      setActionError(error.message);
    } finally {
      setIsStartingAI(false);
    }
  }

  const title = book.title || "Untitled book";
  const author = book.author || "Unknown author";
  const showHoverMeta = isHovered || menuOpen;

  return (
    <article style={cardShellStyle}>
      <div
        style={cardStyle(isHovered)}
        role="button"
        tabIndex={0}
        onClick={() => navigate(`/reader/${book.id}`)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onFocus={() => setIsHovered(true)}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) {
            setIsHovered(false);
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            navigate(`/reader/${book.id}`);
          }
        }}
      >
        <div style={coverWrapStyle}>
          <div style={coverMediaStyle(isHovered)}>
            {book.cover_url ? (
              <img src={book.cover_url} alt="" style={coverImageStyle} />
            ) : (
              <div style={fallbackCoverStyle}>
                <div style={fallbackSpineStyle} />
                <div style={fallbackTextWrapStyle}>
                  <p style={fallbackEyebrowStyle}>PageBack</p>
                  <div style={fallbackMetaStackStyle}>
                    <p style={fallbackTitleStyle}>{title}</p>
                    <p style={fallbackAuthorStyle}>{author}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div style={coverOverlayStyle(showHoverMeta)} />

          <div style={topRowStyle}>
            <div ref={menuRef} style={menuWrapStyle}>
              <button
                type="button"
                aria-label={`Open actions for ${title}`}
                onClick={(event) => {
                  event.stopPropagation();
                  setMenuOpen((open) => !open);
                }}
                style={menuButtonStyle}
              >
                <span style={menuDotsStyle}>⋮</span>
              </button>
              {menuOpen ? (
                <div style={menuStyle} onClick={(event) => event.stopPropagation()}>
                  <button type="button" style={menuItemStyle} onClick={() => onEditMetadata?.(book)}>
                    Edit metadata
                  </button>
                  {book.ingestion_status !== "complete" ? (
                    <button
                      type="button"
                      disabled={isStartingAI}
                      style={menuItemStyle}
                      onClick={handleEnableAI}
                    >
                      {isStartingAI ? "Starting AI..." : "Enable AI indexing"}
                    </button>
                  ) : null}
                  <button type="button" style={dangerMenuItemStyle} onClick={handleDeleteClick}>
                    Delete book
                  </button>
                </div>
              ) : null}
            </div>
          </div>

          <div style={metaOverlayStyle(showHoverMeta)}>
            <div style={titleRowStyle}>
              <h3 style={titleStyle}>{title}</h3>
              {book.ingestion_status === "complete" ? <span style={statusCheckStyle}>✓</span> : null}
            </div>
            <p style={authorStyle}>{author}</p>
          </div>
        </div>
      </div>
      {actionError ? <p style={errorStyle}>{actionError}</p> : null}
    </article>
  );
}

const cardShellStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.5rem",
};

const cardStyle = (isHovered) => ({
  cursor: "pointer",
  borderRadius: 26,
  overflow: "hidden",
  background: "#efe5d7",
  boxShadow: "0 22px 50px rgba(44, 33, 20, 0.12)",
  transition: "transform 180ms ease, box-shadow 180ms ease",
  transform: isHovered ? "translateY(-4px)" : "translateY(0)",
});

const coverWrapStyle = {
  position: "relative",
  aspectRatio: "0.76",
  minHeight: 320,
  background: "linear-gradient(155deg, #d7b98b 0%, #8e5f41 50%, #3f2b28 100%)",
};

const coverMediaStyle = (isHovered) => ({
  width: "100%",
  height: "100%",
  transition: "filter 180ms ease, transform 180ms ease",
  filter: isHovered ? "blur(8px)" : "none",
  transform: isHovered ? "scale(1.03)" : "scale(1)",
});

const coverImageStyle = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
  display: "block",
};

const fallbackCoverStyle = {
  width: "100%",
  height: "100%",
  display: "flex",
  alignItems: "stretch",
  background: "linear-gradient(155deg, #d7b98b 0%, #8e5f41 50%, #3f2b28 100%)",
};

const fallbackSpineStyle = {
  width: 18,
  background: "linear-gradient(180deg, rgba(255,255,255,0.24), rgba(33, 17, 11, 0.24))",
  boxShadow: "inset -1px 0 0 rgba(255,255,255,0.22)",
};

const fallbackTextWrapStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between",
  padding: "1.35rem 1.2rem 1.25rem",
};

const fallbackMetaStackStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.75rem",
};

const fallbackEyebrowStyle = {
  margin: 0,
  color: "rgba(255, 247, 236, 0.76)",
  textTransform: "uppercase",
  letterSpacing: "0.12em",
  fontSize: "0.72rem",
};

const fallbackTitleStyle = {
  margin: 0,
  color: "#fff8ee",
  fontSize: "1.55rem",
  lineHeight: 1.1,
  maxWidth: "85%",
  textWrap: "balance",
};

const fallbackAuthorStyle = {
  margin: 0,
  color: "rgba(255, 248, 238, 0.8)",
  fontSize: "0.95rem",
  lineHeight: 1.35,
  maxWidth: "82%",
};

const coverOverlayStyle = (showHoverMeta) => ({
  position: "absolute",
  inset: 0,
  background:
    "linear-gradient(180deg, rgba(16, 22, 28, 0.08) 0%, rgba(16, 22, 28, 0.08) 28%, rgba(16, 22, 28, 0.78) 100%)",
  opacity: showHoverMeta ? 1 : 0,
  transition: "opacity 180ms ease",
});

const topRowStyle = {
  position: "absolute",
  top: 14,
  left: 16,
  right: 14,
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "flex-end",
  gap: "0.75rem",
  zIndex: 2,
};

const menuWrapStyle = {
  position: "relative",
};

const menuButtonStyle = {
  display: "grid",
  placeItems: "center",
  width: 30,
  height: 30,
  border: "none",
  padding: 0,
  background: "transparent",
  color: "#fffaf1",
  cursor: "pointer",
  textShadow: "0 2px 8px rgba(0,0,0,0.45)",
};

const menuDotsStyle = {
  fontSize: "1.35rem",
  lineHeight: 1,
};

const menuStyle = {
  position: "absolute",
  top: 46,
  right: 0,
  minWidth: 190,
  display: "flex",
  flexDirection: "column",
  padding: "0.4rem",
  borderRadius: 16,
  background: "#fffaf3",
  border: "1px solid rgba(115, 98, 74, 0.14)",
  boxShadow: "0 24px 50px rgba(25, 23, 19, 0.22)",
  zIndex: 3,
};

const menuItemStyle = {
  border: "none",
  borderRadius: 12,
  background: "transparent",
  textAlign: "left",
  padding: "0.7rem 0.85rem",
  color: "#2d302f",
  fontWeight: 600,
  cursor: "pointer",
};

const dangerMenuItemStyle = {
  ...menuItemStyle,
  color: "#a11d1d",
};

const metaOverlayStyle = (showHoverMeta) => ({
  position: "absolute",
  left: 0,
  right: 0,
  bottom: 0,
  padding: "1.15rem 1.15rem 1.2rem",
  zIndex: 2,
  opacity: showHoverMeta ? 1 : 0,
  transform: showHoverMeta ? "translateY(0)" : "translateY(8px)",
  transition: "opacity 180ms ease, transform 180ms ease",
});

const titleRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.55rem",
};

const titleStyle = {
  margin: 0,
  color: "#fffdf8",
  fontSize: "1.2rem",
  lineHeight: 1.15,
  textShadow: "0 2px 10px rgba(0,0,0,0.22)",
};

const authorStyle = {
  margin: "0.35rem 0 0",
  color: "rgba(255, 249, 242, 0.88)",
  fontSize: "0.95rem",
};

const statusCheckStyle = {
  display: "inline-grid",
  placeItems: "center",
  width: 20,
  height: 20,
  borderRadius: 999,
  background: "#58b66b",
  color: "#fff",
  fontSize: "0.82rem",
  fontWeight: 800,
  boxShadow: "0 6px 16px rgba(15, 53, 24, 0.28)",
};

const errorStyle = {
  margin: 0,
  color: "#a11d1d",
  fontSize: "0.84rem",
};
