const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (${response.status}): ${body}`);
  }
  return response.json();
}

export function getGoogleLoginUrl() {
  return `${API_BASE_URL}/api/v1/auth/google/start`;
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

export async function getBooks() {
  return request("/api/v1/books/", {
    credentials: "include",
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

export async function getRecap(bookId, positionChar, level) {
  const headers = {
    "Content-Type": "application/json",
  };
  const devApiKey = localStorage.getItem("dev_openai_key");
  if (devApiKey) {
    headers["X-Dev-Api-Key"] = devApiKey;
  }

  return request("/api/v1/recap", {
    method: "POST",
    credentials: "include",
    headers,
    body: JSON.stringify({
      book_id: bookId,
      position_char: positionChar,
      level,
    }),
  });
}

export async function getRecapLevels() {
  return request("/api/v1/recap/levels", {
    credentials: "include",
  });
}
