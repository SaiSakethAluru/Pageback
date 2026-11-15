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
    onTextSelected,
    onClearSelection,
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
  const onTextSelectedRef = useRef(onTextSelected);
  const onClearSelectionRef = useRef(onClearSelection);
  const locationsReadyRef = useRef(false);
  const calculatePositionInfoRef = useRef(null);
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
    onTextSelectedRef.current = onTextSelected;
  }, [onTextSelected]);

  useEffect(() => {
    onClearSelectionRef.current = onClearSelection;
  }, [onClearSelection]);

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

    function calculatePositionInfo(location) {
      if (!location || !bookRef.current) {
        return { cfi: latestCfiRef.current ?? initialCfi ?? null, charOffset: 0, percentage: 0 };
      }

      const cfi = location.start?.cfi ?? latestCfiRef.current ?? initialCfi ?? null;
      const totalLocations =
        typeof bookRef.current.locations?.length === "function" ? bookRef.current.locations.length() : 0;

      let percentage = null;
      // 1. Try epub.js locations if ready
      if (totalLocations > 0 && locationsReadyRef.current) {
        const locPct = bookRef.current.locations.percentageFromCfi?.(cfi);
        if (typeof locPct === "number" && Number.isFinite(locPct) && locPct >= 0) {
          percentage = locPct;
        } else if (
          typeof location.start?.percentage === "number" &&
          Number.isFinite(location.start.percentage) &&
          location.start.percentage >= 0
        ) {
          percentage = location.start.percentage;
        }
      }

      // 2. Fallback to pageList if available
      if (percentage === null) {
        const mappedPage = bookRef.current.pageList?.pageFromCfi?.(cfi) ?? -1;
        const lastPage =
          bookRef.current.pageList?.lastPage ||
          (bookRef.current.pageList?.pages?.length > 0 ? bookRef.current.pageList.pages.length : 0);
        if (mappedPage > 0 && lastPage > 0) {
          percentage = Math.max(0, Math.min(1, (mappedPage - 1) / lastPage));
        }
      }

      // 3. Fallback to spine index
      if (percentage === null) {
        let spineIndex = typeof location.start?.index === "number" ? location.start.index : null;
        if (spineIndex === null && cfi) {
          const match = cfi.match(/\/6\/(\d+)!/);
          if (match) {
            spineIndex = Math.floor(parseInt(match[1], 10) / 2);
          }
        }
        const totalSpine = bookRef.current.spine?.length || 1;
        if (spineIndex != null && spineIndex >= 0 && totalSpine > 0) {
          percentage = Math.max(0, Math.min(1, spineIndex / totalSpine));
        }
      }

      if (percentage === null || !Number.isFinite(percentage)) {
        percentage = 0;
      }

      const totalEstimatedChars =
        totalLocations > 0
          ? totalLocations * 1650
          : (bookRef.current.spine?.length || 40) * 14000;

      const charOffset = Math.max(0, Math.round(percentage * totalEstimatedChars));
      return { cfi, charOffset, percentage };
    }

    calculatePositionInfoRef.current = calculatePositionInfo;

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
          const doc = contents.document;
          if (!doc) return;

          doc.addEventListener("keydown", handleContentKeyDown, true);

          // Clear selection when clicked without active selection
          doc.addEventListener("click", () => {
            const sel = contents.window?.getSelection();
            if (!sel || sel.isCollapsed) {
              onClearSelectionRef.current?.();
            }
          });

          // Long press detection for mobile/touch
          let activeTouchTimer = null;
          let touchStartPos = null;

          doc.addEventListener(
            "touchstart",
            (event) => {
              if (event.touches.length !== 1) return;
              const touch = event.touches[0];
              touchStartPos = { x: touch.clientX, y: touch.clientY };

              if (activeTouchTimer) {
                clearTimeout(activeTouchTimer);
              }

              activeTouchTimer = setTimeout(() => {
                activeTouchTimer = null;
                try {
                  let range = null;
                  if (doc.caretRangeFromPoint) {
                    range = doc.caretRangeFromPoint(touch.clientX, touch.clientY);
                  } else if (doc.caretPositionFromPoint) {
                    const pos = doc.caretPositionFromPoint(touch.clientX, touch.clientY);
                    if (pos) {
                      range = doc.createRange();
                      range.setStart(pos.offsetNode, pos.offset);
                      range.collapse(true);
                    }
                  }

                  if (range && range.startContainer && range.startContainer.nodeType === Node.TEXT_NODE) {
                    const textNode = range.startContainer;
                    const fullText = textNode.nodeValue || "";
                    const offset = range.startOffset;

                    let start = offset;
                    while (start > 0 && /[\w'-]/.test(fullText[start - 1])) {
                      start--;
                    }
                    let end = offset;
                    while (end < fullText.length && /[\w'-]/.test(fullText[end])) {
                      end++;
                    }

                    if (end > start) {
                      const word = fullText.slice(start, end).trim();
                      if (word) {
                        const wordRange = doc.createRange();
                        wordRange.setStart(textNode, start);
                        wordRange.setEnd(textNode, end);
                        const wordRect = wordRange.getBoundingClientRect();
                        const iframeEl = doc.defaultView?.frameElement;
                        const iframeRect = iframeEl?.getBoundingClientRect() || { left: 0, top: 0 };

                        const sel = contents.window?.getSelection();
                        if (sel) {
                          sel.removeAllRanges();
                          sel.addRange(wordRange);
                        }

                        onTextSelectedRef.current?.({
                          text: word,
                          isLongPress: true,
                          rect: {
                            top: wordRect.top + iframeRect.top,
                            bottom: wordRect.bottom + iframeRect.top,
                            left: wordRect.left + iframeRect.left,
                            right: wordRect.right + iframeRect.left,
                            width: wordRect.width,
                            height: wordRect.height,
                          },
                        });
                      }
                    }
                  }
                } catch {
                  // Ignore touch lookup errors
                }
              }, 450);
            },
            { passive: true }
          );

          doc.addEventListener(
            "touchmove",
            (event) => {
              if (activeTouchTimer && touchStartPos && event.touches[0]) {
                const dx = event.touches[0].clientX - touchStartPos.x;
                const dy = event.touches[0].clientY - touchStartPos.y;
                if (Math.hypot(dx, dy) > 10) {
                  clearTimeout(activeTouchTimer);
                  activeTouchTimer = null;
                }
              }
            },
            { passive: true }
          );

          doc.addEventListener("touchend", () => {
            if (activeTouchTimer) {
              clearTimeout(activeTouchTimer);
              activeTouchTimer = null;
            }
          });

          // Mouse selection on desktop
          doc.addEventListener("mouseup", () => {
            setTimeout(() => {
              const sel = contents.window?.getSelection();
              if (sel && !sel.isCollapsed) {
                const text = sel.toString().trim();
                if (text && text.length > 0) {
                  try {
                    const range = sel.getRangeAt(0);
                    const rect = range.getBoundingClientRect();
                    const iframeEl = doc.defaultView?.frameElement;
                    const iframeRect = iframeEl?.getBoundingClientRect() || { left: 0, top: 0 };
                    onTextSelectedRef.current?.({
                      text,
                      isLongPress: false,
                      rect: {
                        top: rect.top + iframeRect.top,
                        bottom: rect.bottom + iframeRect.top,
                        left: rect.left + iframeRect.left,
                        right: rect.right + iframeRect.left,
                        width: rect.width,
                        height: rect.height,
                      },
                    });
                  } catch {
                    // Ignore range errors
                  }
                }
              }
            }, 10);
          });
        });

        rendition.on("selected", (cfiRange, contents) => {
          try {
            const range = rendition.getRange(cfiRange);
            if (!range) return;
            const text = range.toString().trim();
            if (!text) return;
            const rect = range.getBoundingClientRect();
            const iframeEl = contents?.document?.defaultView?.frameElement;
            const iframeRect = iframeEl?.getBoundingClientRect() || { left: 0, top: 0 };
            onTextSelectedRef.current?.({
              text,
              cfiRange,
              isLongPress: false,
              rect: {
                top: rect.top + iframeRect.top,
                bottom: rect.bottom + iframeRect.top,
                left: rect.left + iframeRect.left,
                right: rect.right + iframeRect.left,
                width: rect.width,
                height: rect.height,
              },
            });
          } catch {
            // ignore
          }
        });

        handleRelocated = (location) => {
          const { cfi, charOffset } = calculatePositionInfo(location);
          if (cfi) {
            latestCfiRef.current = cfi;
          }
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
            const currLoc = rendition.currentLocation();
            if (currLoc) {
              const { cfi, charOffset } = calculatePositionInfo(currLoc);
              if (cfi && charOffset > 0) {
                latestCfiRef.current = cfi;
                onPositionChangeRef.current?.(cfi, charOffset);
              }
              emitReaderState(currLoc);
            }
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
    getCharOffset() {
      const currLoc = renditionRef.current?.currentLocation();
      return calculatePositionInfoRef.current ? calculatePositionInfoRef.current(currLoc).charOffset : 0;
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
