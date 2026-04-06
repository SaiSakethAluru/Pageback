import { useEffect, useState } from "react";

import * as api from "../../services/api";
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

  return (
    <div style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={{ margin: 0 }}>Your Library</h1>
          <p style={{ margin: "0.5rem 0 0", color: "#69645e" }}>
            Upload EPUBs and pick up where you left off.
          </p>
          {user ? <p style={{ margin: "0.5rem 0 0", color: "#8b8278" }}>{user.email}</p> : null}
        </div>
        <div style={actionsStyle}>
          <UploadButton onUploadComplete={loadBooks} />
          <button type="button" onClick={handleLogout} style={logoutStyle}>
            Log Out
          </button>
        </div>
      </div>

      {loading ? <p>Loading books...</p> : null}
      {!loading && books.length === 0 ? <p>No books yet. Upload your first EPUB.</p> : null}

      <div style={gridStyle}>
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            onDelete={setDeletingBook}
            onEditMetadata={setEditingBook}
          />
        ))}
      </div>

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

const pageStyle = {
  minHeight: "100vh",
  padding: "2rem",
  background:
    "radial-gradient(circle at top, rgba(255,255,255,0.5), transparent 32%), linear-gradient(180deg, #f6f0e4 0%, #eee1cd 100%)",
  cursor: "default",
  caretColor: "transparent",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "1rem",
  marginBottom: "2rem",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
  gap: "1.35rem",
};

const actionsStyle = {
  display: "flex",
  alignItems: "flex-start",
  gap: "0.75rem",
};

const logoutStyle = {
  border: "1px solid #c9beae",
  borderRadius: 999,
  padding: "0.8rem 1rem",
  background: "#fff8ef",
  color: "#17313e",
  fontWeight: 600,
  cursor: "pointer",
};
