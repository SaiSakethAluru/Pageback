import { Link } from "react-router-dom";

import appIcon from "../../assets/icons/pageback-book.svg";

export default function SettingsPage() {
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
        <p style={todoStyle}>TODO</p>
      </main>
    </div>
  );
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
  maxWidth: 760,
  margin: "0 2rem",
  padding: "2rem",
  borderRadius: 28,
  background: "rgba(255, 250, 243, 0.72)",
  boxShadow: "0 22px 50px rgba(44, 33, 20, 0.08)",
};

const todoStyle = {
  margin: "1rem 0 0",
  color: "#69645e",
};
