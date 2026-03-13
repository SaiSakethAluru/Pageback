export default function RecapPanel({ summary, isLoading, level, onDismiss }) {
  return (
    <>
      <div style={backdropStyle} onClick={onDismiss} />
      <section style={panelStyle}>
        <button type="button" onClick={onDismiss} style={closeStyle}>
          X
        </button>
        <p style={{ marginTop: 0, color: "#7c7269" }}>Recap level {level}</p>
        {isLoading ? <p>Generating recap...</p> : <p style={summaryStyle}>{summary}</p>}
      </section>
    </>
  );
}

const backdropStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(17, 24, 39, 0.3)",
  zIndex: 40,
};

const panelStyle = {
  position: "fixed",
  left: 0,
  right: 0,
  bottom: 0,
  zIndex: 41,
  background: "#fffaf0",
  borderTopLeftRadius: 24,
  borderTopRightRadius: 24,
  padding: "1.5rem",
  minHeight: 220,
  boxShadow: "0 -20px 50px rgba(0,0,0,0.15)",
  transform: "translateY(0)",
  transition: "transform 200ms ease",
};

const closeStyle = {
  position: "absolute",
  top: 16,
  right: 16,
  border: "none",
  background: "transparent",
  fontSize: "1rem",
};

const summaryStyle = {
  marginTop: "1.25rem",
  fontSize: "1rem",
  lineHeight: 1.7,
  whiteSpace: "pre-wrap",
};
