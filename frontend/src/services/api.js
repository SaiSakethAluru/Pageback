const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const body = await response.json();
      throw new Error(body.error || `Request failed (${response.status})`);
    }

    const body = await response.text();
    throw new Error(body || `Request failed (${response.status})`);
  }
  return response.json();
}

export function getGoogleLoginUrl() {
  return `${API_BASE_URL}/api/v1/auth/google/start`;
}

export function getDevLoginUrl(userId) {
  return `${API_BASE_URL}/api/v1/auth/dev-login${userId ? `?user_id=${encodeURIComponent(userId)}` : ""}`;
}

export async function getCurrentUser() {
  return request("/api/v1/auth/me", {
    credentials: "include",
  });
}

export async function logout() {
  return request("/api/v1/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}

export async function uploadBook(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/v1/books/upload", {
    method: "POST",
    body: formData,
    credentials: "include",
  });
}

export async function getBookStatus(bookId) {
  return request(`/api/v1/books/${bookId}/status`, {
    credentials: "include",
  });
}

export async function startIngestion(bookId) {
  return request(`/api/v1/books/${bookId}/ingestion/start`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  });
}

export async function getIngestionRequests() {
  return request("/api/v1/books/ingestion/requests", {
    credentials: "include",
  });
}

export async function pauseIngestion(requestId) {
  return request(`/api/v1/books/ingestion/${requestId}/pause`, {
    method: "POST",
    credentials: "include",
  });
}

export async function resumeIngestion(requestId) {
  return request(`/api/v1/books/ingestion/${requestId}/resume`, {
    method: "POST",
    credentials: "include",
  });
}

export async function cancelIngestion(requestId) {
  return request(`/api/v1/books/ingestion/${requestId}/cancel`, {
    method: "POST",
    credentials: "include",
  });
}

export async function getBooks() {
  return request("/api/v1/books/", {
    credentials: "include",
  });
}

export async function deleteBook(bookId) {
  return request(`/api/v1/books/${bookId}`, {
    method: "DELETE",
    credentials: "include",
  });
}

export async function updateBookMetadata(bookId, metadata) {
  return request(`/api/v1/books/${bookId}/metadata`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(metadata),
  });
}

export async function savePosition(bookId, positionCfi, positionChar) {
  return request(`/api/v1/positions/${bookId}`, {
    method: "PUT",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      position_cfi: positionCfi,
      position_char: positionChar,
    }),
  });
}

export async function getPosition(bookId) {
  return request(`/api/v1/positions/${bookId}`, {
    credentials: "include",
  });
}

export async function getBookFileUrl(bookId) {
  return request(`/api/v1/books/${bookId}/file-url`, {
    credentials: "include",
  });
}

export async function getRecap(bookId, positionChar, level, positionCfi = null) {
  return request("/api/v1/recap/", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      book_id: bookId,
      position_char: positionChar,
      level,
      position_cfi: positionCfi,
    }),
  });
}

export async function getRecapLevels() {
  return request("/api/v1/recap/levels", {
    credentials: "include",
  });
}

export async function lookupContextual(bookId, term, positionChar = 0, positionCfi = null) {
  return request("/api/v1/recap/contextual-lookup", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      book_id: bookId,
      term,
      position_char: positionChar,
      position_cfi: positionCfi,
    }),
  });
}

export async function sendChatMessage(bookId, messages, positionChar = 0, positionCfi = null) {
  return request("/api/v1/recap/chat", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      book_id: bookId,
      messages,
      position_char: positionChar,
      position_cfi: positionCfi,
    }),
  });
}

export async function uploadBookCover(bookId, file) {
  const formData = new FormData();
  formData.append("cover", file);
  return request(`/api/v1/books/${bookId}/cover`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
}

export async function updateBookCoverFromUrl(bookId, coverUrl) {
  return request(`/api/v1/books/${bookId}/cover-from-url`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ cover_url: coverUrl }),
  });
}

export async function fetchOnlineBookMetadata(title, author = "") {
  let query = "";
  if (title && author) {
    query = `title=${encodeURIComponent(title)}&author=${encodeURIComponent(author)}`;
  } else if (title) {
    query = `q=${encodeURIComponent(title)}`;
  } else {
    throw new Error("Title is required to search metadata");
  }

  const response = await fetch(`https://openlibrary.org/search.json?${query}&limit=5`);
  if (!response.ok) {
    throw new Error(`Failed to search OpenLibrary (${response.status})`);
  }
  const data = await response.json();
  const docs = data.docs || [];

  return docs.map((doc) => ({
    title: doc.title,
    author: Array.isArray(doc.author_name) ? doc.author_name.join(", ") : doc.author_name || "",
    firstPublishYear: doc.first_publish_year || null,
    publisher: Array.isArray(doc.publisher) ? doc.publisher[0] : doc.publisher || null,
    coverUrl: doc.cover_i ? `https://covers.openlibrary.org/b/id/${doc.cover_i}-L.jpg` : null,
    isbn: Array.isArray(doc.isbn) ? doc.isbn[0] : null,
  }));
}
