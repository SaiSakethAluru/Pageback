import { useState } from "react";

import { useNavigate } from "react-router-dom";

import * as api from "../../services/api";

export default function BookCard({ book }) {
  const navigate = useNavigate();
  const isAIComplete = book.ingestion_status === "complete";
  const [isStartingAI, setIsStartingAI] = useState(false);
  const modelLine =
    book.llm && book.llm.provider
      ? `${book.llm.provider} | recap: ${book.llm.recap_model} | embed: ${book.llm.embedding_model}`
      : "";
  const progressLine =
    typeof book.ingestion_progress === "number" ? `${book.ingestion_progress}%` : "";
  const stepLine = book.ingestion_step || "";
  const errorLine = book.ingestion_error || "";

  async function startAI(background) {
    setIsStartingAI(true);
    try {
      await api.startIngestion(book.id, { background });
    } finally {
      setIsStartingAI(false);
    }
  }

  return (
    <div style={cardStyle}>
      <div style={badgeStyle(book.ingestion_status)}>{labelForStatus(book.ingestion_status)}</div>
      <h3 style={{ margin: "0 0 0.5rem" }}>{book.title || "Untitled book"}</h3>
      <p style={{ margin: 0, color: "#646261" }}>{book.author || "Unknown author"}</p>
      <div style={actionsStyle}>
        <button type="button" onClick={() => navigate(`/reader/${book.id}`)} style={readButtonStyle}>
          Read
        </button>
        {!isAIComplete ? (
          <div style={aiButtonsStyle}>
            {modelLine ? <p style={modelLineStyle}>Using: {modelLine}</p> : null}
            {progressLine ? <p style={progressLineStyle}>Progress: {progressLine}</p> : null}
            {stepLine ? <p style={stepLineStyle}>{stepLine}</p> : null}
            {errorLine ? <p style={errorLineStyle}>Error: {errorLine}</p> : null}
            <button
              type="button"
              disabled={isStartingAI}
              onClick={() => startAI(true)}
              style={aiButtonStyle}
            >
              Enable AI (background)
            </button>
            <button
              type="button"
              disabled={isStartingAI}
              onClick={() => startAI(false)}
              style={aiButtonStyle}
            >
              Enable AI (now)
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function labelForStatus(status) {
  if (status === "ready") {
    return "Ready";
  }
  if (status === "complete") {
    return "Complete";
  }
  if (status === "failed") {
    return "Failed";
  }
  return "Processing";
}

const cardStyle = {
  position: "relative",
  textAlign: "left",
  padding: "1.25rem",
  borderRadius: 18,
  border: "1px solid #ddd3c1",
  background: "#fffdf8",
  minHeight: 160,
};

const badgeStyle = (status) => ({
  display: "inline-block",
  marginBottom: "1rem",
  padding: "0.25rem 0.6rem",
  borderRadius: 999,
  background:
    status === "complete" ? "#d8f1df" : status === "failed" ? "#f8d7d7" : "#f3ebd7",
  color: "#2e3b39",
  fontSize: "0.8rem",
});

const actionsStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "0.75rem",
  marginTop: "1rem",
};

const readButtonStyle = {
  border: "1px solid #c9beae",
  borderRadius: 999,
  padding: "0.6rem 0.9rem",
  background: "#fff8ef",
  color: "#17313e",
  fontWeight: 700,
};

const aiButtonsStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
};

const modelLineStyle = {
  margin: 0,
  fontSize: "0.72rem",
  color: "#6d645a",
  lineHeight: 1.25,
};

const progressLineStyle = {
  margin: 0,
  fontSize: "0.72rem",
  color: "#6d645a",
  lineHeight: 1.25,
};

const stepLineStyle = {
  margin: 0,
  fontSize: "0.72rem",
  color: "#6d645a",
  lineHeight: 1.25,
  maxWidth: 240,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const errorLineStyle = {
  margin: 0,
  fontSize: "0.72rem",
  color: "#a11d1d",
  lineHeight: 1.25,
  maxWidth: 240,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const aiButtonStyle = {
  border: "none",
  borderRadius: 999,
  padding: "0.55rem 0.85rem",
  background: "#17313e",
  color: "#fff",
  fontWeight: 700,
  fontSize: "0.8rem",
};
