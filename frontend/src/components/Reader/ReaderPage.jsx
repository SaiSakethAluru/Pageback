import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getReaderType } from "../../readers/BookReaderFactory";
import EpubReader from "../../readers/EpubReader";
import PdfReader from "../../readers/PdfReader";
import * as api from "../../services/api";
import RecapFAB from "./RecapFAB";

export default function ReaderPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const readerRef = useRef(null);
  const saveTimerRef = useRef(null);
  const [bookUrl, setBookUrl] = useState("");
  const [initialCfi, setInitialCfi] = useState(null);
  const [currentCfi, setCurrentCfi] = useState(null);
  const [currentChar, setCurrentChar] = useState(0);
  const [isStartingAI, setIsStartingAI] = useState(false);
  const [ingestion, setIngestion] = useState({
    status: "ready",
    progress: null,
    step: "",
    error: "",
    llm: null,
  });

  useEffect(() => {
    async function load() {
      const [fileUrl, position, ingestionStatus] = await Promise.all([
        api.getBookFileUrl(bookId),
        api.getPosition(bookId),
        api.getBookStatus(bookId),
      ]);
      setBookUrl(fileUrl.signed_url || "");

      setInitialCfi(position.position_cfi);
      setCurrentCfi(position.position_cfi);
      setCurrentChar(position.position_char || 0);
      setIngestion({
        status: ingestionStatus.status || ingestionStatus.ingestion_status || "ready",
        progress: ingestionStatus.progress ?? null,
        step: ingestionStatus.step || "",
        error: ingestionStatus.error || "",
        llm: ingestionStatus.llm || null,
      });
    }

    load();
    return () => {
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
    };
  }, [bookId]);

  useEffect(() => {
    let intervalId = null;
    async function refreshIngestion() {
      const ingestionStatus = await api.getBookStatus(bookId);
      setIngestion({
        status: ingestionStatus.status || ingestionStatus.ingestion_status || "ready",
        progress: ingestionStatus.progress ?? null,
        step: ingestionStatus.step || "",
        error: ingestionStatus.error || "",
        llm: ingestionStatus.llm || null,
      });
    }

    if (ingestion.status === "processing") {
      intervalId = window.setInterval(() => {
        refreshIngestion().catch(() => {});
      }, 2000);
    }

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [bookId, ingestion.status]);

  function handlePositionChange(cfi, charOffset) {
    setCurrentCfi(cfi);
    setCurrentChar(charOffset);
    if (saveTimerRef.current) {
      window.clearTimeout(saveTimerRef.current);
    }
    saveTimerRef.current = window.setTimeout(() => {
      api.savePosition(bookId, cfi, charOffset).catch(() => {});
    }, 2000);
  }

  const readerType = getReaderType("original.epub");
  const ReaderComponent = readerType === "pdf" ? PdfReader : EpubReader;

  async function startAI(background) {
    setIsStartingAI(true);
    try {
      await api.startIngestion(bookId, { background });
      const ingestionStatus = await api.getBookStatus(bookId);
      setIngestion({
        status: ingestionStatus.status || ingestionStatus.ingestion_status || "ready",
        progress: ingestionStatus.progress ?? null,
        step: ingestionStatus.step || "",
        error: ingestionStatus.error || "",
        llm: ingestionStatus.llm || null,
      });
    } finally {
      setIsStartingAI(false);
    }
  }

  const isAIComplete = ingestion.status === "complete";
  const modelLine =
    ingestion.llm && ingestion.llm.provider
      ? `${ingestion.llm.provider} | recap: ${ingestion.llm.recap_model} | embed: ${ingestion.llm.embedding_model}`
      : "";

  function goToPreviousPage() {
    readerRef.current?.prev?.();
  }

  function goToNextPage() {
    readerRef.current?.next?.();
  }

  return (
    <div style={readerPageStyle}>
      <button type="button" onClick={() => navigate("/library")} style={backStyle}>
        Back
      </button>

      <section style={aiPanelStyle}>
        <p style={{ margin: 0, fontWeight: 800 }}>
          {isAIComplete ? "AI processing complete" : "AI processing (opt-in)"}
        </p>
        {modelLine ? <p style={{ margin: "0.5rem 0 0", color: "#6d645a" }}>Using: {modelLine}</p> : null}

        {!isAIComplete ? (
          <>
            <div style={progressRowStyle}>
              <p style={{ margin: 0 }}>
                Status: <span style={{ fontWeight: 700 }}>{ingestion.status}</span>
              </p>
              {typeof ingestion.progress === "number" ? (
                <p style={{ margin: 0, fontWeight: 700 }}>{ingestion.progress}%</p>
              ) : null}
            </div>
            {ingestion.step ? <p style={{ margin: "0.4rem 0 0", color: "#6d645a" }}>{ingestion.step}</p> : null}
            {ingestion.error ? (
              <p style={{ margin: "0.4rem 0 0", color: "#a11d1d" }}>Error: {ingestion.error}</p>
            ) : null}

            <div style={aiButtonsStyle}>
              <button
                type="button"
                onClick={() => startAI(true)}
                disabled={isStartingAI}
                style={aiButtonStyle}
              >
                Enable AI (background)
              </button>
              <button
                type="button"
                onClick={() => startAI(false)}
                disabled={isStartingAI}
                style={aiButtonStyle}
              >
                Enable AI (now)
              </button>
            </div>
            <p style={{ margin: "0.7rem 0 0", color: "#6d645a" }}>
              Recaps unlock when AI processing finishes.
            </p>
          </>
        ) : null}
      </section>

      <div style={readerShellStyle}>
        <button type="button" onClick={goToPreviousPage} style={navButtonLeftStyle}>
          Previous
        </button>
        <ReaderComponent
          ref={readerRef}
          bookUrl={bookUrl}
          initialCfi={initialCfi}
          onPositionChange={handlePositionChange}
        />
        <button type="button" onClick={goToNextPage} style={navButtonRightStyle}>
          Next
        </button>
      </div>
      <RecapFAB bookId={bookId} positionChar={currentChar} isAIComplete={isAIComplete} />
    </div>
  );
}

const readerPageStyle = {
  minHeight: "100vh",
  background: "#ddd4c2",
  padding: "1rem",
};

const backStyle = {
  border: "none",
  background: "#fff6e8",
  borderRadius: 999,
  padding: "0.65rem 1rem",
  marginBottom: "1rem",
};

const aiPanelStyle = {
  background: "#fffaf0",
  border: "1px solid #e7dcc7",
  borderRadius: 16,
  padding: "0.9rem 1rem",
  marginBottom: "1rem",
};

const progressRowStyle = {
  display: "flex",
  alignItems: "baseline",
  justifyContent: "space-between",
  gap: "1rem",
  marginTop: "0.7rem",
};

const aiButtonsStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  marginTop: "0.8rem",
};

const aiButtonStyle = {
  border: "none",
  borderRadius: 12,
  padding: "0.65rem 0.9rem",
  background: "#17313e",
  color: "#fff",
  fontWeight: 800,
};

const readerShellStyle = {
  position: "relative",
  height: "calc(100vh - 96px)",
  background: "#fffaf0",
  borderRadius: 24,
  overflow: "hidden",
  boxShadow: "0 24px 60px rgba(0,0,0,0.12)",
};

const navButtonBaseStyle = {
  position: "absolute",
  top: "50%",
  transform: "translateY(-50%)",
  zIndex: 2,
  border: "none",
  borderRadius: 999,
  padding: "0.8rem 1rem",
  background: "rgba(23, 49, 62, 0.88)",
  color: "#fff",
  fontWeight: 700,
  cursor: "pointer",
};

const navButtonLeftStyle = {
  ...navButtonBaseStyle,
  left: "1rem",
};

const navButtonRightStyle = {
  ...navButtonBaseStyle,
  right: "1rem",
};
