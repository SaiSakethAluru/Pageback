import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import appIcon from "../../assets/icons/pageback-book.svg";
import * as api from "../../services/api";

export default function SettingsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyRequestId, setBusyRequestId] = useState(null);

  async function loadRequests() {
    setError("");
    const response = await api.getIngestionRequests();
    setRequests(response);
  }

  useEffect(() => {
    let isMounted = true;
    async function load() {
      try {
        const response = await api.getIngestionRequests();
        if (isMounted) {
          setRequests(response);
          setLoading(false);
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError.message);
          setLoading(false);
        }
      }
    }
    load();
    const interval = window.setInterval(() => {
      loadRequests().catch((requestError) => setError(requestError.message));
    }, 5000);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, []);

  async function handlePause(requestId) {
    await runAction(requestId, () => api.pauseIngestion(requestId));
  }

  async function handleResume(requestId) {
    await runAction(requestId, () => api.resumeIngestion(requestId));
  }

  async function handleCancel(requestId) {
    const confirmed = window.confirm(
      "Cancel this ingestion and delete all embeddings already stored for this book? This cannot be undone."
    );
    if (!confirmed) {
      return;
    }
    await runAction(requestId, () => api.cancelIngestion(requestId));
  }

  async function runAction(requestId, action) {
    setBusyRequestId(requestId);
    setError("");
    try {
      await action();
      await loadRequests();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyRequestId(null);
    }
  }

  return (
    <div style={pageStyle}>
      <header style={navBarStyle}>
        <Link to="/library" style={brandStyle} aria-label="Back to PageBack library">
          <img src={appIcon} alt="" style={brandIconStyle} />
          <span>PageBack</span>
        </Link>
      </header>
      <main style={contentStyle}>
        <h1 style={{ margin: 0 }}>Settings</h1>
        <section style={sectionStyle}>
          <div>
            <h2 style={sectionTitleStyle}>Ingestion queue</h2>
            <p style={sectionCopyStyle}>
              Pause work to keep already embedded chunks, resume later from the last stored chunk, or cancel to delete
              partial embeddings for that book.
            </p>
          </div>
          {error ? <p style={errorStyle}>{error}</p> : null}
          {loading ? <p style={mutedStyle}>Loading ingestion requests...</p> : null}
          {!loading && requests.length === 0 ? (
            <p style={emptyStyle}>No active ingestion requests right now.</p>
          ) : null}
          {!loading && requests.length > 0 ? (
            <div style={requestListStyle}>
              {requests.map((request) => (
                <IngestionRequestCard
                  key={request.id}
                  request={request}
                  isBusy={busyRequestId === request.id}
                  onPause={handlePause}
                  onResume={handleResume}
                  onCancel={handleCancel}
                />
              ))}
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}

function IngestionRequestCard({ request, isBusy, onPause, onResume, onCancel }) {
  const progress = request.progress ?? progressFromCounts(request.embedded_chunks, request.total_chunks);
  const embeddedChunks = request.embedded_chunks ?? 0;
  const totalChunks = request.total_chunks ?? 0;
  const embeddedTokens = request.embedded_tokens ?? 0;
  const totalTokens = request.total_tokens ?? 0;
  const isPaused = request.status === "paused" || request.control_status === "paused";
  const canPause = request.status === "processing" || request.status === "queued";
  const canResume = isPaused || request.status === "failed";

  return (
    <article style={requestCardStyle}>
      <div style={requestHeaderStyle}>
        <div>
          <h3 style={requestTitleStyle}>{request.book_title || "Untitled book"}</h3>
          <p style={requestMetaStyle}>{request.status} - {request.step || "waiting"}</p>
        </div>
        <span style={statusPillStyle}>{progress ?? 0}%</span>
      </div>
      <div style={progressTrackStyle}>
        <div style={{ ...progressFillStyle, width: `${Math.max(0, Math.min(progress ?? 0, 100))}%` }} />
      </div>
      <p style={requestMetaStyle}>
        {embeddedChunks}/{totalChunks || "?"} chunks embedded
        {totalTokens ? ` - ${embeddedTokens}/${totalTokens} tokens` : ""}
      </p>
      {request.error_message ? <p style={errorStyle}>{request.error_message}</p> : null}
      <div style={actionRowStyle}>
        {canPause ? (
          <button type="button" disabled={isBusy} style={secondaryButtonStyle} onClick={() => onPause(request.id)}>
            Pause
          </button>
        ) : null}
        {canResume ? (
          <button type="button" disabled={isBusy} style={primaryButtonStyle} onClick={() => onResume(request.id)}>
            Resume
          </button>
        ) : null}
        <button type="button" disabled={isBusy} style={dangerButtonStyle} onClick={() => onCancel(request.id)}>
          Cancel
        </button>
      </div>
    </article>
  );
}

function progressFromCounts(embeddedChunks, totalChunks) {
  if (!totalChunks) {
    return 0;
  }
  return Math.round((embeddedChunks / totalChunks) * 100);
}

const pageStyle = {
  minHeight: "100vh",
  padding: "0 0 2rem",
  background:
    "radial-gradient(circle at top, rgba(255,255,255,0.5), transparent 32%), linear-gradient(180deg, #f6f0e4 0%, #eee1cd 100%)",
  cursor: "default",
  caretColor: "transparent",
};

const navBarStyle = {
  minHeight: 64,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0 2rem",
  marginBottom: "2rem",
  background: "rgba(255, 250, 243, 0.92)",
  borderBottom: "1px solid rgba(115, 98, 74, 0.16)",
  boxShadow: "0 12px 32px rgba(44, 33, 20, 0.08)",
  position: "sticky",
  top: 0,
  zIndex: 10,
  backdropFilter: "blur(14px)",
};

const brandStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "0.7rem",
  color: "#17313e",
  textDecoration: "none",
  fontSize: "1.2rem",
  fontWeight: 800,
};

const brandIconStyle = {
  width: 38,
  height: 38,
  borderRadius: 12,
};

const contentStyle = {
  maxWidth: 960,
  margin: "0 auto",
  padding: "2rem",
  borderRadius: 28,
  background: "rgba(255, 250, 243, 0.72)",
  boxShadow: "0 22px 50px rgba(44, 33, 20, 0.08)",
};

const sectionStyle = {
  marginTop: "1.5rem",
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
};

const sectionTitleStyle = {
  margin: 0,
  color: "#17313e",
};

const sectionCopyStyle = {
  margin: "0.45rem 0 0",
  color: "#69645e",
  lineHeight: 1.55,
};

const mutedStyle = {
  color: "#69645e",
};

const emptyStyle = {
  padding: "1rem",
  borderRadius: 18,
  background: "rgba(255, 248, 239, 0.82)",
  color: "#69645e",
};

const errorStyle = {
  margin: 0,
  color: "#a11d1d",
  fontWeight: 700,
};

const requestListStyle = {
  display: "grid",
  gap: "1rem",
};

const requestCardStyle = {
  padding: "1.1rem",
  borderRadius: 22,
  background: "#fff8ef",
  border: "1px solid rgba(115, 98, 74, 0.16)",
  boxShadow: "0 16px 32px rgba(44, 33, 20, 0.08)",
};

const requestHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: "1rem",
  alignItems: "flex-start",
};

const requestTitleStyle = {
  margin: 0,
  color: "#17313e",
};

const requestMetaStyle = {
  margin: "0.45rem 0 0",
  color: "#69645e",
  fontSize: "0.94rem",
};

const statusPillStyle = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  padding: "0.35rem 0.7rem",
  background: "#17313e",
  color: "#fff8ef",
  fontWeight: 800,
};

const progressTrackStyle = {
  height: 10,
  marginTop: "1rem",
  overflow: "hidden",
  borderRadius: 999,
  background: "rgba(23, 49, 62, 0.12)",
};

const progressFillStyle = {
  height: "100%",
  borderRadius: 999,
  background: "linear-gradient(90deg, #d9b77f, #17313e)",
};

const actionRowStyle = {
  display: "flex",
  gap: "0.6rem",
  flexWrap: "wrap",
  marginTop: "1rem",
};

const baseButtonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.65rem 0.95rem",
  fontWeight: 800,
  cursor: "pointer",
};

const primaryButtonStyle = {
  ...baseButtonStyle,
  background: "#17313e",
  color: "#fff8ef",
};

const secondaryButtonStyle = {
  ...baseButtonStyle,
  background: "#ead8bd",
  color: "#17313e",
};

const dangerButtonStyle = {
  ...baseButtonStyle,
  background: "#f6d5ce",
  color: "#a11d1d",
};
