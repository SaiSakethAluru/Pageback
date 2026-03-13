import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import ePub from "epubjs";

const EpubReader = forwardRef(function EpubReader(
  { bookUrl, initialCfi, onPositionChange },
  ref,
) {
  const containerRef = useRef(null);
  const bookRef = useRef(null);
  const renditionRef = useRef(null);
  const latestCfiRef = useRef(initialCfi ?? null);

  useEffect(() => {
    if (!bookUrl || !containerRef.current) {
      return undefined;
    }

    const book = ePub(bookUrl);
    const rendition = book.renderTo(containerRef.current, {
      width: "100%",
      height: "100%",
    });

    bookRef.current = book;
    renditionRef.current = rendition;

    const handleRelocated = (location) => {
      const cfi = location?.start?.cfi ?? null;
      latestCfiRef.current = cfi;
      const charOffset = Math.max(
        0,
        Math.round((location?.start?.displayed?.page ?? 0) * 1200),
      );
      onPositionChange?.(cfi, charOffset);
    };

    rendition.on("relocated", handleRelocated);
    if (initialCfi) {
      rendition.display(initialCfi);
    } else {
      rendition.display();
    }

    return () => {
      rendition.off("relocated", handleRelocated);
      rendition.destroy();
      book.destroy();
    };
  }, [bookUrl, initialCfi, onPositionChange]);

  useImperativeHandle(ref, () => ({
    getCurrentCfi() {
      return latestCfiRef.current;
    },
  }));

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
});

export default EpubReader;
