"use client";

/** Export queue: DOCX (docxtpl/python-docx) and PDF (Playwright/LibreOffice). */

import { Download, FileText, Loader2, Trash2 } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/card";
import { absoluteUrl, apiDelete, apiGet, apiPost } from "@/lib/api";
import type { ExportRecord } from "@/lib/types";
import { formatDate } from "@/lib/utils";

async function pollExport(id: string): Promise<ExportRecord> {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    const record = await apiGet<ExportRecord>(`/api/exports/${id}`);
    if (record.status === "succeeded" || record.status === "failed") return record;
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
  throw new Error("The export is taking longer than expected.");
}

export function ExportsPanel({
  documentId,
  onVersionCreated,
}: {
  documentId: string;
  onVersionCreated: () => void;
}) {
  const [exports, setExports] = React.useState<ExportRecord[] | null>(null);
  const [busyFormat, setBusyFormat] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(() => {
    apiGet<{ items: ExportRecord[] }>(`/api/documents/${documentId}/exports`)
      .then((data) => setExports(data.items))
      .catch(() => setExports([]));
  }, [documentId]);

  React.useEffect(() => {
    load();
  }, [load]);

  async function start(format: "docx" | "pdf") {
    setBusyFormat(format);
    setError(null);
    try {
      const created = await apiPost<ExportRecord>(
        `/api/documents/${documentId}/exports`,
        { format },
      );
      const finished = await pollExport(created.id);
      if (finished.status === "failed") {
        setError(finished.error || "Export failed");
      } else {
        onVersionCreated();
      }
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusyFormat(null);
    }
  }

  async function remove(id: string) {
    await apiDelete(`/api/exports/${id}`);
    load();
  }

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-lavender text-brand">
          <FileText size={14} />
        </span>
        <h2 className="font-display text-[15px] font-semibold text-ink">Export</h2>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="primary"
          onClick={() => start("docx")}
          disabled={busyFormat !== null}
        >
          {busyFormat === "docx" ? (
            <Loader2 size={14} className="animate-spin" />
          ) : null}
          DOCX
        </Button>
        <Button
          variant="primary"
          onClick={() => start("pdf")}
          disabled={busyFormat !== null}
        >
          {busyFormat === "pdf" ? (
            <Loader2 size={14} className="animate-spin" />
          ) : null}
          PDF
        </Button>
      </div>

      <p className="mt-2 text-[12.5px] leading-5 text-muted">
        DOCX stays fully editable in Word; PDF is rendered from the web layout.
      </p>

      {error ? (
        <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
          {error}
        </p>
      ) : null}

      <div className="mt-4">
        <h3 className="mb-2 font-display text-[11.5px] font-medium uppercase tracking-wide text-subtle">
          Recent exports
        </h3>
        {exports === null ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : exports.length === 0 ? (
          <p className="text-[13px] text-muted">Nothing exported yet.</p>
        ) : (
          <ul className="space-y-1.5">
            {exports.map((record) => (
              <li
                key={record.id}
                className="flex items-center gap-2 rounded-lg border border-line bg-white p-2.5 shadow-l1"
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-display text-[12.5px] font-medium text-ink">
                    {record.fileName}
                  </span>
                  <span className="block text-[11.5px] text-subtle">
                    {record.status === "succeeded"
                      ? `${formatDate(record.completedAt ?? record.createdAt)}${
                          record.sizeBytes
                            ? ` · ${Math.max(1, Math.round(record.sizeBytes / 1024))} KB`
                            : ""
                        }`
                      : record.status === "failed"
                        ? record.error || "failed"
                        : record.status}
                  </span>
                </span>
                {record.status === "succeeded" ? (
                  <a
                    href={absoluteUrl(record.downloadUrl)}
                    download={record.fileName}
                    title="Download"
                    className="flex h-7 w-7 items-center justify-center rounded-md text-muted transition-colors hover:bg-lavender hover:text-brand"
                  >
                    <Download size={14} />
                  </a>
                ) : null}
                <button
                  type="button"
                  onClick={() => remove(record.id)}
                  title="Delete export"
                  className="flex h-7 w-7 items-center justify-center rounded-md text-subtle transition-colors hover:bg-red-50 hover:text-danger"
                >
                  <Trash2 size={13} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
