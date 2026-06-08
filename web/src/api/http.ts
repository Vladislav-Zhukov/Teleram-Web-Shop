export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function withApi(url?: string | null) {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${API_URL}${url}`;
}

function readTokens() {
  return {
    access: localStorage.getItem("access_token") || "",
    refresh: localStorage.getItem("refresh_token") || ""
  };
}

function writeTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function raw<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, init);
  const data = (await r.json().catch(() => ({}))) as any;
  if (!r.ok) {
  const code =
    data?.error ||
    data?.detail?.error ||
    data?.detail?.code ||
    data?.detail ||
    "HTTP_ERROR";

  const message =
    data?.message ||
    data?.detail?.message ||
    (typeof data?.detail === "string" ? data.detail : null) ||
    String(code);

  throw {
    error: code,      // важно: оставляем код в .error (чтобы refresh-логика не сломалась)
    message,          // человеческий текст
    status: r.status,
    raw: data,
  };
}
  return data as T;
}

// refresh + retry once on 401
export async function request<T>(
  path: string,
  init: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth, ...rest } = init;
  const tokens = readTokens();

  const headers = new Headers(rest.headers || {});
  // If body is FormData, browser will set correct multipart boundary.
  const isForm = typeof FormData !== "undefined" && rest.body instanceof FormData;
  if (!isForm) headers.set("Content-Type", "application/json");
  if (auth && tokens.access) headers.set("Authorization", `Bearer ${tokens.access}`);

  try {
    return await raw<T>(path, { ...rest, headers });
  } catch (e: any) {
    if (e?.error === "AUTH_REQUIRED" || e?.error === "INVALID_TOKEN" || e?.error === "INVALID_TOKEN_TYPE") {
      if (!tokens.refresh) throw e;

      const refreshed = await raw<{ access_token: string; refresh_token: string }>(
        "/auth/refresh",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: tokens.refresh })
        }
      );
      writeTokens(refreshed.access_token, refreshed.refresh_token);

      const tokens2 = readTokens();
      const headers2 = new Headers(rest.headers || {});
      const isForm2 = typeof FormData !== "undefined" && rest.body instanceof FormData;
      if (!isForm2) headers2.set("Content-Type", "application/json");
      if (auth && tokens2.access) headers2.set("Authorization", `Bearer ${tokens2.access}`);

      return await raw<T>(path, { ...rest, headers: headers2 });
    }

    if (e?.error === "REFRESH_REVOKED" || e?.error === "INVALID_REFRESH") {
      clearTokens();
    }
    throw e;
  }
}

export const tokenStorage = { readTokens, writeTokens, clearTokens };
