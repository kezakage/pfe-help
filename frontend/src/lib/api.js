/**
 * Tiny API client for the PatrimoineHub backend.
 * - JWT in localStorage with auto-refresh on 401.
 * - JSON by default; supports FormData for uploads (Content-Type omitted).
 */
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "pfe.access";
const REFRESH_KEY = "pfe.refresh";

export const tokens = {
  get access() {
    return localStorage.getItem(TOKEN_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(access, refresh) {
    if (access) localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

let refreshPromise = null;

async function refreshAccess() {
  if (!tokens.refresh) return false;
  if (!refreshPromise) {
    refreshPromise = fetch(`${BASE}/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh }),
    })
      .then(async (r) => {
        if (!r.ok) {
          tokens.clear();
          return false;
        }
        const data = await r.json();
        tokens.set(data.access, data.refresh || tokens.refresh);
        return true;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function request(
  path,
  { method = "GET", body, query, headers, raw } = {},
) {
  const url = new URL(path.startsWith("http") ? path : `${BASE}${path}`);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v === undefined || v === null || v === "") return;
      if (Array.isArray(v)) {
        v.forEach((item) => {
          if (item !== undefined && item !== null && item !== "")
            url.searchParams.append(k, item);
        });
      } else {
        url.searchParams.append(k, v);
      }
    });
  }

  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  const finalHeaders = { Accept: "application/json", ...(headers || {}) };
  if (!isForm && body !== undefined)
    finalHeaders["Content-Type"] = "application/json";
  if (tokens.access) finalHeaders.Authorization = `Bearer ${tokens.access}`;

  const opts = {
    method,
    headers: finalHeaders,
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  };

  let res = await fetch(url, opts);

  if (res.status === 401 && tokens.refresh) {
    const ok = await refreshAccess();
    if (ok) {
      finalHeaders.Authorization = `Bearer ${tokens.access}`;
      res = await fetch(url, opts);
    }
  }

  if (raw) return res;
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  const isJson = ct.includes("application/json");
  const data = isJson ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    const err = new Error(
      (isJson && data?.detail) ||
        (isJson && JSON.stringify(data)) ||
        `HTTP ${res.status}`,
    );
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  get: (path, query) => request(path, { query }),
  post: (path, body) => request(path, { method: "POST", body }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  put: (path, body) => request(path, { method: "PUT", body }),
  del: (path) => request(path, { method: "DELETE" }),
  upload: (path, formData) => request(path, { method: "POST", body: formData }),
};

// ---------- domain helpers ----------

export const auth = {
  login: (email, password) => api.post("/auth/login/", { email, password }),
  refresh: (refresh) => api.post("/auth/refresh/", { refresh }),
  register: (data) => api.post("/auth/register/", data),
  me: () => api.get("/auth/me/"),
  // OAuth2 / SSO
  socialProviders: () => api.get("/auth/social/providers/"),
  socialLogin: (provider, code, redirect_uri) =>
    api.post(`/auth/social/${provider}/`, { code, redirect_uri }),
  updateMe: (id, data) => api.patch(`/auth/me/${id}/`, data),
};

export const heritage = {
  resources: (filters) => api.get("/heritage/resources/", filters),
  resource: (id) => api.get(`/heritage/resources/${id}/`),
  createResource: (data) => api.post("/heritage/resources/", data),
  deleteResource: (id) => api.del(`/heritage/resources/${id}/`),
  fts: (q) => api.get("/heritage/resources/full-text/", { q }),
  search: (params) => api.get("/heritage/resources/search/", params),
  suggest: (q, size = 10) =>
    api.get("/heritage/resources/suggest/", { q, size }),
  geojson: (filters) => api.get("/heritage/resources/geojson/", filters),

  projects: (filters) => api.get("/heritage/projects/", filters),
  project: (id) => api.get(`/heritage/projects/${id}/`),
  createProject: (data) => api.post("/heritage/projects/", data),
  updateProject: (id, data) => api.patch(`/heritage/projects/${id}/`, data),
  deleteProject: (id) => api.del(`/heritage/projects/${id}/`),
  publish: (id) => api.post(`/heritage/projects/${id}/publish/`),
  members: (id) => api.get(`/heritage/projects/${id}/members/`),
  addMember: (id, data) => api.post(`/heritage/projects/${id}/members/`, data),
};

export const pages = {
  list: (project) => api.get("/pages/", { project }),
  get: (id) => api.get(`/pages/${id}/`),
  create: (data) => api.post("/pages/", data),
  history: (id) => api.get(`/pages/versions/history/<id>/`),
  versions: (page) => api.get("/pages/versions/", { page }),
  createVersion: (data) => api.post("/pages/versions/", data),
  restore: (versionId) => api.post(`/pages/versions/${versionId}/restore/`),
  diff: (a, b) => api.get("/pages/versions/diff/", { a, b }),
};

export const media = {
  list: (project) => api.get("/media/", { project }),
  listImages: (project) => api.get("/media/", { project, media_type: "image" }),
  list3D: (project) => api.get("/media/", { project, media_type: "model_3d" }),
  retrieve: (id) => api.get(`/media/${id}/`),
  upload: (formData) => api.upload("/media/", formData),
  annotations: (filters) => api.get("/media/annotations/", filters),
  createAnnotation: (data) => api.post("/media/annotations/", data),
  deleteAnnotation: (id) => api.del(`/media/annotations/${id}/`),
  validateAnnotation: (id) =>
    api.post(`/media/annotations/${id}/validate_annotation/`),
  rejectAnnotation: (id) => api.post(`/media/annotations/${id}/reject/`),
};

export const discussions = {
  list: (project) => api.get("/discussions/", { project }),
  get: (id) => api.get(`/discussions/${id}/`),
  create: (data) => api.post("/discussions/", data),
  resolve: (id) => api.post(`/discussions/${id}/resolve/`),
  messages: (id) => api.get(`/discussions/${id}/messages/`),
  postMessage: (id, body) => api.post(`/discussions/${id}/messages/`, { body }),
  votes: (id) => api.get(`/discussions/${id}/votes/`),
  vote: (id, choice, comment = "") =>
    api.post(`/discussions/${id}/votes/`, { choice, comment, discussion: id }),
  tally: (id) => api.get(`/discussions/${id}/tally/`),
};

export const exports_ = {
  list: () => api.get("/exports/"),
  create: (data) => api.post("/exports/", data),
  get: (id) => api.get(`/exports/${id}/`),
};

export const notifications = {
  list: () => api.get("/notifications/"),
  unreadCount: () => api.get("/notifications/unread_count/"),
  markRead: (id) => api.post(`/notifications/${id}/mark_read/`),
  markAllRead: () => api.post("/notifications/mark_all_read/"),
};

export const chat = {
  ask: (message, { sessionId, anonKey } = {}) =>
    api.post("/chat/ask/", {
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
      ...(anonKey ? { anon_key: anonKey } : {}),
    }),
  sessions: () => api.get("/chat/sessions/"),
  session: (id) => api.get(`/chat/sessions/${id}/`),
  deleteSession: (id) => api.del(`/chat/sessions/${id}/`),
};

export const adminApi = {
  users: (filters) => api.get("/auth/admin/users/", filters),
  validateUser: (id, action = "approve") =>
    api.post(`/auth/admin/users/${id}/validate/`, { decision: action }),
  suspend: (id) => api.post(`/auth/admin/users/${id}/suspend/`),
  disciplines: () => api.get("/auth/disciplines/"),
  stats: () => api.get("/auth/admin/stats/"),
};

export function mediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  const base = import.meta.env.VITE_MEDIA_URL || "http://localhost:8000";
  return path.startsWith("/") ? `${base}${path}` : `${base}/${path}`;
}
