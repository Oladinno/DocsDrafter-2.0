/** Status pill presentation, shared by list rows and the editor. */

export type StatusKey = "draft" | "in_review" | "final" | "archived";

const META: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-white border-line text-muted" },
  in_review: {
    label: "In review",
    className: "bg-amber-50 border-amber-200 text-amber-700",
  },
  final: {
    label: "Final",
    className: "bg-emerald-50 border-emerald-200 text-emerald-700",
  },
  archived: {
    label: "Archived",
    className: "bg-surface-container border-line text-muted",
  },
};

export function statusMeta(status: string) {
  return META[status] ?? { label: status, className: "bg-white border-line text-muted" };
}

export const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "in_review", label: "In review" },
  { value: "final", label: "Final" },
  { value: "archived", label: "Archived" },
];
