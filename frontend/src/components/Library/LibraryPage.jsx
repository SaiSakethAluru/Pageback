import { useEffect, useState } from "react";

import supabase from "../../services/supabaseClient";
import * as api from "../../services/api";
import BookCard from "./BookCard";
import UploadButton from "./UploadButton";

export default function LibraryPage() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadBooks() {
    setLoading(true);
    const {
      data: { user },
    } = await supabase.auth.getUser();
    const response = await api.getBooks(user.id);
    setBooks(response);
    setLoading(false);
  }

  useEffect(() => {
    loadBooks().catch(() => setLoading(false));
  }, []);

  return (
    <div style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={{ margin: 0 }}>Your Library</h1>
          <p style={{ margin: "0.5rem 0 0", color: "#69645e" }}>
            Upload EPUBs and pick up where you left off.
          </p>
        </div>
        <UploadButton onUploadComplete={loadBooks} />
      </div>

      {loading ? <p>Loading books...</p> : null}
      {!loading && books.length === 0 ? <p>No books yet. Upload your first EPUB.</p> : null}

      <div style={gridStyle}>
        {books.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </div>
  );
}

const pageStyle = {
  minHeight: "100vh",
  padding: "2rem",
  background: "linear-gradient(180deg, #f6f1e6 0%, #eee6d8 100%)",
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
  gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
  gap: "1rem",
};
