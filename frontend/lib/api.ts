/** HTTP client for the DocsDrafter API.

Credentials (the HttpOnly session cookie) are always sent, and every
state-changing request carries the signed double-submit CSRF token.
*/

/** Same-origin by default: Next proxies `/api/*` to the FastAPI service, so
 * cookies stay first-party. Set NEXT_PUBLIC_API_URL to talk to an API that is
 * not proxied. */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function ensureCsrf(): Promise<string | null> {
  const existing = readCookie("dd_csrf");
  if (existing) return existing;
  try {
    await fetch(`${API_BASE}/api/auth/csrf`, { credentials: "include" });
  } catch {
    return null;
  }
  return readCookie("dd_csrf");
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);

  if (!SAFE_METHODS.has(method)) {
    const token = await ensureCsrf();
    if (token) headers.set("X-CSRF-Token", token);
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      credentials: "include",
    });
  } catch {
    throw new ApiError(0, "Could not reach the API. Is the backend running?");
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    type ApiIssue = { msg?: string; loc?: (string | number)[] };
    type ApiDetail = string | ApiIssue[];
    const detail = (payload as { detail?: ApiDetail } | null)?.detail;
    let message = `Request failed (${response.status})`;
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail) && detail[0]) {
      const first = detail[0];
      message = first.loc
        ? `${first.loc.join(".")}: ${first.msg ?? "invalid value"}`
        : (first.msg ?? "Invalid input");
    }
    throw new ApiError(response.status, message);
  }

  return payload as T;
}

export const apiGet = <T>(path: string) => api<T>(path);
export const apiPost = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
export const apiPatch = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
export const apiDelete = <T = void>(path: string) =>
  api<T>(path, { method: "DELETE" });

/** Absolute URL for a backend download path (ownership is checked server-side). */
export function absoluteUrl(path: string): string {
  if (!path) return "";
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}
