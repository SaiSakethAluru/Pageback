import { useNavigate } from "react-router-dom";

export default function BookCard({ book }) {
  const navigate = useNavigate();
  const isReady = book.ingestion_status === "complete";

  return (
    <button
      type="button"
      onClick={() => {
        if (isReady) {
          navigate(`/reader/${book.id}`);
        }
      }}
      disabled={!isReady}
      style={{
        ...cardStyle,
        opacity: isReady ? 1 : 0.6,
        cursor: isReady ? "pointer" : "not-allowed",
      }}
    >
      <div style={badgeStyle(book.ingestion_status)}>{labelForStatus(book.ingestion_status)}</div>
      <h3 style={{ margin: "0 0 0.5rem" }}>{book.title || "Untitled book"}</h3>
      <p style={{ margin: 0, color: "#646261" }}>{book.author || "Unknown author"}</p>
    </button>
  );
}

function labelForStatus(status) {
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
