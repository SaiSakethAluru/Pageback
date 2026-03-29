import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import ePub from "epubjs";

const EpubReader = forwardRef(function EpubReader(
  {
    bookUrl,
    initialCfi,
    onPositionChange,
    layoutMode = "horizontal-spread",
    fontScale = 100,
    fontFamily = "Georgia, serif",
    onReaderStateChange,
  },
  ref,
) {
  const containerRef = useRef(null);
  const bookRef = useRef(null);
  const renditionRef = useRef(null);
  const latestCfiRef = useRef(initialCfi ?? null);
  const onPositionChangeRef = useRef(onPositionChange);
  const onReaderStateChangeRef = useRef(onReaderStateChange);
  const [error, setError] = useState("");

  useEffect(() => {
    onPositionChangeRef.current = onPositionChange;
  }, [onPositionChange]);

  useEffect(() => {
    onReaderStateChangeRef.current = onReaderStateChange;
  }, [onReaderStateChange]);

  useEffect(() => {
    if (initialCfi) {
      latestCfiRef.current = initialCfi;
    }
  }, [initialCfi]);

  useEffect(() => {
    if (!renditionRef.current) {
      return;
    }

    renditionRef.current.themes.fontSize(`${fontScale}%`);
    renditionRef.current.themes.font(fontFamily);
  }, [fontFamily, fontScale]);

  useEffect(() => {
    if (!bookUrl || !containerRef.current) {
      return undefined;
    }

    let isCancelled = false;
    let rendition = null;
    let book = null;
    let handleRelocated = null;

    const layoutConfig = getLayoutConfig(layoutMode);

    function emitReaderState(location) {
      if (!location || !bookRef.current) {
        return;
      }

      const hasGeneratedLocations =
        typeof bookRef.current.locations?.length === "function" &&
        bookRef.current.locations.length() > 0;
      const currentPage = hasGeneratedLocations
        ? bookRef.current.locations.locationFromCfi(location.start.cfi) + 1
        : location.start.displayed.page;
      const totalPages = hasGeneratedLocations
        ? bookRef.current.locations.length()
        : location.start.displayed.total;

      onReaderStateChangeRef.current?.({
        atStart: Boolean(location.atStart),
        atEnd: Boolean(location.atEnd),
        canGoPrevious: !location.atStart,
        canGoNext: !location.atEnd,
        currentPage: Number.isFinite(currentPage) ? Math.max(1, currentPage) : 1,
        totalPages: Number.isFinite(totalPages) ? Math.max(1, totalPages) : 1,
      });
    }

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
          flow: layoutConfig.flow,
          manager: layoutConfig.manager,
          spread: layoutConfig.spread,
          minSpreadWidth: 0,
        });

        bookRef.current = book;
        renditionRef.current = rendition;
        rendition.themes.default({
          body: {
            "line-height": "1.65",
            color: "#211d19",
            background: "transparent",
          },
        });
        rendition.themes.fontSize(`${fontScale}%`);
        rendition.themes.font(fontFamily);

        handleRelocated = (location) => {
          const cfi = location?.start?.cfi ?? null;
          latestCfiRef.current = cfi;
          const percentage = book.locations?.percentageFromCfi?.(cfi) ?? 0;
          const totalLocations =
            typeof book.locations?.length === "function" ? book.locations.length() : 0;
          const charOffset = Math.max(0, Math.round(percentage * Math.max(1, totalLocations) * 1200));
          onPositionChangeRef.current?.(cfi, charOffset);
          emitReaderState(location);
        };

        rendition.on("relocated", handleRelocated);
        await book.ready;
        try {
          await book.locations.generate(1650);
        } catch {
          // If locations fail to generate we fall back to section-local page counts.
        }

        const targetCfi = latestCfiRef.current ?? initialCfi;
        if (targetCfi) {
          await rendition.display(targetCfi);
        } else {
          await rendition.display();
        }
        emitReaderState(rendition.currentLocation());
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
  }, [bookUrl, initialCfi, layoutMode]);

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
    async goToPage(pageNumber) {
      if (!bookRef.current || !renditionRef.current) {
        return false;
      }

      const totalPages =
        typeof bookRef.current.locations?.length === "function" ? bookRef.current.locations.length() : 0;
      if (!totalPages) {
        return false;
      }

      const boundedPage = Math.min(Math.max(1, Number(pageNumber) || 1), totalPages);
      const targetCfi = bookRef.current.locations.cfiFromLocation(boundedPage - 1);
      if (!targetCfi) {
        return false;
      }

      await renditionRef.current.display(targetCfi);
      return true;
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

function getLayoutConfig(layoutMode) {
  switch (layoutMode) {
    case "horizontal-single":
      return {
        flow: "paginated",
        manager: "default",
        spread: "none",
      };
    case "vertical-single":
      return {
        flow: "scrolled-doc",
        manager: "default",
        spread: "none",
      };
    case "vertical-continuous":
      return {
        flow: "scrolled-continuous",
        manager: "continuous",
        spread: "none",
      };
    case "horizontal-spread":
    default:
      return {
        flow: "paginated",
        manager: "default",
        spread: "auto",
      };
  }
}

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
