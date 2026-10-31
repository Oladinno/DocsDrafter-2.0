"use client";

/** AI drafting panel: describe the document, review the generated blocks, then
 * choose to apply or discard them - the user always decides. */

import type { Editor } from "@tiptap/react";
import { Loader2, Sparkles } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/card";
import { Field, Textarea } from "@/components/ui/input";
import { apiGet, apiPost } from "@/lib/api";
import type { Job } from "@/lib/types";
import { cn } from "@/lib/utils";

type Operation = "draft" | "rewrite" | "expand" | "summarize";

const OPERATION_META: Record<
  Operation,
  { label: string; hint: string; needsPrompt: boolean }
> = {
  draft: {
    label: "Draft",
    hint: "Generate a full document from a brief",
    needsPrompt: true,
  },
  rewrite: { label: "Rewrite", hint: "Improve the selected text", needsPrompt: false },
  expand: { label: "Expand", hint: "Add detail to the selection", needsPrompt: false },
  summarize: {
    label: "Summarize",
    hint: "Condense the selection",
    needsPrompt: false,
  },
};

async function pollJob(id: string): Promise<Job> {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const job = await apiGet<Job>(`/api/jobs/${id}`);
    if (job.status === "succeeded" || job.status === "failed") return job;
    await new Promise((resolve) => setTimeout(resolve, 600));
  }
  throw new Error("The generation is taking longer than expected. Try again.");
}

export function AiPanel({
  documentId,
  title,
  selection,
  editor,
  onApplied,
}: {
  documentId: string;
  title: string;
  selection: string;
  editor: Editor | null;
  onApplied: () => void;
}) {
  const [operation, setOperation] = React.useState<Operation>("draft");
  const [prompt, setPrompt] = React.useState("");
  const [instructions, setInstructions] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [preview, setPreview] = React.useState<Job | null>(null);

  const meta = OPERATION_META[operation];
  const hasSelection = selection.trim().length > 0;

  async function generate() {
    if (!editor) return;
    if (operation !== "draft" && !hasSelection) {
      setError("Select some text in the document first.");
      return;
    }
    setBusy(true);
    setError(null);
    setPreview(null);
    try {
      const body: Record<string, unknown> = {
        operation,
        documentId,
        title,
        prompt,
        instructions,
        selection: operation === "draft" ? "" : selection,
        surrounding: "",
      };
      const created = await apiPost<Job>("/api/ai/generate", body);
      const finished = await pollJob(created.id);
      if (finished.status === "failed") {
        setError(finished.error || "Generation failed");
      } else {
        setPreview(finished);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  function apply() {
    if (!editor || !preview?.result) return;
    const result = preview.result;
    if (operation === "draft") {
      editor.chain().focus().setContent(result.content as never).run();
    } else if (!selection.trim()) {
      editor.chain().focus().insertContent(result.blocks as never).run();
    } else {
      editor
        .chain()
        .focus()
        .deleteSelection()
        .insertContent(result.blocks as never)
        .run();
    }
    setPreview(null);
    setPrompt("");
    setInstructions("");
    onApplied();
  }

  const previewText = preview?.result?.plainText ?? "";

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-lavender text-brand">
          <Sparkles size={14} />
        </span>
        <h2 className="font-display text-[15px] font-semibold text-ink">Assistant</h2>
        {preview?.result?.provider ? (
          <span className="rounded-sm border border-line bg-canvas px-1.5 py-0.5 font-display text-[10.5px] text-muted">
            {preview.result.provider}
          </span>
        ) : null}
      </div>

      <div className="mb-3 grid grid-cols-4 gap-1 rounded-lg border border-line bg-white p-1 shadow-l1">
        {(Object.keys(OPERATION_META) as Operation[]).map((key) => {
          const disabled = key !== "draft" && !hasSelection;
          return (
            <button
              key={key}
              type="button"
              disabled={disabled}
              title={disabled ? "Select text first" : OPERATION_META[key].hint}
              onClick={() => setOperation(key)}
              className={cn(
                "rounded-md px-1 py-1.5 font-display text-[12px] font-medium transition-colors disabled:opacity-40",
                operation === key
                  ? "bg-lavender text-brand"
                  : "text-muted hover:bg-canvas hover:text-ink",
              )}
            >
              {OPERATION_META[key].label}
            </button>
          );
        })}
      </div>

      <p className="mb-3 text-[12.5px] leading-5 text-muted">{meta.hint}</p>

      <div className="space-y-3">
        {meta.needsPrompt ? (
          <Field label="Describe the document">
            <Textarea
              rows={5}
              value={prompt}
              placeholder="A one-page project proposal for migrating our billing service to a new provider, aimed at the platform team…"
              onChange={(event) => setPrompt(event.target.value)}
            />
          </Field>
        ) : (
          <Field label="Instructions" hint="optional">
            <Textarea
              rows={3}
              value={instructions}
              placeholder="Make it more formal / shorten it by half / add concrete examples…"
              onChange={(event) => setInstructions(event.target.value)}
            />
          </Field>
        )}

        {operation !== "draft" && hasSelection ? (
          <div className="rounded-lg border border-line bg-canvas p-2.5">
            <div className="mb-1 font-display text-[11px] font-medium uppercase tracking-wide text-subtle">
              Selection
            </div>
            <p className="line-clamp-4 text-[12.5px] leading-5 text-muted">
              {selection}
            </p>
          </div>
        ) : null}

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
            {error}
          </p>
        ) : null}

        {busy ? (
          <div className="flex items-center gap-2 rounded-lg border border-brand/25 bg-lavender/50 px-3 py-2.5 text-[13px] text-brand">
            <Loader2 size={14} className="animate-spin" />
            Generating a suggestion…
          </div>
        ) : null}

        {preview && !busy ? (
          <div className="ai-active rounded-xl border border-line bg-white p-3 shadow-l2">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-display text-[12px] font-medium text-brand">
                Suggestion
              </span>
              <span className="text-[11.5px] text-subtle">
                {previewText.split(/\s+/).filter(Boolean).length} words
              </span>
            </div>
            <div className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg bg-canvas p-2.5 text-[13.5px] leading-6 text-ink">
              {previewText}
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <Button
                variant="ghost"
                size="compact"
                onClick={() => setPreview(null)}
              >
                Discard
              </Button>
              <Button variant="primary" size="compact" onClick={apply}>
                {operation === "draft" ? "Replace document" : "Apply to selection"}
              </Button>
            </div>
          </div>
        ) : null}

        {!preview && !busy ? (
          <Button
            variant="ai"
            className="w-full"
            onClick={generate}
            disabled={!editor || (meta.needsPrompt && !prompt.trim())}
          >
            <Sparkles size={14} />
            {operation === "draft" ? "Draft document" : `${meta.label} selection`}
          </Button>
        ) : null}
      </div>
    </div>
  );
}

export function AiPanelFallback() {
  return (
    <div className="flex justify-center py-10">
      <Spinner />
    </div>
  );
}
