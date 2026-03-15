import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import * as api from "../../services/api";

export default function AuthGuard({ children }) {
  const [user, setUser] = useState(undefined);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .getCurrentUser()
      .then(({ user: nextUser }) => setUser(nextUser))
      .catch(() => {
        setUser(null);
        navigate("/login", { replace: true });
      });
  }, [navigate]);

  if (user === undefined) {
    return <div style={spinnerWrapStyle}>Loading...</div>;
  }

  if (!user) {
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
