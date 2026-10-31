"use client";

import type { Editor } from "@tiptap/react";
import { useParams, useRouter } from "next/navigation";
import * as React from "react";

import { AppShell, RequireAuth } from "@/components/app-shell";
import { DocumentEditor } from "@/components/editor/document-editor";
import { AiPanel } from "@/components/editor/ai-panel";
import { ExportsPanel } from "@/components/editor/exports-panel";
import { VersionsPanel } from "@/components/editor/versions-panel";
import { Spinner } from "@/components/ui/card";
import { apiGet, apiPatch } from "@/lib/api";
import type { Document as DocumentModel, DocContent } from "@/lib/types";
import { STATUS_OPTIONS, statusMeta } from "@/lib/status";
import { cn, relativeTime } from "@/lib/utils";

type Tab = "ai" | "versions" | "exports";

export default function DocumentPage() {
  return (
    <RequireAuth>
      <DocumentWorkspace />
    </RequireAuth>
  );
}

function DocumentWorkspace() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const documentId = params.id;

  const [doc, setDoc] = React.useState<DocumentModel | null>(null);
  const [content, setContent] = React.useState<DocContent | null>(null);
  const [saveState, setSaveState] = React.useState<"saved" | "saving" | "error">(
    "saved",
  );
  const [selection, setSelection] = React.useState("");
  const [tab, setTab] = React.useState<Tab>("ai");
  const [versionsKey, setVersionsKey] = React.useState(0);
  const [error, setError] = React.useState<string | null>(null);
  const [panelOpen, setPanelOpen] = React.useState(true);
  const [editor, setEditor] = React.useState<Editor | null>(null);

  const loaded = React.useRef(false);

  React.useEffect(() => {
    let cancelled = false;
    apiGet<DocumentModel>(`/api/documents/${documentId}`)
      .then((data) => {
        if (cancelled) return;
        setDoc(data);
        setContent(data.content);
        loaded.current = true;
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Document not found");
          if (err instanceof Error && /not found/i.test(err.message)) {
            router.replace("/dashboard");
          }
        }
      });
    return () => {
      cancelled = true;
    };
  }, [documentId, router]);

  // Debounced autosave of document content.
  React.useEffect(() => {
    if (!loaded.current || !content || !doc) return;
    if (JSON.stringify(content) === JSON.stringify(doc.content)) return;

    const timer = window.setTimeout(async () => {
      try {
        const updated = await apiPatch<DocumentModel>(
          `/api/documents/${documentId}`,
          { content },
        );
        setDoc((previous) =>
          previous
            ? {
                ...updated,
                versionCount: updated.versionCount,
              }
            : updated,
        );
        setSaveState("saved");
        if (updated.versionCount !== doc.versionCount) {
          setVersionsKey((key) => key + 1);
        }
      } catch (err) {
        setSaveState("error");
        setError(err instanceof Error ? err.message : "Autosave failed");
      }
    }, 1200);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content]);

  async function patch(fields: Partial<{ title: string; status: string }>) {
    try {
      const updated = await apiPatch<DocumentModel>(
        `/api/documents/${documentId}`,
        fields,
      );
      setDoc((previous) => ({ ...updated, content: previous?.content ?? updated.content }));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update");
    }
  }

  function reload(updated: DocumentModel) {
    loaded.current = false;
    setDoc(updated);
    setContent(updated.content);
    editor?.commands.setContent(updated.content as never);
    window.setTimeout(() => {
      loaded.current = true;
    }, 0);
    setVersionsKey((key) => key + 1);
  }

  async function refreshDocument() {
    try {
      const fresh = await apiGet<DocumentModel>(`/api/documents/${documentId}`);
      reload(fresh);
    } catch {
      setVersionsKey((key) => key + 1);
    }
  }

  if (!doc) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        {error ? (
          <p className="text-[14px] text-danger">{error}</p>
        ) : (
          <Spinner className="h-6 w-6" />
        )}
      </div>
    );
  }

  const status = statusMeta(doc.status);
  const tabs: { id: Tab; label: string }[] = [
    { id: "ai", label: "Assistant" },
    { id: "versions", label: "Versions" },
    { id: "exports", label: "Export" },
  ];

  return (
    <AppShell
      actions={
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "font-display text-[11.5px] font-medium",
              saveState === "error" ? "text-danger" : "text-subtle",
            )}
          >
            {saveState === "saving"
              ? "Saving…"
              : saveState === "error"
                ? "Save failed"
                : `Saved ${relativeTime(doc.updatedAt)}`}
          </span>
          <button
            type="button"
            onClick={() => setPanelOpen((open) => !open)}
            className="rounded-md border border-line bg-white px-2 py-1 font-display text-[12px] font-medium text-muted shadow-l1 transition-colors hover:text-ink"
          >
            {panelOpen ? "Hide panel" : "Show panel"}
          </button>
        </div>
      }
    >
      <div
        className={cn(
          "grid gap-6",
          panelOpen ? "lg:grid-cols-[minmax(0,1fr)_360px]" : "lg:grid-cols-1",
        )}
      >
        <section className="min-w-0">
          <div className="mx-auto w-full max-w-[860px]">
            <div className="mb-3 flex flex-wrap items-center gap-3">
              <input
                value={doc.title}
                onChange={(event) =>
                  setDoc((previous) =>
                    previous ? { ...previous, title: event.target.value } : previous,
                  )
                }
                onBlur={() => patch({ title: doc.title })}
                aria-label="Document title"
                className="min-w-0 flex-1 rounded-md border border-transparent bg-transparent px-1 py-1 font-display text-[22px] font-semibold tracking-tight text-ink transition-colors hover:border-line focus:border-brand focus:outline-none"
              />
              <select
                value={doc.status}
                onChange={(event) => patch({ status: event.target.value })}
                aria-label="Document status"
                className={cn(
                  "h-[22px] cursor-pointer appearance-none rounded-full border px-2 font-display text-[11px] font-medium focus:outline-none",
                  status.className,
                )}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {error ? (
              <p className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
                {error}
              </p>
            ) : null}

            <div className="rounded-xl border border-line bg-white p-6 shadow-l1 sm:p-10">
              <DocumentEditor
                key={doc.id}
                initialContent={content ?? { type: "doc", content: [] }}
                onReady={setEditor}
                onChange={(next) => {
                  setContent(next);
                  setSaveState("saving");
                }}
                onSelectionChange={setSelection}
              />
            </div>

            <div className="mt-3 flex items-center justify-between text-[12px] text-subtle">
              <span>
                {content ? countWords(content) : 0} words · v{doc.versionCount}{" "}
                versions
              </span>
              <span>Edited {relativeTime(doc.updatedAt)}</span>
            </div>
          </div>
        </section>

        {panelOpen ? (
          <aside className="lg:sticky lg:top-20 lg:h-[calc(100vh-7rem)]">
            <div className="flex h-full flex-col rounded-xl border border-line bg-white p-4 shadow-l1">
              <div className="mb-4 grid grid-cols-3 gap-1 rounded-lg border border-line bg-canvas p-1">
                {tabs.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setTab(item.id)}
                    className={cn(
                      "rounded-md px-1 py-1.5 font-display text-[12.5px] font-medium transition-colors",
                      tab === item.id
                        ? "bg-white text-ink shadow-l1"
                        : "text-muted hover:text-ink",
                    )}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              <div className="min-h-0 flex-1 overflow-y-auto">
                {tab === "ai" ? (
                  <AiPanel
                    documentId={doc.id}
                    title={doc.title}
                    selection={selection}
                    editor={editor}
                    onApplied={() => setVersionsKey((key) => key + 1)}
                  />
                ) : null}
                {tab === "versions" ? (
                  <VersionsPanel
                    documentId={doc.id}
                    refreshKey={versionsKey}
                    onRestored={refreshDocument}
                  />
                ) : null}
                {tab === "exports" ? (
                  <ExportsPanel
                    documentId={doc.id}
                    onVersionCreated={() => setVersionsKey((key) => key + 1)}
                  />
                ) : null}
              </div>
            </div>
          </aside>
        ) : null}
      </div>
    </AppShell>
  );
}

function countWords(content: DocContent): number {
  const text: string[] = [];
  const walk = (nodes: unknown) => {
    if (!Array.isArray(nodes)) return;
    for (const node of nodes as Record<string, unknown>[]) {
      if (node.type === "text" && typeof node.text === "string") text.push(node.text);
      if (Array.isArray(node.content)) walk(node.content);
    }
  };
  walk(content.content);
  return text.join(" ").split(/\s+/).filter(Boolean).length;
}
