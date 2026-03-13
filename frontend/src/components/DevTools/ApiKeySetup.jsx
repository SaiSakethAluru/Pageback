import { useState } from "react";

export default function ApiKeySetup() {
  const [value, setValue] = useState(localStorage.getItem("dev_openai_key") || "");

  if (import.meta.env.VITE_ENV !== "development") {
    return null;
  }

  return (
    <div style={panelStyle}>
      <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
        Dev OpenAI key
      </label>
      <input
        type="password"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        style={inputStyle}
      />
      <button
        type="button"
        onClick={() => localStorage.setItem("dev_openai_key", value)}
        style={buttonStyle}
      >
        Save
      </button>
    </div>
  );
  // TODO: remove this component entirely before any public release
}

const panelStyle = {
  position: "fixed",
  top: 16,
  right: 16,
  zIndex: 1000,
  padding: "0.75rem",
  background: "rgba(255,255,255,0.95)",
  border: "1px solid #d5d1c7",
  borderRadius: 12,
  boxShadow: "0 10px 24px rgba(0,0,0,0.08)",
};

const inputStyle = {
  width: 220,
  padding: "0.5rem 0.75rem",
  borderRadius: 8,
  border: "1px solid #c7c1b3",
  marginRight: "0.5rem",
};

const buttonStyle = {
  padding: "0.5rem 0.75rem",
  borderRadius: 8,
  border: "none",
  background: "#17313e",
  color: "#fff",
};
