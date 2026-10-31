"use client";

import { FileText, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";

import { AppShell, RequireAuth, SearchInput } from "@/components/app-shell";
import { TemplateDialog } from "@/components/template-dialog";
import { Badge, Card, EmptyState, Spinner } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiGet, apiPost } from "@/lib/api";
import type { Document, DocumentSummary, Template } from "@/lib/types";
import { statusMeta } from "@/lib/status";

export default function DashboardPage() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}

function Dashboard() {
  const router = useRouter();
  const [documents, setDocuments] = React.useState<DocumentSummary[] | null>(null);
  const [templates, setTemplates] = React.useState<Template[]>([]);
  const [query, setQuery] = React.useState("");
  const [status, setStatus] = React.useState("");
  const [activeTemplate, setActiveTemplate] = React.useState<Template | null>(null);
  const [creating, setCreating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    apiGet<Template[]>("/api/templates").then(setTemplates).catch(() => undefined);
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const params = new URLSearchParams();
        if (query) params.set("q", query);
        if (status) params.set("status", status);
        const list = await apiGet<{ items: DocumentSummary[]; total: number }>(
          `/api/documents?${params.toString()}`,
        );
        if (!cancelled) {
          setDocuments(list.items);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load");
      }
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query, status]);

  async function newBlank() {
    setCreating(true);
    setError(null);
    try {
      const document = await apiPost<Document>("/api/documents", {
        title: "Untitled document",
      });
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create document");
      setCreating(false);
    }
  }

  const statuses = [
    { value: "", label: "All statuses" },
    { value: "draft", label: "Draft" },
    { value: "in_review", label: "In review" },
    { value: "final", label: "Final" },
    { value: "archived", label: "Archived" },
  ];

  return (
    <AppShell
      search={
        <SearchInput
          value={query}
          onChange={setQuery}
          placeholder="Search documents…"
        />
      }
      actions={
        <Button variant="primary" onClick={newBlank} disabled={creating}>
          <Plus size={15} />
          <span className="hidden sm:inline">New document</span>
        </Button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h1 className="font-display text-[20px] font-semibold text-ink">
              Your documents
            </h1>
            <div className="flex gap-1 rounded-lg border border-line bg-white p-0.5 shadow-l1">
              {statuses.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setStatus(item.value)}
                  className={
                    status === item.value
                      ? "rounded-md bg-lavender px-2.5 py-1 font-display text-[12px] font-medium text-brand"
                      : "rounded-md px-2.5 py-1 font-display text-[12px] font-medium text-muted transition-colors hover:text-ink"
                  }
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {error ? (
            <p className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
              {error}
            </p>
          ) : null}

          {documents === null ? (
            <div className="flex justify-center py-16">
              <Spinner />
            </div>
          ) : documents.length === 0 ? (
            <EmptyState
              title={query ? "No documents match" : "No documents yet"}
              description={
                query
                  ? "Try a different search term or clear the status filter."
                  : "Start from a template, or create a blank document and let AI draft the first pass."
              }
              action={
                <div className="flex gap-2">
                  <Button variant="primary" onClick={newBlank}>
                    <Plus size={15} /> New document
                  </Button>
                  <Button onClick={() => router.push("/templates")}>
                    Browse templates
                  </Button>
                </div>
              }
            />
          ) : (
            <Card className="divide-y divide-line overflow-hidden">
              {documents.map((doc) => (
                <button
                  key={doc.id}
                  type="button"
                  onClick={() => router.push(`/documents/${doc.id}`)}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-canvas"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-line bg-canvas text-muted">
                    <FileText size={15} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-display text-[14px] font-medium text-ink">
                      {doc.title}
                    </span>
                    <span className="block text-[12.5px] text-subtle">
                      {doc.wordCount} words · {doc.versionCount} versions ·
                      updated {new Date(doc.updatedAt).toLocaleString()}
                    </span>
                  </span>
                  <Badge className={statusMeta(doc.status).className}>
                    {statusMeta(doc.status).label}
                  </Badge>
                </button>
              ))}
            </Card>
          )}
        </section>

        <aside>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-[16px] font-semibold text-ink">
              Start from a template
            </h2>
            <button
              type="button"
              onClick={() => router.push("/templates")}
              className="font-display text-[12.5px] font-medium text-brand hover:underline"
            >
              See all
            </button>
          </div>

          <div className="space-y-2">
            {templates.slice(0, 5).map((template) => (
              <button
                key={template.id}
                type="button"
                onClick={() => setActiveTemplate(template)}
                className="w-full rounded-xl border border-line bg-white p-3 text-left shadow-l1 transition-colors hover:border-brand/40 hover:bg-lavender/40"
              >
                <span className="font-display text-[13.5px] font-semibold text-ink">
                  {template.name}
                </span>
                <span className="mt-0.5 block text-[12.5px] leading-5 text-muted">
                  {template.description}
                </span>
              </button>
            ))}
            {templates.length === 0 ? (
              <div className="rounded-xl border border-dashed border-line bg-white p-4 text-[13px] text-muted">
                Loading templates…
              </div>
            ) : null}
          </div>
        </aside>
      </div>

      <TemplateDialog
        template={activeTemplate}
        onClose={() => setActiveTemplate(null)}
      />
    </AppShell>
  );
}
