import * as React from "react";

import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-line bg-white shadow-l1",
        className,
      )}
      {...props}
    />
  );
}

export function Badge({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex h-[22px] items-center rounded-full border px-2 font-display text-[11px] font-medium",
        className,
      )}
      {...props}
    />
  );
}

export function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="rounded-sm border border-line bg-canvas px-1.5 py-0.5 font-display text-[11px] font-medium text-muted">
      {children}
    </kbd>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-line border-t-brand",
        className,
      )}
      role="status"
      aria-label="Loading"
    />
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-line bg-white px-6 py-14 text-center">
      <h3 className="font-display text-[16px] font-semibold text-ink">{title}</h3>
      <p className="mt-1 max-w-md text-[14px] text-muted">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
