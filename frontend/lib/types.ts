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
  role: string;
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
  employeeId?: string | null;
  candidateId?: string | null;
  category?: string;
  documentType?: string;
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

// ============================================================================
// HRMS & Recruitment Types
// ============================================================================

export type Department = {
  id: string;
  name: string;
  code: string;
  description: string;
  managerId: string | null;
  createdAt: string;
  employeeCount: number;
};

export type Employee = {
  id: string;
  employeeCode: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  jobTitle: string;
  departmentId: string | null;
  departmentName: string | null;
  managerId: string | null;
  managerName: string | null;
  employmentStatus: "active" | "on_leave" | "terminated" | "onboarding";
  employmentType: "full_time" | "part_time" | "contractor" | "intern";
  hireDate: string | null;
  createdAt: string;
  salary?: number | null;
  currency?: string;
  notes?: string;
  documentCount?: number;
};

export type JobPosting = {
  id: string;
  title: string;
  departmentId: string | null;
  departmentName: string | null;
  employmentType: string;
  location: string;
  salaryRange: string | null;
  description: string;
  requirements: string;
  status: "draft" | "open" | "closed";
  createdAt: string;
  updatedAt: string;
  applicantCount: number;
};

export type CandidateApplication = {
  id: string;
  candidateId: string;
  jobPostingId: string;
  jobTitle: string | null;
  stage: "applied" | "screening" | "interview" | "offer" | "hired" | "rejected";
  rating: number | null;
  notes: string;
  offerDocumentId: string | null;
  createdAt: string;
  updatedAt: string;
};

export type Candidate = {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  resumeUrl: string | null;
  linkedinUrl: string | null;
  source: string;
  notes: string;
  createdAt: string;
  applications: CandidateApplication[];
};

