import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import * as api from "../../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getCurrentUser()
      .then(() => {
        navigate("/library", { replace: true });
      })
      .catch(() => {});
  }, [navigate]);

  useEffect(() => {
    const authError = searchParams.get("error");
    if (authError) {
      setError("Google sign-in failed. Please try again.");
    }
  }, [searchParams]);

  function handleLogin() {
    window.location.href = api.getGoogleLoginUrl();
  }

  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <div style={{ marginBottom: "1.5rem" }}>
          <h1 style={{ margin: 0 }}>PageBack</h1>
          <p style={{ margin: "0.5rem 0 0", color: "#5d6663" }}>
            Recaps that stay behind your current page.
          </p>
        </div>
        <button type="button" onClick={handleLogin} style={buttonStyle}>
          Continue with Google
        </button>
        {error ? <p style={errorStyle}>{error}</p> : null}
      </div>
    </div>
  );
}

const pageStyle = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  background:
    "radial-gradient(circle at top, #f3e8d3 0%, #efe4d6 30%, #e3ddd0 100%)",
  padding: "2rem",
};

const cardStyle = {
  width: "min(100%, 420px)",
  padding: "2rem",
  background: "rgba(255,255,255,0.95)",
  borderRadius: 24,
  boxShadow: "0 24px 60px rgba(41,37,36,0.12)",
};

const buttonStyle = {
  width: "100%",
  border: "none",
  borderRadius: 999,
  padding: "0.9rem 1.1rem",
  background: "#17313e",
  color: "#fff",
  fontWeight: 600,
  fontSize: "1rem",
};

const errorStyle = {
  margin: "0.75rem 0 0",
  color: "#a11d1d",
};
