/** Shared contracts mirroring the FastAPI schemas (camelCase on the wire). */

export type Mark = { type: string; attrs?: Record<string, unknown> };

export type TextNode = {
  type: "text";
  text: string;
  marks?: Mark[];
};

export type ContentNode = {
  type: string;
  attrs?: Record<string, unknown>;
  content?: ContentNode[];
  text?: string;
  marks?: Mark[];
};

export type DocContent = {
  type: "doc";
  content: ContentNode[];
};

export type User = {
  id: string;
  email: string;
  name: string;
  createdAt: string;
};

export type TemplateField = {
  key: string;
  label: string;
  kind?: string;
  required?: boolean;
  placeholder?: string;
  default?: string;
};

export type Template = {
  id: string;
  slug: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  isBuiltin: boolean;
  fields: TemplateField[];
  preview: string;
  structure?: DocContent;
};

export type DocumentSummary = {
  id: string;
  title: string;
  status: string;
  templateId: string | null;
  wordCount: number;
  versionCount: number;
  createdAt: string;
  updatedAt: string;
};

export type Document = DocumentSummary & {
  content: DocContent;
  source: Record<string, string>;
};

export type DocumentVersion = {
  id: string;
  documentId: string;
  versionNumber: number;
  title: string;
  status: string;
  note: string;
  kind: string;
  createdAt: string;
};

export type DocumentStats = {
  words: number;
  characters: number;
  readingMinutes: number;
  versions: number;
  exports: number;
};

export type AIResult = {
  content: DocContent;
  blocks: ContentNode[];
  provider: string;
  plainText: string;
};

export type Job = {
  id: string;
  kind: string;
  status: "pending" | "running" | "succeeded" | "failed";
  payload: Record<string, unknown>;
  result: (AIResult & Record<string, unknown>) | null;
  error: string | null;
  createdAt: string;
  completedAt: string | null;
};

export type ExportRecord = {
  id: string;
  documentId: string;
  format: "docx" | "pdf";
  status: "pending" | "running" | "succeeded" | "failed";
  fileName: string;
  storageBackend: string;
  sizeBytes: number | null;
  renderer: string | null;
  versionNumber: number | null;
  error: string | null;
  createdAt: string;
  completedAt: string | null;
  downloadUrl: string;
};

export const STATUS_META: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-white border-line text-muted" },
  in_review: { label: "In review", className: "bg-amber-50 border-amber-200 text-amber-700" },
  final: { label: "Final", className: "bg-emerald-50 border-emerald-200 text-emerald-700" },
  archived: { label: "Archived", className: "bg-surface-container border-line text-muted" },
};
