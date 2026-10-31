import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "focus-ring h-9 w-full rounded-lg border border-line bg-white px-3 text-[14px] text-ink placeholder:text-subtle shadow-l1 transition-colors disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "focus-ring w-full rounded-lg border border-line bg-white px-3 py-2 text-[14px] text-ink placeholder:text-subtle shadow-l1 transition-colors",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export function Field({
  label,
  hint,
  error,
  children,
  className,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("block", className)}>
      <span className="font-display text-[13px] font-medium text-ink">{label}</span>
      {hint ? <span className="ml-2 text-[12px] text-subtle">{hint}</span> : null}
      <div className="mt-1.5">{children}</div>
      {error ? (
        <span className="mt-1 block text-[12.5px] text-danger">{error}</span>
      ) : null}
    </label>
  );
}
