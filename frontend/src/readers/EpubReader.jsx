import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import ePub from "epubjs";

const EpubReader = forwardRef(function EpubReader(
  { bookUrl, initialCfi, onPositionChange },
  ref,
) {
  const containerRef = useRef(null);
  const bookRef = useRef(null);
  const renditionRef = useRef(null);
  const latestCfiRef = useRef(initialCfi ?? null);
  const onPositionChangeRef = useRef(onPositionChange);
  const [error, setError] = useState("");

  useEffect(() => {
    onPositionChangeRef.current = onPositionChange;
  }, [onPositionChange]);

  useEffect(() => {
    if (!bookUrl || !containerRef.current) {
      return undefined;
    }

    let isCancelled = false;
    let rendition = null;
    let book = null;
    let handleRelocated = null;

    async function loadBook() {
      setError("");

      try {
        const response = await fetch(bookUrl);
        if (!response.ok) {
          throw new Error(`EPUB download failed (${response.status})`);
        }

        const data = await response.arrayBuffer();
        if (isCancelled || !containerRef.current) {
          return;
        }

        book = ePub(data);
        rendition = book.renderTo(containerRef.current, {
          width: "100%",
          height: "100%",
        });

        bookRef.current = book;
        renditionRef.current = rendition;

        handleRelocated = (location) => {
          const cfi = location?.start?.cfi ?? null;
          latestCfiRef.current = cfi;
          const charOffset = Math.max(
            0,
            Math.round((location?.start?.displayed?.page ?? 0) * 1200),
          );
          onPositionChangeRef.current?.(cfi, charOffset);
        };

        rendition.on("relocated", handleRelocated);
        if (initialCfi) {
          await rendition.display(initialCfi);
        } else {
          await rendition.display();
        }
      } catch (loadError) {
        if (!isCancelled) {
          setError(loadError instanceof Error ? loadError.message : "Could not open this EPUB.");
        }
      }
    }

    loadBook();

    return () => {
      isCancelled = true;
      if (rendition && handleRelocated) {
        rendition.off("relocated", handleRelocated);
      }
      if (rendition) {
        rendition.destroy();
      }
      if (book) {
        book.destroy();
      }
    };
  }, [bookUrl, initialCfi]);

  useImperativeHandle(ref, () => ({
    getCurrentCfi() {
      return latestCfiRef.current;
    },
    next() {
      return renditionRef.current?.next();
    },
    prev() {
      return renditionRef.current?.prev();
    },
  }));

  return (
    <>
      {error ? <div style={errorStyle}>Reader error: {error}</div> : null}
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
    </>
  );
});

export default EpubReader;

const errorStyle = {
  position: "absolute",
  top: "1rem",
  left: "1rem",
  right: "1rem",
  zIndex: 1,
  padding: "0.8rem 1rem",
  borderRadius: 12,
  background: "#fff2f2",
  color: "#8a1c1c",
  border: "1px solid #f0bcbc",
};
