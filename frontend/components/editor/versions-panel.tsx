"use client";

/** Version history: list saved states, create named snapshots, restore. */

import { History, RotateCcw } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiGet, apiPost } from "@/lib/api";
import type { DocumentVersion } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function VersionsPanel({
  documentId,
  refreshKey,
  onRestored,
}: {
  documentId: string;
  refreshKey: number;
  onRestored: () => void;
}) {
  const [versions, setVersions] = React.useState<DocumentVersion[] | null>(null);
  const [note, setNote] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(() => {
    apiGet<DocumentVersion[]>(`/api/documents/${documentId}/versions`)
      .then(setVersions)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [documentId]);

  React.useEffect(() => {
    load();
  }, [load, refreshKey]);

  async function snapshot() {
    setBusy(true);
    setError(null);
    try {
      await apiPost(`/api/documents/${documentId}/versions`, { note });
      setNote("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save a version");
    } finally {
      setBusy(false);
    }
  }

  async function restore(version: DocumentVersion) {
    setBusy(true);
    setError(null);
    try {
      await apiPost(
        `/api/documents/${documentId}/versions/${version.id}/restore`,
        {},
      );
      load();
      onRestored();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not restore");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-lavender text-brand">
          <History size={14} />
        </span>
        <h2 className="font-display text-[15px] font-semibold text-ink">
          Version history
        </h2>
      </div>

      <div className="mb-3 flex gap-2">
        <Input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Name this version…"
        />
        <Button variant="secondary" onClick={snapshot} disabled={busy}>
          Save
        </Button>
      </div>

      {error ? (
        <p className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
          {error}
        </p>
      ) : null}

      {versions === null ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : versions.length === 0 ? (
        <p className="text-[13px] text-muted">
          No versions yet. Edits are snapshotted automatically as you write.
        </p>
      ) : (
        <ol className="space-y-1.5 overflow-y-auto pr-1">
          {versions.map((version, index) => (
            <li
              key={version.id}
              className="flex items-start gap-2 rounded-lg border border-line bg-white p-2.5 shadow-l1"
            >
              <span className="mt-0.5 flex h-6 min-w-6 items-center justify-center rounded-full bg-canvas px-1.5 font-display text-[11px] font-semibold text-muted">
                v{version.versionNumber}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-display text-[13px] font-medium text-ink">
                  {version.note || version.title}
                </span>
                <span className="block text-[11.5px] text-subtle">
                  {formatDate(version.createdAt)} · {version.kind}
                  {version.status !== "draft" ? ` · ${version.status}` : ""}
                </span>
              </span>
              {index === 0 ? (
                <span className="rounded-sm border border-line bg-canvas px-1.5 py-0.5 font-display text-[10.5px] text-muted">
                  latest
                </span>
              ) : (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => restore(version)}
                  title="Restore this version"
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted transition-colors hover:bg-lavender hover:text-brand disabled:opacity-40"
                >
                  <RotateCcw size={14} />
                </button>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
