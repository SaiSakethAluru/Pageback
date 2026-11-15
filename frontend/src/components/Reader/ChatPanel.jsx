import { useEffect, useRef, useState } from "react";
import * as api from "../../services/api";

const SUGGESTIONS = [
  "Summarize key events so far",
  "Who are the main characters right now?",
  "What is the current mystery or goal?",
  "Explain what just happened in this chapter",
];

export default function ChatPanel({
  bookId,
  positionChar = 0,
  positionCfi = null,
  isOpen,
  onClose,
}) {
  const storageKey = `pageback_chat_${bookId}`;
  const [messages, setMessages] = useState(() => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [seriesInfo, setSeriesInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!bookId) return;
    let active = true;
    api.getBookSeries(bookId)
      .then((data) => {
        if (active && data?.series_name && data?.previous_books?.length > 0) {
          setSeriesInfo(data);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [bookId]);

  useEffect(() => {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {
      // ignore storage errors
    }
  }, [messages, storageKey]);

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
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (!isOpen) {
    return null;
  }

  async function handleSend(textToSend) {
    const text = (textToSend || input).trim();
    if (!text || isLoading) return;

    setInput("");
    setError("");
    const newMessages = [...messages, { role: "user", content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage(
        bookId,
        newMessages,
        positionChar,
        positionCfi
      );
      setMessages([
        ...newMessages,
        { role: "assistant", content: response.reply },
      ]);
    } catch (err) {
      setError(err.message || "Failed to get an answer.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleClear() {
    setMessages([]);
    setError("");
    try {
      sessionStorage.removeItem(storageKey);
    } catch {
      // ignore
    }
  }

  return (
    <aside
      style={panelStyle}
      role="complementary"
      aria-label="Book discussion side chat"
    >
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
      <div style={headerStyle}>
        <div>
          <div style={titleRowStyle}>
            <span style={badgeStyle}>Cursor Chat</span>
            <span style={spoilerBadgeStyle}>🛡️ Spoiler-safe</span>
            {seriesInfo ? (
              <span
                style={seriesTagStyle}
                title={`Backstory context active from ${seriesInfo.previous_books.length} earlier book(s) in ${seriesInfo.series_name}`}
              >
                📚 Series: {seriesInfo.series_name}
              </span>
            ) : null}
          </div>
          <h2 style={titleStyle}>Book Assistant</h2>
          <p style={subtitleStyle}>
            Ask questions grounded strictly in what you have read so far.
          </p>
        </div>
        <div style={headerActionsStyle}>
          {messages.length > 0 ? (
            <button
              type="button"
              onClick={handleClear}
              style={clearButtonStyle}
              title="Clear chat history"
            >
              Clear
            </button>
          ) : null}
          <button
            type="button"
            onClick={onClose}
            style={closeButtonStyle}
            aria-label="Close chat panel"
          >
            ✕
          </button>
        </div>
      </div>

      <div style={messagesContainerStyle}>
        {messages.length === 0 ? (
          <div style={emptyStateStyle}>
            <p style={emptyTitleStyle}>Discuss this book</p>
            <p style={emptyDescStyle}>
              Ask about characters, motives, clues, or themes. All answers are
              strictly spoiler-safe and restricted to what you have already read.
            </p>

            <div style={suggestionsTitleStyle}>Suggested questions</div>
            <div style={suggestionsListStyle}>
              {SUGGESTIONS.map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(suggestion)}
                  style={suggestionPillStyle}
                >
                  💬 {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              ...messageRowStyle,
              justifyContent:
                msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              style={
                msg.role === "user" ? userBubbleStyle : assistantBubbleStyle
              }
            >
              {msg.role === "assistant" ? (
                <div style={assistantHeaderStyle}>
                  <span style={assistantIconStyle}>📖 PageBack AI</span>
                </div>
              ) : null}
              <p style={messageTextStyle}>{msg.content}</p>
            </div>
          </div>
        ))}

        {isLoading ? (
          <div style={{ ...messageRowStyle, justifyContent: "flex-start" }}>
            <div style={assistantBubbleStyle}>
              <div style={loadingDotsStyle}>
                <span style={dotStyle}>●</span>
                <span style={dotStyle}>●</span>
                <span style={dotStyle}>●</span>
                <span style={loadingLabelStyle}>Thinking with book context...</span>
              </div>
            </div>
          </div>
        ) : null}

        {error ? (
          <div style={errorBannerStyle}>
            <p style={errorTextStyle}>{error}</p>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </div>

      <form
        style={inputFormStyle}
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about what you've read... (Enter to send)"
          rows={2}
          style={textareaStyle}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          style={{
            ...sendButtonStyle,
            opacity: !input.trim() || isLoading ? 0.5 : 1,
            cursor: !input.trim() || isLoading ? "not-allowed" : "pointer",
          }}
          aria-label="Send message"
        >
          Send
        </button>
      </form>
    </aside>
  );
}

const panelStyle = {
  position: "fixed",
  top: 0,
  right: 0,
  bottom: 0,
  width: "min(430px, 100vw)",
  background: "#fbf8f3",
  color: "#211d19",
  boxShadow: "-8px 0 32px rgba(20, 25, 31, 0.22)",
  borderLeft: "1px solid rgba(115, 98, 74, 0.2)",
  display: "flex",
  flexDirection: "column",
  zIndex: 70,
  animation: "slideInRight 0.2s ease-out",
};

const headerStyle = {
  padding: "1.1rem 1.25rem 0.9rem",
  borderBottom: "1px solid rgba(115, 98, 74, 0.14)",
  background: "#f6f1e8",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  flexShrink: 0,
};

const titleRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.45rem",
  marginBottom: "0.2rem",
};

const badgeStyle = {
  fontSize: "0.7rem",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "#8c6541",
};

const spoilerBadgeStyle = {
  fontSize: "0.7rem",
  fontWeight: 600,
  color: "#2b5e3b",
  background: "#e4efe7",
  padding: "0.1rem 0.4rem",
  borderRadius: "5px",
};

const seriesTagStyle = {
  fontSize: "0.7rem",
  fontWeight: 600,
  color: "#7e5229",
  background: "#f4ebd9",
  border: "1px solid rgba(126, 82, 41, 0.2)",
  padding: "0.1rem 0.45rem",
  borderRadius: "5px",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
  maxWidth: "180px",
};

const titleStyle = {
  margin: "0 0 0.15rem",
  fontSize: "1.25rem",
  fontFamily: "Georgia, serif",
  color: "#1c1712",
};

const subtitleStyle = {
  margin: 0,
  fontSize: "0.8rem",
  color: "#73685c",
};

const headerActionsStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.4rem",
};

const clearButtonStyle = {
  background: "none",
  border: "1px solid rgba(115, 98, 74, 0.2)",
  padding: "0.25rem 0.6rem",
  borderRadius: "6px",
  fontSize: "0.75rem",
  color: "#73685c",
  cursor: "pointer",
};

const closeButtonStyle = {
  background: "none",
  border: "none",
  fontSize: "1.1rem",
  cursor: "pointer",
  color: "#73685c",
  padding: "0.25rem 0.5rem",
  borderRadius: "6px",
};

const messagesContainerStyle = {
  flex: 1,
  overflowY: "auto",
  padding: "1.25rem",
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
};

const emptyStateStyle = {
  padding: "2rem 0.5rem",
  textAlign: "center",
};

const emptyTitleStyle = {
  fontSize: "1.15rem",
  fontFamily: "Georgia, serif",
  fontWeight: 600,
  margin: "0 0 0.5rem",
  color: "#2b241e",
};

const emptyDescStyle = {
  fontSize: "0.88rem",
  lineHeight: "1.5",
  color: "#6e6255",
  margin: "0 0 1.5rem",
};

const suggestionsTitleStyle = {
  fontSize: "0.75rem",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  color: "#8c6541",
  marginBottom: "0.6rem",
  textAlign: "left",
};

const suggestionsListStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.5rem",
  textAlign: "left",
};

const suggestionPillStyle = {
  background: "#f1ede4",
  border: "1px solid rgba(115, 98, 74, 0.16)",
  borderRadius: "10px",
  padding: "0.6rem 0.85rem",
  fontSize: "0.85rem",
  color: "#3d342a",
  cursor: "pointer",
  textAlign: "left",
  lineHeight: "1.35",
  transition: "background 0.12s ease",
};

const messageRowStyle = {
  display: "flex",
  width: "100%",
};

const userBubbleStyle = {
  background: "#2e261e",
  color: "#f6f1e8",
  borderRadius: "16px 16px 4px 16px",
  padding: "0.75rem 1rem",
  maxWidth: "85%",
  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
};

const assistantBubbleStyle = {
  background: "#ede7dc",
  color: "#211d19",
  borderRadius: "16px 16px 16px 4px",
  padding: "0.85rem 1.05rem",
  maxWidth: "92%",
  boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
};

const assistantHeaderStyle = {
  display: "flex",
  alignItems: "center",
  marginBottom: "0.35rem",
};

const assistantIconStyle = {
  fontSize: "0.72rem",
  fontWeight: 700,
  color: "#8c6541",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
};

const messageTextStyle = {
  margin: 0,
  fontSize: "0.92rem",
  lineHeight: "1.55",
  whiteSpace: "pre-wrap",
};

const loadingDotsStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.35rem",
  color: "#8c6541",
};

const dotStyle = {
  fontSize: "0.75rem",
};

const loadingLabelStyle = {
  fontSize: "0.8rem",
  color: "#73685c",
  marginLeft: "0.35rem",
};

const errorBannerStyle = {
  background: "#fff0f0",
  border: "1px solid #f2c2c2",
  borderRadius: "8px",
  padding: "0.6rem 0.85rem",
  color: "#8a2424",
};

const errorTextStyle = {
  margin: 0,
  fontSize: "0.85rem",
};

const inputFormStyle = {
  padding: "0.85rem 1.25rem",
  borderTop: "1px solid rgba(115, 98, 74, 0.14)",
  background: "#f6f1e8",
  display: "flex",
  gap: "0.6rem",
  alignItems: "flex-end",
  flexShrink: 0,
};

const textareaStyle = {
  flex: 1,
  padding: "0.65rem 0.85rem",
  borderRadius: "12px",
  border: "1px solid rgba(115, 98, 74, 0.25)",
  background: "#ffffff",
  fontFamily: "inherit",
  fontSize: "0.9rem",
  lineHeight: "1.4",
  resize: "none",
  outline: "none",
};

const sendButtonStyle = {
  background: "#3e3223",
  color: "#f6f1e8",
  border: "none",
  borderRadius: "10px",
  padding: "0.65rem 1rem",
  fontSize: "0.85rem",
  fontWeight: 600,
  cursor: "pointer",
  whiteSpace: "nowrap",
  height: "40px",
};
