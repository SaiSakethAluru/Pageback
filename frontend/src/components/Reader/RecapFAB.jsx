import { useState } from "react";

import * as api from "../../services/api";
import RecapLevelIndicator from "./RecapLevelIndicator";
import RecapPanel from "./RecapPanel";

export default function RecapFAB({ bookId, userId, positionChar }) {
  const [currentLevel, setCurrentLevel] = useState(0);
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  async function handleClick() {
    const nextLevel = Math.min(currentLevel + 1 || 1, 5);
    setCurrentLevel(nextLevel);
    setIsPanelOpen(true);
    setIsLoading(true);

    try {
      const response = await api.getRecap(bookId, userId, positionChar, nextLevel);
      setSummary(response.summary);
    } finally {
      setIsLoading(false);
    }
  }

  function handleDismiss() {
    setCurrentLevel(0);
    setSummary("");
    setIsPanelOpen(false);
  }

  return (
    <>
      <button type="button" onClick={handleClick} style={fabStyle}>
        <span style={{ fontWeight: 700 }}>Recap</span>
        <RecapLevelIndicator level={currentLevel} />
      </button>
      {isPanelOpen ? (
        <RecapPanel
          summary={summary}
          isLoading={isLoading}
          level={currentLevel}
          onDismiss={handleDismiss}
        />
      ) : null}
    </>
  );
  // TODO: replace tap with swipe gesture using @use-gesture/react
}

const fabStyle = {
  position: "fixed",
  right: 24,
  bottom: 24,
  zIndex: 30,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 8,
  border: "none",
  borderRadius: 999,
  padding: "1rem 1.15rem",
  background: "#17313e",
  color: "#fff",
  boxShadow: "0 16px 32px rgba(23,49,62,0.28)",
};
