"use client";

/** Catches anything that escapes component-level handling: window "error",
 * unhandled promise rejections, and failed resources (scripts, images).
 * Mounted once in the root layout; renders nothing.
 */

import { useEffect } from "react";

import { reportError } from "@/lib/client-log";

export function ErrorReporter() {
  useEffect(() => {
    const onError = (event: ErrorEvent) => {
      // Uncaught throw on window: the event carries the error.
      if (event.error || event.message) {
        reportError(event.error ?? event.message, {
          source: event.filename ? `${event.filename}:${event.lineno}` : "window",
        });
      }
    };
    const onRejection = (event: PromiseRejectionEvent) => {
      const reason =
        event.reason instanceof Error
          ? event.reason
          : `Unhandled promise rejection: ${String(event.reason)}`;
      reportError(reason, { source: "unhandledrejection" });
    };
    const onResourceError = (event: Event) => {
      const target = event.target;
      if (target instanceof HTMLScriptElement) {
        reportError(`Resource failed to load: ${target.src}`, { source: "resource" });
      } else if (target instanceof HTMLLinkElement) {
        reportError(`Resource failed to load: ${target.href}`, { source: "resource" });
      }
    };

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    window.addEventListener("error", onResourceError, true);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
      window.removeEventListener("error", onResourceError, true);
    };
  }, []);

  return null;
}
