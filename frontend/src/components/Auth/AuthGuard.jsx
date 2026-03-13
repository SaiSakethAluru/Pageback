import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import supabase from "../../services/supabaseClient";

export default function AuthGuard({ children }) {
  const [session, setSession] = useState(undefined);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      if (!nextSession) {
        navigate("/login", { replace: true });
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  if (session === undefined) {
    return <div style={spinnerWrapStyle}>Loading...</div>;
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

const spinnerWrapStyle = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  fontSize: "1.1rem",
};
