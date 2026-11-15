import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import appIcon from "../../assets/icons/pageback-book.svg";
import * as api from "../../services/api";
import AddBookCard from "./AddBookCard";
import BookCard from "./BookCard";
import DeleteBookModal from "./DeleteBookModal";
import MetadataEditorModal from "./MetadataEditorModal";
import UploadButton from "./UploadButton";

export default function LibraryPage() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [editingBook, setEditingBook] = useState(null);
  const [deletingBook, setDeletingBook] = useState(null);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [viewMode, setViewMode] = useState(
    () => localStorage.getItem("pageback_library_view_mode") || "grid"
  );
  const profileMenuRef = useRef(null);

  useEffect(() => {
    try {
      localStorage.setItem("pageback_library_view_mode", viewMode);
    } catch {
      // ignore
    }
  }, [viewMode]);

  async function loadBooks() {
    setLoading(true);
    const [{ user: currentUser }, response] = await Promise.all([api.getCurrentUser(), api.getBooks()]);
    setUser(currentUser);
    setBooks(response);
    setLoading(false);
  }

  useEffect(() => {
    loadBooks().catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!profileMenuOpen) {
      return undefined;
    }

    function handleWindowClick(event) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setProfileMenuOpen(false);
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") {
        setProfileMenuOpen(false);
      }
    }

    window.addEventListener("mousedown", handleWindowClick);
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("mousedown", handleWindowClick);
      window.removeEventListener("keydown", handleEscape);
    };
  }, [profileMenuOpen]);

  async function handleLogout() {
    await api.logout();
    window.location.href = "/login";
  }

  function handleMetadataSaved(bookId, updatedMetadata) {
    setBooks((currentBooks) =>
      currentBooks.map((book) =>
        book.id === bookId
          ? {
              ...book,
              title: updatedMetadata.title ?? null,
              author: updatedMetadata.author ?? null,
              series_name: updatedMetadata.series_name ?? book.series_name,
              series_order: updatedMetadata.series_order ?? book.series_order,
              cover_url: updatedMetadata.cover_url ?? book.cover_url,
            }
          : book
      )
    );
  }

  const displayName = getDisplayName(user);
  const profileInitial = displayName.charAt(0).toUpperCase();

  return (
    <div style={pageStyle}>
      <header style={navBarStyle}>
        <Link to="/library" style={brandStyle} aria-label="PageBack library">
          <img src={appIcon} alt="" style={brandIconStyle} />
          <span>PageBack</span>
        </Link>

        <div style={navActionsStyle}>
          <UploadButton
            onUploadComplete={loadBooks}
            containerStyle={topUploadContainerStyle}
            errorStyle={topUploadErrorStyle}
            renderTrigger={({ openFilePicker, isUploading }) => (
              <button
                type="button"
                aria-label="Upload book"
                onClick={openFilePicker}
                style={iconButtonStyle}
              >
                {isUploading ? "..." : "+"}
              </button>
            )}
          />
          <div ref={profileMenuRef} style={profileMenuWrapStyle}>
            <button
              type="button"
              aria-label="Open profile menu"
              aria-expanded={profileMenuOpen}
              onClick={() => setProfileMenuOpen((open) => !open)}
              style={profileButtonStyle}
            >
              <span style={profileAvatarStyle}>{profileInitial}</span>
              <span style={profileNameStyle}>{displayName}</span>
            </button>
            {profileMenuOpen ? (
              <div style={profileMenuStyle}>
                <div style={profileSummaryStyle}>
                  <span style={profileSummaryNameStyle}>{displayName}</span>
                  {user?.email ? <span style={profileSummaryEmailStyle}>{user.email}</span> : null}
                </div>
                <Link to="/settings" style={profileMenuItemStyle} onClick={() => setProfileMenuOpen(false)}>
                  Settings
                </Link>
                <button type="button" onClick={handleLogout} style={dangerProfileMenuItemStyle}>
                  Log out
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <main>
        <div style={toolbarStyle}>
          <div>
            <h1 style={pageTitleStyle}>My Library</h1>
            <p style={pageSubtitleStyle}>
              {books.length} book{books.length === 1 ? "" : "s"} in your collection
            </p>
          </div>

          <div style={toolbarActionsStyle}>
            <div style={viewToggleWrapStyle} role="radiogroup" aria-label="Library display mode">
              <button
                type="button"
                onClick={() => setViewMode("grid")}
                style={{
                  ...viewToggleButtonStyle,
                  ...(viewMode === "grid" ? activeViewToggleButtonStyle : null),
                }}
                aria-label="Grid view"
                title="Apple Books Grid View"
              >
                ▦ Grid
              </button>
              <button
                type="button"
                onClick={() => setViewMode("list")}
                style={{
                  ...viewToggleButtonStyle,
                  ...(viewMode === "list" ? activeViewToggleButtonStyle : null),
                }}
                aria-label="Calibre list view"
                title="Calibre Table View"
              >
                ☰ Calibre List
              </button>
            </div>
          </div>
        </div>

        {loading ? <p style={loadingStateStyle}>Loading books...</p> : null}

        {!loading && viewMode === "grid" ? (
          <div style={gridStyle}>
            {books.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                onDelete={setDeletingBook}
                onEditMetadata={setEditingBook}
              />
            ))}
            <AddBookCard onUploadComplete={loadBooks} />
          </div>
        ) : null}

        {!loading && viewMode === "list" ? (
          <div style={tableContainerStyle}>
            <table style={tableStyle}>
              <thead>
                <tr style={tableHeadRowStyle}>
                  <th style={thStyle}>Cover</th>
                  <th style={{ ...thStyle, textAlign: "left" }}>Title & Author</th>
                  <th style={thStyle}>Series</th>
                  <th style={thStyle}>Format</th>
                  <th style={thStyle}>AI Status</th>
                  <th style={thStyle}>Added</th>
                  <th style={{ ...thStyle, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {books.map((book) => (
                  <tr key={book.id} style={tableRowStyle}>
                    <td style={tdCoverStyle}>
                      <Link to={`/reader/${book.id}`} style={coverLinkStyle}>
                        {book.cover_url ? (
                          <img src={book.cover_url} alt="" style={tableCoverImgStyle} />
                        ) : (
                          <div style={tableCoverFallbackStyle}>
                            {getInitials(book.title)}
                          </div>
                        )}
                      </Link>
                    </td>
                    <td style={tdMainStyle}>
                      <Link to={`/reader/${book.id}`} style={bookTitleLinkStyle}>
                        {book.title || "Untitled"}
                      </Link>
                      <span style={bookAuthorSpanStyle}>
                        {book.author || "Unknown author"}
                      </span>
                    </td>
                    <td style={tdCenterStyle}>
                      {book.series_name ? (
                        <span style={seriesTableBadgeStyle} title={`Series: ${book.series_name}`}>
                          {book.series_name} {book.series_order != null ? `#${book.series_order}` : ""}
                        </span>
                      ) : (
                        <span style={emptySeriesSpanStyle}>—</span>
                      )}
                    </td>
                    <td style={tdCenterStyle}>
                      <span style={formatBadgeStyle}>EPUB</span>
                    </td>
                    <td style={tdCenterStyle}>
                      <span
                        style={{
                          ...statusBadgeStyle,
                          background:
                            book.ingestion_status === "complete"
                              ? "#e4efe7"
                              : book.ingestion_status === "processing"
                              ? "#fff3dc"
                              : "#f0ece4",
                          color:
                            book.ingestion_status === "complete"
                              ? "#2b5e3b"
                              : book.ingestion_status === "processing"
                              ? "#875a13"
                              : "#695e52",
                        }}
                      >
                        {book.ingestion_status === "complete"
                          ? "✓ AI Ready"
                          : book.ingestion_status === "processing"
                          ? "⏳ Processing"
                          : "Ready"}
                      </span>
                    </td>
                    <td style={tdCenterStyle}>
                      <span style={dateSpanStyle}>
                        {book.created_at
                          ? new Date(book.created_at).toLocaleDateString(undefined, {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })
                          : "—"}
                      </span>
                    </td>
                    <td style={tdActionsStyle}>
                      <Link to={`/reader/${book.id}`} style={actionReadBtnStyle}>
                        Read
                      </Link>
                      <button
                        type="button"
                        onClick={() => setEditingBook(book)}
                        style={actionIconBtnStyle}
                        title="Edit metadata & cover"
                        aria-label="Edit metadata"
                      >
                        ✏️
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingBook(book)}
                        style={actionIconBtnStyle}
                        title="Delete book"
                        aria-label="Delete book"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </main>

      <DeleteBookModal
        book={deletingBook}
        isOpen={Boolean(deletingBook)}
        onClose={() => setDeletingBook(null)}
        onDeleted={(deletedBookId) =>
          setBooks((currentBooks) => currentBooks.filter((entry) => entry.id !== deletedBookId))
        }
      />

      <MetadataEditorModal
        book={editingBook}
        isOpen={Boolean(editingBook)}
        onClose={() => setEditingBook(null)}
        onSaved={handleMetadataSaved}
      />
    </div>
  );
}

function getDisplayName(user) {
  if (!user) {
    return "Profile";
  }

  if (user.display_name) {
    return user.display_name;
  }

  if (user.email) {
    return user.email.split("@")[0];
  }

  return "Profile";
}

const pageStyle = {
  minHeight: "100vh",
  padding: "0 0 2rem",
  background:
    "radial-gradient(circle at top, rgba(255,255,255,0.5), transparent 32%), linear-gradient(180deg, #f6f0e4 0%, #eee1cd 100%)",
  cursor: "default",
  caretColor: "transparent",
};

const navBarStyle = {
  minHeight: 64,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "1rem",
  padding: "0 2rem",
  marginBottom: "2rem",
  background: "rgba(255, 250, 243, 0.92)",
  borderBottom: "1px solid rgba(115, 98, 74, 0.16)",
  boxShadow: "0 12px 32px rgba(44, 33, 20, 0.08)",
  position: "sticky",
  top: 0,
  zIndex: 10,
  backdropFilter: "blur(14px)",
};

const brandStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "0.7rem",
  color: "#17313e",
  textDecoration: "none",
  fontSize: "1.2rem",
  fontWeight: 800,
};

const brandIconStyle = {
  width: 38,
  height: 38,
  borderRadius: 12,
};

const navActionsStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.75rem",
};

const topUploadContainerStyle = {
  position: "relative",
};

const topUploadErrorStyle = {
  position: "absolute",
  top: "calc(100% + 0.4rem)",
  right: 0,
  width: 280,
  margin: 0,
  padding: "0.65rem 0.75rem",
  borderRadius: 14,
  background: "#fff8ef",
  boxShadow: "0 12px 30px rgba(44, 33, 20, 0.14)",
  zIndex: 5,
};

const iconButtonStyle = {
  display: "grid",
  placeItems: "center",
  width: 42,
  height: 42,
  border: "none",
  borderRadius: 999,
  background: "#17313e",
  color: "#fff8ef",
  fontSize: "1.9rem",
  fontWeight: 300,
  lineHeight: 1,
  cursor: "pointer",
  boxShadow: "0 12px 28px rgba(23, 49, 62, 0.22)",
};

const profileMenuWrapStyle = {
  position: "relative",
};

const profileButtonStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "0.6rem",
  border: "1px solid rgba(23, 49, 62, 0.14)",
  borderRadius: 999,
  padding: "0.35rem 0.75rem 0.35rem 0.35rem",
  background: "#fff8ef",
  color: "#17313e",
  fontWeight: 700,
  cursor: "pointer",
  boxShadow: "0 12px 28px rgba(44, 33, 20, 0.08)",
};

const profileAvatarStyle = {
  display: "grid",
  placeItems: "center",
  width: 34,
  height: 34,
  borderRadius: 999,
  background: "#d9b77f",
  color: "#17313e",
  fontWeight: 800,
};

const profileNameStyle = {
  maxWidth: 180,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const profileMenuStyle = {
  position: "absolute",
  top: 54,
  right: 0,
  minWidth: 230,
  display: "flex",
  flexDirection: "column",
  padding: "0.5rem",
  borderRadius: 18,
  background: "#fffaf3",
  border: "1px solid rgba(115, 98, 74, 0.14)",
  boxShadow: "0 24px 50px rgba(25, 23, 19, 0.22)",
  zIndex: 4,
};

const profileSummaryStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.2rem",
  padding: "0.65rem 0.75rem 0.75rem",
  borderBottom: "1px solid rgba(115, 98, 74, 0.14)",
  marginBottom: "0.35rem",
};

const profileSummaryNameStyle = {
  color: "#17313e",
  fontWeight: 800,
};

const profileSummaryEmailStyle = {
  color: "#8b8278",
  fontSize: "0.86rem",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const profileMenuItemStyle = {
  border: "none",
  borderRadius: 12,
  background: "transparent",
  color: "#2d302f",
  textAlign: "left",
  textDecoration: "none",
  padding: "0.7rem 0.85rem",
  fontWeight: 700,
  cursor: "pointer",
  font: "inherit",
};

const dangerProfileMenuItemStyle = {
  ...profileMenuItemStyle,
  color: "#a11d1d",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
  gap: "1.35rem",
  padding: "0 2rem",
};

function getInitials(title) {
  const words = (title || "Book")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);
  return words.map((word) => word[0]?.toUpperCase() || "").join("") || "BK";
}

const toolbarStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-end",
  padding: "0 2rem 1.5rem",
  flexWrap: "wrap",
  gap: "1rem",
};

const pageTitleStyle = {
  margin: 0,
  fontSize: "2rem",
  fontFamily: "Georgia, serif",
  color: "#201a14",
  fontWeight: 700,
};

const pageSubtitleStyle = {
  margin: "0.25rem 0 0",
  fontSize: "0.9rem",
  color: "#74695d",
};

const toolbarActionsStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.75rem",
};

const viewToggleWrapStyle = {
  display: "flex",
  background: "#e8ded2",
  padding: "3px",
  borderRadius: "12px",
  gap: "2px",
};

const viewToggleButtonStyle = {
  border: "none",
  background: "transparent",
  color: "#6b5d4f",
  padding: "0.45rem 0.85rem",
  borderRadius: "9px",
  fontSize: "0.82rem",
  fontWeight: 600,
  cursor: "pointer",
  transition: "all 0.15s ease",
};

const activeViewToggleButtonStyle = {
  background: "#ffffff",
  color: "#241e17",
  boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
};

const loadingStateStyle = {
  padding: "2rem",
  textAlign: "center",
  color: "#74695d",
};

const tableContainerStyle = {
  margin: "0 2rem",
  background: "#ffffff",
  borderRadius: "18px",
  border: "1px solid rgba(115, 98, 74, 0.16)",
  boxShadow: "0 4px 20px rgba(0, 0, 0, 0.04)",
  overflowX: "auto",
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "0.92rem",
  color: "#282119",
};

const tableHeadRowStyle = {
  background: "#f8f4ee",
  borderBottom: "1px solid rgba(115, 98, 74, 0.14)",
};

const thStyle = {
  padding: "0.85rem 1rem",
  fontSize: "0.75rem",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "#7e6c5a",
  fontWeight: 700,
  textAlign: "center",
};

const tableRowStyle = {
  borderBottom: "1px solid rgba(115, 98, 74, 0.08)",
  transition: "background 0.1s ease",
};

const tdCoverStyle = {
  padding: "0.6rem 1rem",
  width: "56px",
};

const coverLinkStyle = {
  display: "block",
  textDecoration: "none",
};

const tableCoverImgStyle = {
  width: "38px",
  height: "52px",
  objectFit: "cover",
  borderRadius: "6px",
  boxShadow: "0 2px 6px rgba(0,0,0,0.12)",
  display: "block",
};

const tableCoverFallbackStyle = {
  width: "38px",
  height: "52px",
  borderRadius: "6px",
  background: "linear-gradient(135deg, #c9a779, #6d4a2d)",
  color: "#fff",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "0.75rem",
  fontWeight: 700,
};

const tdMainStyle = {
  padding: "0.6rem 1rem",
};

const bookTitleLinkStyle = {
  display: "block",
  fontSize: "1rem",
  fontWeight: 700,
  color: "#1e1710",
  textDecoration: "none",
  marginBottom: "0.15rem",
};

const bookAuthorSpanStyle = {
  display: "block",
  fontSize: "0.85rem",
  color: "#74695d",
  fontStyle: "italic",
};

const tdCenterStyle = {
  padding: "0.6rem 1rem",
  textAlign: "center",
};

const formatBadgeStyle = {
  fontSize: "0.72rem",
  fontWeight: 700,
  color: "#4e4336",
  background: "#ece5d8",
  padding: "0.2rem 0.5rem",
  borderRadius: "6px",
};

const seriesTableBadgeStyle = {
  fontSize: "0.78rem",
  fontWeight: 600,
  color: "#7e5229",
  background: "#f4ebd9",
  border: "1px solid rgba(126, 82, 41, 0.2)",
  padding: "0.2rem 0.6rem",
  borderRadius: "8px",
  whiteSpace: "nowrap",
  display: "inline-block",
  maxWidth: "180px",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const emptySeriesSpanStyle = {
  color: "#a59c90",
  fontSize: "0.85rem",
};

const statusBadgeStyle = {
  fontSize: "0.74rem",
  fontWeight: 600,
  padding: "0.2rem 0.6rem",
  borderRadius: "8px",
  display: "inline-block",
};

const dateSpanStyle = {
  fontSize: "0.82rem",
  color: "#7e7468",
};

const tdActionsStyle = {
  padding: "0.6rem 1rem",
  textAlign: "right",
  whiteSpace: "nowrap",
};

const actionReadBtnStyle = {
  background: "#1c323f",
  color: "#ffffff",
  textDecoration: "none",
  padding: "0.35rem 0.85rem",
  borderRadius: "8px",
  fontSize: "0.8rem",
  fontWeight: 600,
  marginRight: "0.5rem",
  display: "inline-block",
};

const actionIconBtnStyle = {
  background: "transparent",
  border: "1px solid rgba(115, 98, 74, 0.2)",
  borderRadius: "8px",
  padding: "0.3rem 0.5rem",
  fontSize: "0.85rem",
  cursor: "pointer",
  marginLeft: "0.35rem",
};
