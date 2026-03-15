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

  useEffect(() => {
    async function load() {
      const [fileUrl, position] = await Promise.all([api.getBookFileUrl(bookId), api.getPosition(bookId)]);
      setBookUrl(fileUrl.signed_url || "");

      setInitialCfi(position.position_cfi);
      setCurrentCfi(position.position_cfi);
      setCurrentChar(position.position_char || 0);
    }

    load();
    return () => {
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
    };
  }, [bookId]);

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

  return (
    <div style={readerPageStyle}>
      <button type="button" onClick={() => navigate("/library")} style={backStyle}>
        Back
      </button>
      <div style={readerShellStyle}>
        <ReaderComponent
          ref={readerRef}
          bookUrl={bookUrl}
          initialCfi={initialCfi}
          onPositionChange={handlePositionChange}
        />
      </div>
      <RecapFAB bookId={bookId} positionChar={currentChar} />
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

const readerShellStyle = {
  height: "calc(100vh - 96px)",
  background: "#fffaf0",
  borderRadius: 24,
  overflow: "hidden",
  boxShadow: "0 24px 60px rgba(0,0,0,0.12)",
};
