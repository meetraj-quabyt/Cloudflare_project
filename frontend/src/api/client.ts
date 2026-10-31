const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  get: (path: string) => apiFetch(path),
  post: (path: string, body?: unknown) => apiFetch(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  del: (path: string) => apiFetch(path, { method: "DELETE" }),
};