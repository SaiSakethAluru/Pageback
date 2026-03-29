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
    onLoadingChange,
    onReadyChange,
  },
  ref,
) {
  const containerRef = useRef(null);
  const bookRef = useRef(null);
  const renditionRef = useRef(null);
  const latestCfiRef = useRef(initialCfi ?? null);
  const onPositionChangeRef = useRef(onPositionChange);
  const onReaderStateChangeRef = useRef(onReaderStateChange);
  const onLoadingChangeRef = useRef(onLoadingChange);
  const onReadyChangeRef = useRef(onReadyChange);
  const locationsReadyRef = useRef(false);
  const [error, setError] = useState("");

  useEffect(() => {
    onPositionChangeRef.current = onPositionChange;
  }, [onPositionChange]);

  useEffect(() => {
    onReaderStateChangeRef.current = onReaderStateChange;
  }, [onReaderStateChange]);

  useEffect(() => {
    onLoadingChangeRef.current = onLoadingChange;
  }, [onLoadingChange]);

  useEffect(() => {
    onReadyChangeRef.current = onReadyChange;
  }, [onReadyChange]);

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
    let handleContentKeyDown = null;

    const layoutConfig = getLayoutConfig(layoutMode);

    function emitReaderState(location) {
      if (!location || !bookRef.current) {
        return;
      }

      const mappedPage = bookRef.current.pageList?.pageFromCfi?.(location.start.cfi) ?? -1;
      const hasPageList = mappedPage !== -1;
      const hasGeneratedLocations =
        !hasPageList &&
        locationsReadyRef.current &&
        typeof bookRef.current.locations?.length === "function" &&
        bookRef.current.locations.length() > 0;
      const currentPage = hasPageList
        ? mappedPage
        : hasGeneratedLocations
          ? bookRef.current.locations.locationFromCfi(location.start.cfi) + 1
          : null;
      const totalPages = hasPageList
        ? bookRef.current.pageList.lastPage || null
        : hasGeneratedLocations
          ? bookRef.current.locations.length()
          : null;

      onReaderStateChangeRef.current?.({
        atStart: Boolean(location.atStart),
        atEnd: Boolean(location.atEnd),
        canGoPrevious: !location.atStart,
        canGoNext: !location.atEnd,
        currentPage: Number.isFinite(currentPage) ? Math.max(1, currentPage) : null,
        totalPages: Number.isFinite(totalPages) ? Math.max(1, totalPages) : null,
      });
    }

    async function loadBook() {
      setError("");
      locationsReadyRef.current = false;
      onLoadingChangeRef.current?.(true);
      onReadyChangeRef.current?.(false);

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
            "caret-color": "transparent",
            outline: "none",
          },
        });
        rendition.themes.fontSize(`${fontScale}%`);
        rendition.themes.font(fontFamily);

        handleContentKeyDown = (event) => {
          if (event.defaultPrevented) {
            return;
          }

          if (event.key === "Escape") {
            clearRenditionFocus(rendition);
            event.preventDefault();
            return;
          }

          if (layoutMode.startsWith("horizontal")) {
            if (event.key === "ArrowLeft") {
              rendition.prev();
              event.preventDefault();
            }
            if (event.key === "ArrowRight") {
              rendition.next();
              event.preventDefault();
            }
            return;
          }

          if (event.key === "ArrowUp") {
            rendition.prev();
            event.preventDefault();
          }
          if (event.key === "ArrowDown") {
            rendition.next();
            event.preventDefault();
          }
        };

        rendition.hooks.content.register((contents) => {
          contents.document?.addEventListener("keydown", handleContentKeyDown, true);
        });

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

        const targetCfi = latestCfiRef.current ?? initialCfi;
        if (targetCfi) {
          await rendition.display(targetCfi);
        } else {
          await rendition.display();
        }
        emitReaderState(rendition.currentLocation());
        onReadyChangeRef.current?.(true);
        onLoadingChangeRef.current?.(false);

        book.locations
          .generate(1650)
          .then(() => {
            if (isCancelled) {
              return;
            }
            locationsReadyRef.current = true;
            emitReaderState(rendition.currentLocation());
          })
          .catch(() => {
            // If locations fail to generate we keep the book readable and omit absolute page counts.
          });
      } catch (loadError) {
        if (!isCancelled) {
          setError(loadError instanceof Error ? loadError.message : "Could not open this EPUB.");
        }
        onLoadingChangeRef.current?.(false);
      }
    }

    loadBook();

    return () => {
      isCancelled = true;
      if (rendition && handleRelocated) {
        rendition.off("relocated", handleRelocated);
      }
      if (rendition && handleContentKeyDown) {
        const contents = rendition.getContents?.() ?? [];
        contents.forEach((content) => {
          content.document?.removeEventListener("keydown", handleContentKeyDown, true);
        });
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

      const targetFromPageList = bookRef.current.pageList?.cfiFromPage?.(pageNumber);
      if (targetFromPageList && targetFromPageList !== -1) {
        await renditionRef.current.display(targetFromPageList);
        return true;
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
    clearFocus() {
      const contents = renditionRef.current?.getContents?.() ?? [];
      contents.forEach((content) => {
        content.document?.activeElement?.blur?.();
        content.window?.getSelection?.()?.removeAllRanges?.();
      });
      document.activeElement?.blur?.();
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

function clearRenditionFocus(rendition) {
  const contents = rendition?.getContents?.() ?? [];
  contents.forEach((content) => {
    content.document?.activeElement?.blur?.();
    content.window?.getSelection?.()?.removeAllRanges?.();
  });
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
