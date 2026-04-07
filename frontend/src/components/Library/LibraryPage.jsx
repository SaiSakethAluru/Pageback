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
  const profileMenuRef = useRef(null);

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
        {loading ? <p>Loading books...</p> : null}

        {!loading ? (
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
