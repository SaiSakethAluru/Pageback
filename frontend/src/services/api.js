const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (${response.status}): ${body}`);
  }
  return response.json();
}

export async function uploadBook(file, userId) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", userId);
  return request("/api/v1/books/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getBookStatus(bookId) {
  return request(`/api/v1/books/${bookId}/status`);
}

export async function getBooks(userId) {
  return request(`/api/v1/books?user_id=${encodeURIComponent(userId)}`);
}

export async function savePosition(bookId, userId, positionCfi, positionChar) {
  return request(`/api/v1/positions/${bookId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      position_cfi: positionCfi,
      position_char: positionChar,
    }),
  });
}

export async function getPosition(bookId, userId) {
  return request(`/api/v1/positions/${bookId}?user_id=${encodeURIComponent(userId)}`);
}

export async function getRecap(bookId, userId, positionChar, level) {
  const headers = {
    "Content-Type": "application/json",
  };
  const devApiKey = localStorage.getItem("dev_openai_key");
  if (devApiKey) {
    headers["X-Dev-Api-Key"] = devApiKey;
  }

  return request("/api/v1/recap", {
    method: "POST",
    headers,
    body: JSON.stringify({
      book_id: bookId,
      user_id: userId,
      position_char: positionChar,
      level,
    }),
  });
}

export async function getRecapLevels() {
  return request("/api/v1/recap/levels");
}
