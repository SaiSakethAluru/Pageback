import { useEffect, useRef } from "react";

export default function TextSelectionToolbar({
  selectedText,
  rect,
  onDefine,
  onContextualLookup,
  onClear,
}) {
  const toolbarRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (toolbarRef.current && !toolbarRef.current.contains(event.target)) {
        onClear?.();
      }
    }
    window.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("touchstart", handleClickOutside);
    return () => {
      window.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("touchstart", handleClickOutside);
    };
  }, [onClear]);

  if (!selectedText || !rect) {
    return null;
  }

  const isShortText = selectedText.trim().split(/\s+/).length <= 4;
  
  // Calculate position centered horizontally above or below selection
  const toolbarHeight = 44;
  const estimatedWidth = isShortText ? 260 : 160;
  const left = Math.max(
    12,
    Math.min(
      window.innerWidth - estimatedWidth - 12,
      rect.left + rect.width / 2 - estimatedWidth / 2
    )
  );

  const placeAbove = rect.top > toolbarHeight + 16;
  const top = placeAbove
    ? rect.top - toolbarHeight - 8
    : rect.bottom + 8;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(selectedText);
      onClear?.();
    } catch {
      // ignore
    }
  }

  return (
    <div
      ref={toolbarRef}
      style={{
        ...toolbarStyle,
        top: `${top}px`,
        left: `${left}px`,
      }}
      role="toolbar"
      aria-label="Text selection actions"
    >
      <style>{`
        @keyframes pagebackToolbarFadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {isShortText && onDefine ? (
        <button
          type="button"
          onClick={() => {
            onDefine(selectedText);
          }}
          style={actionButtonStyle}
          title="Look up in dictionary"
        >
          📖 Define
        </button>
      ) : null}

      {onContextualLookup ? (
        <button
          type="button"
          onClick={() => {
            onContextualLookup(selectedText);
          }}
          style={actionButtonStyle}
          title="Explain in book context"
        >
          🔍 In Context
        </button>
      ) : null}

      <button
        type="button"
        onClick={handleCopy}
        style={actionButtonStyle}
        title="Copy text"
      >
        📋 Copy
      </button>

      <button
        type="button"
        onClick={onClear}
        style={closeButtonStyle}
        title="Dismiss"
      >
        ✕
      </button>
    </div>
  );
}

const toolbarStyle = {
  position: "fixed",
  height: "40px",
  width: "auto",
  minWidth: "150px",
  maxWidth: "calc(100vw - 24px)",
  background: "#1c1712",
  color: "#f6f1e8",
  borderRadius: "12px",
  boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0 10px",
  zIndex: 85,
  gap: "6px",
  animation: "pagebackToolbarFadeIn 0.15s ease-out",
};

const actionButtonStyle = {
  background: "transparent",
  border: "none",
  color: "#f6f1e8",
  fontSize: "0.82rem",
  fontWeight: 600,
  padding: "6px 8px",
  borderRadius: "8px",
  cursor: "pointer",
  whiteSpace: "nowrap",
  transition: "background 0.12s ease",
};

const closeButtonStyle = {
  background: "transparent",
  border: "none",
  color: "#a69b8d",
  fontSize: "0.85rem",
  padding: "4px 6px",
  borderRadius: "6px",
  cursor: "pointer",
};
