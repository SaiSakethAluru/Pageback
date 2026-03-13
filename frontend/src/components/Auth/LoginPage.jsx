import { useEffect } from "react";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { useNavigate } from "react-router-dom";

import supabase from "../../services/supabaseClient";

export default function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        navigate("/library", { replace: true });
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        navigate("/library", { replace: true });
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <div style={{ marginBottom: "1.5rem" }}>
          <h1 style={{ margin: 0 }}>PageBack</h1>
          <p style={{ margin: "0.5rem 0 0", color: "#5d6663" }}>
            Recaps that stay behind your current page.
          </p>
        </div>
        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={["google"]}
        />
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
