import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getReaderType } from "../../readers/BookReaderFactory";
import EpubReader from "../../readers/EpubReader";
import PdfReader from "../../readers/PdfReader";
import * as api from "../../services/api";
import RecapLevelIndicator from "./RecapLevelIndicator";
import RecapPanel from "./RecapPanel";

const ORIENTATION_OPTIONS = [
  { value: "horizontal-spread", label: "Horizontal 2-page" },
  { value: "horizontal-single", label: "Horizontal single" },
  { value: "vertical-single", label: "Vertical single" },
  { value: "vertical-continuous", label: "Vertical continuous" },
];

const FONT_OPTIONS = [
  { label: "Georgia", value: "Georgia, serif" },
  { label: "Palatino", value: "'Palatino Linotype', Palatino, serif" },
  { label: "Baskerville", value: "Baskerville, 'Times New Roman', serif" },
  { label: "Iowan", value: "'Iowan Old Style', Georgia, serif" },
  { label: "Athelas", value: "Athelas, Georgia, serif" },
  { label: "Serif Sans", value: "system-ui, sans-serif" },
];

const FONT_SCALE_OPTIONS = [85, 95, 100, 110, 120, 135];

export default function ReaderPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const readerRef = useRef(null);
  const saveTimerRef = useRef(null);
  const hudTimerRef = useRef(null);
  const [bookUrl, setBookUrl] = useState("");
  const [initialCfi, setInitialCfi] = useState(null);
  const [currentChar, setCurrentChar] = useState(0);
  const [isReaderLoading, setIsReaderLoading] = useState(true);
  const [isReaderReady, setIsReaderReady] = useState(false);
  const [isStartingAI, setIsStartingAI] = useState(false);
  const [aiDialogOpen, setAIDialogOpen] = useState(false);
  const [recapDialogOpen, setRecapDialogOpen] = useState(false);
  const [fontDialogOpen, setFontDialogOpen] = useState(false);
  const [layoutDialogOpen, setLayoutDialogOpen] = useState(false);
  const [hudVisible, setHudVisible] = useState(true);
  const [startInBackground, setStartInBackground] = useState(true);
  const [layoutMode, setLayoutMode] = useState("horizontal-spread");
  const [fontScale, setFontScale] = useState(100);
  const [fontFamily, setFontFamily] = useState(FONT_OPTIONS[0].value);
  const [pageInput, setPageInput] = useState("1");
  const [readerState, setReaderState] = useState({
    currentPage: null,
    totalPages: null,
    canGoPrevious: false,
    canGoNext: false,
  });
  const [currentLevel, setCurrentLevel] = useState(0);
  const [summary, setSummary] = useState("");
  const [isRecapLoading, setIsRecapLoading] = useState(false);
  const [isRecapPanelOpen, setIsRecapPanelOpen] = useState(false);
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
      setCurrentChar(position.position_char || 0);
      setIsReaderLoading(true);
      setIsReaderReady(false);
      setIngestion({
        status: ingestionStatus.status || ingestionStatus.ingestion_status || "ready",
        progress: ingestionStatus.progress ?? null,
        step: ingestionStatus.step || "",
        error: ingestionStatus.error || "",
        llm: ingestionStatus.llm || null,
      });
    }

    load().catch(() => {});
    return () => {
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
      if (hudTimerRef.current) {
        window.clearTimeout(hudTimerRef.current);
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

  useEffect(() => {
    if (readerState.currentPage) {
      setPageInput(String(readerState.currentPage));
    }
  }, [readerState.currentPage]);

  useEffect(() => {
    if (!isReaderReady) {
      setHudVisible(false);
      return;
    }

    if (aiDialogOpen || recapDialogOpen || fontDialogOpen || layoutDialogOpen || isRecapPanelOpen) {
      setHudVisible(true);
      if (hudTimerRef.current) {
        window.clearTimeout(hudTimerRef.current);
      }
      return;
    }

    if (hudTimerRef.current) {
      window.clearTimeout(hudTimerRef.current);
    }
    hudTimerRef.current = window.setTimeout(() => {
      setHudVisible(false);
    }, 2600);

    return () => {
      if (hudTimerRef.current) {
        window.clearTimeout(hudTimerRef.current);
      }
    };
  }, [aiDialogOpen, fontDialogOpen, isReaderReady, isRecapPanelOpen, layoutDialogOpen, recapDialogOpen, readerState.currentPage]);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        readerRef.current?.clearFocus?.();
        document.activeElement?.blur?.();
        return;
      }

      if (!isReaderReady) {
        return;
      }

      const tagName = event.target?.tagName;
      if (tagName === "INPUT" || tagName === "TEXTAREA") {
        return;
      }

      if (layoutMode.startsWith("horizontal")) {
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          readerRef.current?.prev?.();
        }
        if (event.key === "ArrowRight") {
          event.preventDefault();
          readerRef.current?.next?.();
        }
        return;
      }

      if (event.key === "ArrowUp") {
        event.preventDefault();
        readerRef.current?.prev?.();
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        readerRef.current?.next?.();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isReaderReady, layoutMode]);

  function revealHud() {
    if (!isReaderReady) {
      return;
    }
    setHudVisible(true);
    if (hudTimerRef.current) {
      window.clearTimeout(hudTimerRef.current);
    }
    hudTimerRef.current = window.setTimeout(() => {
      setHudVisible(false);
    }, 2600);
  }

  function closeTransientPanels() {
    setAIDialogOpen(false);
    setRecapDialogOpen(false);
    setFontDialogOpen(false);
    setLayoutDialogOpen(false);
  }

  function handlePositionChange(cfi, charOffset) {
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
  const isAIComplete = ingestion.status === "complete";
  const aiStatusLabel = getAIStatusLabel(ingestion.status);
  const aiStatusDescription = getAIStatusDescription(ingestion.status);

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
      setAIDialogOpen(false);
      revealHud();
    } finally {
      setIsStartingAI(false);
    }
  }

  async function handleGoToPage() {
    const pageNumber = Number(pageInput);
    if (!Number.isFinite(pageNumber)) {
      setPageInput(String(readerState.currentPage || ""));
      return;
    }

    const moved = await readerRef.current?.goToPage?.(pageNumber);
    if (!moved) {
      const boundedPage = Math.min(Math.max(1, Math.round(pageNumber)), readerState.totalPages);
      setPageInput(String(boundedPage));
    }
  }

  async function handleRecapRequest(level) {
    if (!isAIComplete) {
      return;
    }

    setCurrentLevel(level);
    setIsRecapPanelOpen(true);
    setIsRecapLoading(true);
    setRecapDialogOpen(false);

    try {
      const response = await api.getRecap(bookId, currentChar, level);
      setSummary(response.summary);
    } finally {
      setIsRecapLoading(false);
      revealHud();
    }
  }

  function handleDismissRecap() {
    setCurrentLevel(0);
    setSummary("");
    setIsRecapPanelOpen(false);
  }

  return (
    <div
      style={readerPageStyle}
      onMouseMove={revealHud}
      onTouchStart={revealHud}
      onClick={() => {
        closeTransientPanels();
        revealHud();
      }}
    >
      <button
        type="button"
        onClick={() => navigate("/library")}
        style={{
          ...backStyle,
          opacity: hudVisible && isReaderReady ? 1 : 0,
          pointerEvents: hudVisible && isReaderReady ? "auto" : "none",
        }}
      >
        <BackIcon />
      </button>

      <div style={readerShellStyle}>
        {isReaderLoading ? (
          <div style={loadingOverlayStyle}>
            <p style={loadingTitleStyle}>Opening book...</p>
          </div>
        ) : null}

        {isReaderReady && layoutMode.startsWith("horizontal") ? (
          <>
            <button
              type="button"
              onClick={() => readerRef.current?.prev?.()}
              style={{ ...edgeTurnZoneStyle, left: 0 }}
              aria-label="Previous page"
            />
            <button
              type="button"
              onClick={() => readerRef.current?.next?.()}
              style={{ ...edgeTurnZoneStyle, right: 0 }}
              aria-label="Next page"
            />
          </>
        ) : null}

        <ReaderComponent
          ref={readerRef}
          bookUrl={bookUrl}
          initialCfi={initialCfi}
          onPositionChange={handlePositionChange}
          onReaderStateChange={setReaderState}
          onLoadingChange={setIsReaderLoading}
          onReadyChange={setIsReaderReady}
          layoutMode={layoutMode}
          fontScale={fontScale}
          fontFamily={fontFamily}
        />
      </div>

      <div
        style={bottomRevealStripStyle}
        onMouseEnter={revealHud}
        onMouseMove={revealHud}
      />

      <div
        style={{
          ...hudBarWrapStyle,
          transform: hudVisible && isReaderReady ? "translate(-50%, 0)" : "translate(-50%, 130%)",
          opacity: hudVisible && isReaderReady ? 1 : 0,
          pointerEvents: hudVisible && isReaderReady ? "auto" : "none",
        }}
        onMouseEnter={revealHud}
        onClick={(event) => event.stopPropagation()}
      >
        <div style={hudBarStyle}>
          <div style={groupStyle}>
            <button
              type="button"
              onClick={() => navigate("/library")}
              style={secondaryIconButtonStyle}
              aria-label="Back to library"
            >
              <BackIcon />
            </button>
            <button
              type="button"
              onClick={() => {
                closeTransientPanels();
                setLayoutDialogOpen((open) => !open);
              }}
              style={secondaryIconButtonStyle}
              aria-label="Change reading orientation"
            >
              <LayoutIcon />
            </button>
            <button
              type="button"
              onClick={() => {
                closeTransientPanels();
                setFontDialogOpen((open) => !open);
              }}
              style={secondaryIconButtonStyle}
              aria-label="Open typography settings"
            >
              <TypeIcon />
            </button>
          </div>

          <div style={groupStyle}>
            <button
              type="button"
              onClick={() => readerRef.current?.prev?.()}
              disabled={!readerState.canGoPrevious}
              style={navIconButtonStyle}
              aria-label="Previous page"
            >
              <ChevronLeftIcon />
            </button>
            <form
              style={pageControlStyle}
              onSubmit={(event) => {
                event.preventDefault();
                handleGoToPage().catch(() => {});
              }}
            >
              {readerState.totalPages ? (
                <>
                  <input
                    value={pageInput}
                    onChange={(event) => setPageInput(event.target.value.replace(/[^\d]/g, ""))}
                    onBlur={() => {
                      handleGoToPage().catch(() => {});
                    }}
                    inputMode="numeric"
                    style={pageInputStyle}
                    aria-label="Current page"
                  />
                  <span style={pageTotalStyle}>/ {readerState.totalPages}</span>
                </>
              ) : (
                <span style={pageTotalStyle}>Page map loading...</span>
              )}
            </form>
            <button
              type="button"
              onClick={() => readerRef.current?.next?.()}
              disabled={!readerState.canGoNext}
              style={navIconButtonStyle}
              aria-label="Next page"
            >
              <ChevronRightIcon />
            </button>
          </div>

          <div style={groupStyle}>
            <button
              type="button"
              onClick={() => {
                closeTransientPanels();
                setRecapDialogOpen((open) => !open);
              }}
              style={{
                ...iconButtonStyle,
                ...(isAIComplete ? null : disabledIconButtonStyle),
              }}
              disabled={!isAIComplete}
              aria-label="Open recap options"
            >
              <BrainIcon />
            </button>
            <button
              type="button"
              onClick={() => {
                closeTransientPanels();
                setAIDialogOpen((open) => !open);
              }}
              style={iconButtonStyle}
              aria-label="Open AI processing options"
            >
              <SparkIcon />
            </button>
          </div>
        </div>

        {layoutDialogOpen ? (
          <section style={{ ...popoverStyle, ...layoutPopoverStyle }}>
            <div style={popoverHeaderStyle}>
              <p style={popoverTitleStyle}>Reading mode</p>
              <button type="button" onClick={() => setLayoutDialogOpen(false)} style={closePopoverButtonStyle}>
                <CloseIcon />
              </button>
            </div>
            <div style={optionListStyle}>
              {ORIENTATION_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    setLayoutMode(option.value);
                    setLayoutDialogOpen(false);
                    revealHud();
                  }}
                  style={{
                    ...optionButtonStyle,
                    ...(layoutMode === option.value ? selectedOptionButtonStyle : null),
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {fontDialogOpen ? (
          <section style={{ ...popoverStyle, ...fontPopoverStyle }}>
            <div style={popoverHeaderStyle}>
              <p style={popoverTitleStyle}>Text appearance</p>
              <button type="button" onClick={() => setFontDialogOpen(false)} style={closePopoverButtonStyle}>
                <CloseIcon />
              </button>
            </div>
            <div style={fontScaleRowStyle}>
              <button
                type="button"
                onClick={() => setFontScale((value) => Math.max(70, value - 5))}
                style={tinyButtonStyle}
              >
                A-
              </button>
              <div style={fontScaleOptionsStyle}>
                {FONT_SCALE_OPTIONS.map((size) => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => setFontScale(size)}
                    style={{
                      ...chipStyle,
                      ...(fontScale === size ? selectedChipStyle : null),
                    }}
                  >
                    {size}%
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => setFontScale((value) => Math.min(180, value + 5))}
                style={tinyButtonStyle}
              >
                A+
              </button>
            </div>

            <div style={fontListStyle}>
              {FONT_OPTIONS.map((option) => (
                <button
                  key={option.label}
                  type="button"
                  onClick={() => setFontFamily(option.value)}
                  style={{
                    ...fontButtonStyle,
                    fontFamily: option.value,
                    ...(fontFamily === option.value ? selectedOptionButtonStyle : null),
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {recapDialogOpen ? (
          <section style={{ ...popoverStyle, ...recapPopoverStyle }}>
            <div style={popoverHeaderStyle}>
              <p style={popoverTitleStyle}>Recap depth</p>
              <button type="button" onClick={() => setRecapDialogOpen(false)} style={closePopoverButtonStyle}>
                <CloseIcon />
              </button>
            </div>
            <div style={{ display: "flex", justifyContent: "center" }}>
              <RecapLevelIndicator level={currentLevel} />
            </div>
            <div style={optionListStyle}>
              {Array.from({ length: 5 }).map((_, index) => {
                const level = index + 1;
                return (
                  <button
                    key={level}
                    type="button"
                    onClick={() => handleRecapRequest(level).catch(() => {})}
                    style={optionButtonStyle}
                  >
                    Level {level}
                  </button>
                );
              })}
            </div>
          </section>
        ) : null}

        {aiDialogOpen ? (
          <section style={{ ...popoverStyle, ...aiPopoverStyle }}>
            <div style={popoverHeaderStyle}>
              <p style={popoverTitleStyle}>AI processing</p>
              <button type="button" onClick={() => setAIDialogOpen(false)} style={closePopoverButtonStyle}>
                <CloseIcon />
              </button>
            </div>
            <p style={statusLineStyle}>
              {aiStatusLabel}
              {typeof ingestion.progress === "number" ? ` · ${ingestion.progress}%` : ""}
            </p>
            <p style={popoverBodyStyle}>{aiStatusDescription}</p>
            {ingestion.step ? <p style={helperTextStyle}>{ingestion.step}</p> : null}
            {ingestion.error ? <p style={errorTextStyle}>{ingestion.error}</p> : null}

            {(ingestion.status === "ready" || ingestion.status === "error") && !isAIComplete ? (
              <>
                <label style={toggleRowStyle}>
                  <input
                    type="checkbox"
                    checked={startInBackground}
                    onChange={(event) => setStartInBackground(event.target.checked)}
                  />
                  <span>Process in background</span>
                </label>
                <div style={dialogButtonsStyle}>
                  <button
                    type="button"
                    onClick={() => setAIDialogOpen(false)}
                    style={ghostButtonStyle}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => startAI(startInBackground).catch(() => {})}
                    disabled={isStartingAI}
                    style={primaryButtonStyle}
                  >
                    {isStartingAI ? "Starting..." : "Start processing"}
                  </button>
                </div>
              </>
            ) : null}

            {ingestion.llm ? (
              <div style={modelDetailsStyle}>
                <p style={modelLabelStyle}>Model details</p>
                <p style={modelTextStyle}>Provider: {ingestion.llm.provider}</p>
                <p style={modelTextStyle}>Recap: {ingestion.llm.recap_model}</p>
                <p style={modelTextStyle}>Embeddings: {ingestion.llm.embedding_model}</p>
              </div>
            ) : null}
          </section>
        ) : null}
      </div>

      {isRecapPanelOpen ? (
        <RecapPanel
          summary={summary}
          isLoading={isRecapLoading}
          level={currentLevel}
          onDismiss={handleDismissRecap}
        />
      ) : null}
    </div>
  );
}

function getAIStatusLabel(status) {
  if (status === "complete") {
    return "Recaps ready";
  }
  if (status === "processing") {
    return "Processing";
  }
  if (status === "error") {
    return "Needs attention";
  }
  return "Not started";
}

function getAIStatusDescription(status) {
  if (status === "complete") {
    return "AI indexing is finished, so recap actions are available now.";
  }
  if (status === "processing") {
    return "The book is being indexed for spoiler-safe recap generation.";
  }
  if (status === "error") {
    return "The last processing run did not finish. You can try again from here.";
  }
  return "Ready means the book can be processed, but AI indexing has not been started yet.";
}

function ChevronLeftIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path d="M15 5 8 12l7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path d="m9 5 7 7-7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path d="m12 3 1.8 4.7L18.5 9l-4.7 1.3L12 15l-1.8-4.7L5.5 9l4.7-1.3L12 3Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="m18.5 15 .9 2.3 2.3.9-2.3.9-.9 2.4-.9-2.4-2.4-.9 2.4-.9.9-2.3Z" fill="currentColor" />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path d="M9 7.2a3 3 0 0 1 5-2.2A3.2 3.2 0 0 1 18.8 8a3.4 3.4 0 0 1-.1 5.8A3.2 3.2 0 0 1 16 19H9.7A3.7 3.7 0 0 1 6 15.3V10a2.8 2.8 0 0 1 3-2.8Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 6.3v10.4M9.6 10h2.3M12 13.5h2.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function TypeIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path d="M6 7.5V5h12v2.5M12 5v14M8.5 19h7" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function LayoutIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <rect x="4" y="5" width="7" height="14" rx="1.8" stroke="currentColor" strokeWidth="1.8" />
      <rect x="13" y="5" width="7" height="14" rx="1.8" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path d="M15 6 9 12l6 6" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" aria-hidden="true">
      <path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

const readerPageStyle = {
  position: "relative",
  minHeight: "100vh",
  background:
    "radial-gradient(circle at top, rgba(240,225,198,0.9), rgba(225,213,193,0.96) 35%, #d8ccb8 100%)",
  overflow: "hidden",
};

const backStyle = {
  position: "fixed",
  top: 18,
  left: 18,
  zIndex: 30,
  display: "grid",
  placeItems: "center",
  width: 42,
  height: 42,
  border: "1px solid rgba(77, 60, 40, 0.14)",
  borderRadius: 999,
  background: "rgba(255, 250, 241, 0.9)",
  color: "#2c241d",
  backdropFilter: "blur(14px)",
  boxShadow: "0 12px 28px rgba(45, 33, 20, 0.12)",
};

const readerShellStyle = {
  position: "relative",
  height: "100vh",
  width: "100vw",
  background: "#f8f1e4",
  overflow: "hidden",
};

const loadingOverlayStyle = {
  position: "absolute",
  inset: 0,
  zIndex: 6,
  display: "grid",
  placeItems: "center",
  textAlign: "center",
  padding: "2rem",
  background:
    "linear-gradient(180deg, rgba(248, 241, 228, 0.98), rgba(243, 233, 216, 0.96))",
};

const loadingTitleStyle = {
  margin: 0,
  fontSize: "1.15rem",
  fontWeight: 800,
  color: "#2e241a",
};

const loadingTextStyle = {
  margin: "0.6rem 0 0",
  maxWidth: 420,
  lineHeight: 1.6,
  color: "#6d6153",
};

const edgeTurnZoneStyle = {
  position: "absolute",
  top: 0,
  bottom: 0,
  zIndex: 5,
  width: "clamp(56px, 9vw, 120px)",
  border: "none",
  background: "transparent",
  cursor: "pointer",
};

const hudBarWrapStyle = {
  position: "fixed",
  left: "50%",
  bottom: 18,
  zIndex: 35,
  width: "min(960px, calc(100vw - 24px))",
  transition: "transform 220ms ease, opacity 220ms ease",
};

const bottomRevealStripStyle = {
  position: "fixed",
  left: 0,
  right: 0,
  bottom: 0,
  zIndex: 20,
  height: 96,
  background: "transparent",
};

const hudBarStyle = {
  position: "relative",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
  padding: "0.6rem 0.8rem",
  borderRadius: 999,
  background: "rgba(30, 25, 21, 0.82)",
  color: "#fff7ec",
  backdropFilter: "blur(22px)",
  boxShadow: "0 22px 40px rgba(25, 20, 15, 0.28)",
};

const groupStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const iconButtonStyle = {
  display: "grid",
  placeItems: "center",
  width: 44,
  height: 44,
  border: "none",
  borderRadius: 999,
  background: "rgba(255, 248, 236, 0.14)",
  color: "inherit",
  cursor: "pointer",
};

const secondaryIconButtonStyle = {
  ...iconButtonStyle,
  width: 40,
  height: 40,
  background: "rgba(255, 248, 236, 0.08)",
};

const navIconButtonStyle = {
  ...iconButtonStyle,
  width: 46,
  height: 46,
};

const disabledIconButtonStyle = {
  opacity: 0.45,
  cursor: "not-allowed",
};

const pageControlStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  minWidth: 110,
  padding: "0 0.2rem",
};

const pageInputStyle = {
  width: 42,
  border: "none",
  outline: "none",
  background: "transparent",
  color: "inherit",
  fontSize: "0.98rem",
  fontWeight: 700,
  textAlign: "right",
};

const pageTotalStyle = {
  color: "rgba(255, 247, 236, 0.72)",
  fontWeight: 600,
};

const popoverStyle = {
  position: "absolute",
  bottom: 66,
  padding: "0.95rem",
  borderRadius: 22,
  background: "rgba(255, 251, 243, 0.97)",
  color: "#261d15",
  boxShadow: "0 22px 50px rgba(32, 24, 16, 0.22)",
  backdropFilter: "blur(20px)",
};

const layoutPopoverStyle = {
  left: 72,
  width: 240,
};

const fontPopoverStyle = {
  left: 132,
  width: "min(460px, calc(100vw - 32px))",
};

const recapPopoverStyle = {
  right: 62,
  width: 220,
};

const aiPopoverStyle = {
  right: 12,
  width: 320,
};

const popoverTitleStyle = {
  margin: 0,
  fontSize: "0.96rem",
  fontWeight: 800,
};

const popoverHeaderStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 10,
};

const closePopoverButtonStyle = {
  display: "grid",
  placeItems: "center",
  width: 28,
  height: 28,
  border: "none",
  borderRadius: 999,
  background: "rgba(32, 26, 20, 0.08)",
  color: "#31261d",
};

const popoverBodyStyle = {
  margin: "0.5rem 0 0",
  color: "#5d5145",
  lineHeight: 1.5,
};

const statusLineStyle = {
  margin: "0.45rem 0 0",
  fontWeight: 700,
};

const helperTextStyle = {
  margin: "0.45rem 0 0",
  color: "#7b6e61",
  fontSize: "0.9rem",
};

const errorTextStyle = {
  margin: "0.45rem 0 0",
  color: "#a32828",
  fontSize: "0.92rem",
};

const optionListStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  marginTop: "0.8rem",
};

const optionButtonStyle = {
  border: "1px solid rgba(67, 53, 39, 0.1)",
  borderRadius: 14,
  padding: "0.72rem 0.85rem",
  background: "#fff",
  textAlign: "left",
  color: "#261d15",
};

const selectedOptionButtonStyle = {
  background: "#201a14",
  color: "#fff9ef",
};

const fontScaleRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  marginTop: "0.8rem",
};

const fontScaleOptionsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 6,
};

const tinyButtonStyle = {
  border: "1px solid rgba(67, 53, 39, 0.1)",
  borderRadius: 12,
  padding: "0.58rem 0.7rem",
  background: "#fff",
  fontWeight: 700,
};

const chipStyle = {
  border: "1px solid rgba(67, 53, 39, 0.1)",
  borderRadius: 999,
  padding: "0.45rem 0.72rem",
  background: "#fff",
  fontWeight: 700,
  fontSize: "0.84rem",
};

const selectedChipStyle = {
  background: "#201a14",
  color: "#fff9ef",
};

const fontListStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(122px, 1fr))",
  gap: 8,
  marginTop: "0.8rem",
};

const fontButtonStyle = {
  border: "1px solid rgba(67, 53, 39, 0.1)",
  borderRadius: 14,
  padding: "0.75rem 0.85rem",
  background: "#fff",
  textAlign: "left",
};

const toggleRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  marginTop: "0.9rem",
  color: "#3a2f24",
  fontWeight: 600,
};

const dialogButtonsStyle = {
  display: "flex",
  justifyContent: "flex-end",
  gap: 8,
  marginTop: "1rem",
};

const ghostButtonStyle = {
  border: "1px solid rgba(67, 53, 39, 0.12)",
  borderRadius: 12,
  padding: "0.72rem 0.95rem",
  background: "#fff",
  color: "#2f251c",
  fontWeight: 700,
};

const primaryButtonStyle = {
  border: "none",
  borderRadius: 12,
  padding: "0.72rem 0.95rem",
  background: "#1f3441",
  color: "#fff",
  fontWeight: 800,
};

const modelDetailsStyle = {
  marginTop: "1rem",
  paddingTop: "0.9rem",
  borderTop: "1px solid rgba(67, 53, 39, 0.08)",
};

const modelLabelStyle = {
  margin: 0,
  fontSize: "0.82rem",
  fontWeight: 800,
  color: "#7d6f61",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
};

const modelTextStyle = {
  margin: "0.35rem 0 0",
  fontSize: "0.9rem",
  color: "#493d31",
};
