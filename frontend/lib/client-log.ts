/** Report browser-side errors to the backend so they show up in Railway's
 * logs alongside server output (POST /api/logs).
 *
 * Fire-and-forget: never throws, and converts its own upload failures into at
 * most one console.warn so logging cannot start an error loop.
 */

import { apiPost } from "@/lib/api";

function truncate(value: string, max: number): string {
  return value.length <= max ? value : `${value.slice(0, max)}...`;
}

function describe(error: unknown): string {
  if (error instanceof Error) return error.message || error.name;
  if (typeof error === "string") return error;
  try {
    return JSON.stringify(error) ?? String(error);
  } catch {
    return String(error);
  }
}

function extractStack(error: unknown): string | null {
  return error instanceof Error && error.stack ? truncate(error.stack, 8000) : null;
}

export function logClient(
  level: "error" | "warn" | "info",
  message: string,
  error?: unknown,
  extra?: Record<string, string>,
): void {
  const text = truncate(message, 2000);
  // firefox: https://developer.mozilla.org/docs/Web/API/Window/error_event
  const withExtra = extra
    ? `${text} | ${Object.entries(extra)
        .map(([key, value]) => `${key}=${value}`)
        .join(" ")}`
    : text;

  if (level === "error") console.error(withExtra, error ?? "");
  else console.warn(withExtra, error ?? "");

  void apiPost("/api/logs", {
    level,
    message: text,
    stack: error === undefined ? null : extractStack(error),
    url: typeof window !== "undefined" ? truncate(window.location.href, 2048) : null,
    userAgent:
      typeof navigator !== "undefined" ? truncate(navigator.userAgent, 400) : null,
  }).catch(() => {
    // Backend unreachable (e.g. offline) or payload rejected: this attempt is
    // lost, the browser copy above is always kept.
    console.warn("client log could not be delivered");
  });
}

/** Report a caught/uncaught error: console.error plus a copy to the backend. */
export function reportError(error: unknown, extra?: Record<string, string>): void {
  logClient("error", describe(error), error, extra);
}
