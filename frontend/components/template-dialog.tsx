"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Spinner } from "@/components/ui/card";
import { apiPost } from "@/lib/api";
import type { Document, Template, TemplateField } from "@/lib/types";

/** Start a document from a template by filling its structured fields. */
export function TemplateDialog({
  template,
  onClose,
}: {
  template: Template | null;
  onClose: () => void;
}) {
  const router = useRouter();
  const [values, setValues] = React.useState<Record<string, string>>({});
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [initializedFor, setInitializedFor] = React.useState<string | null>(null);

  // Reset the form when a different template is opened (render-phase reset).
  if (template && initializedFor !== template.id) {
    setInitializedFor(template.id);
    setError(null);
    setValues(
      Object.fromEntries(
        template.fields.map((field) => [field.key, field.default ?? ""]),
      ),
    );
  }

  if (!template) return null;

  const missing =
    template.fields.find(
      (field: TemplateField) =>
        field.required && !values[field.key]?.trim(),
    ) ?? null;

  async function create() {
    if (!template) return;
    if (missing) {
      setError(`${missing.label} is required`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const document = await apiPost<Document>("/api/documents", {
        templateId: template.id,
        source: values,
      });
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create document");
      setBusy(false);
    }
  }

  return (
    <Dialog
      open
      onClose={onClose}
      title={template.name}
      description={template.description}
    >
      <div className="space-y-4">
        {template.fields.length === 0 ? (
          <p className="text-[14px] text-muted">
            This template starts you off with a clean structure - no setup
            needed.
          </p>
        ) : (
          template.fields.map((field) => (
            <Field
              key={field.key}
              label={field.label}
              hint={field.required ? "required" : undefined}
            >
              {field.key === "highlights" || field.key === "objective" ? (
                <Textarea
                  rows={3}
                  value={values[field.key] ?? ""}
                  placeholder={field.placeholder}
                  onChange={(event) =>
                    setValues((prev) => ({ ...prev, [field.key]: event.target.value }))
                  }
                />
              ) : (
                <Input
                  value={values[field.key] ?? ""}
                  placeholder={field.placeholder}
                  onChange={(event) =>
                    setValues((prev) => ({ ...prev, [field.key]: event.target.value }))
                  }
                />
              )}
            </Field>
          ))
        )}

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
            {error}
          </p>
        ) : null}

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button variant="primary" onClick={create} disabled={busy}>
            {busy ? <Spinner className="h-3.5 w-3.5 border-t-white" /> : null}
            Create document
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
