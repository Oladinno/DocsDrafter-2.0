import {
  Boxes,
  ClipboardList,
  FileCheck2,
  GitBranch,
  Layers,
  PanelRight,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface MatrixItem {
  icon: LucideIcon;
  title: string;
  body: string;
}

const matrixItems: MatrixItem[] = [
  {
    icon: ClipboardList,
    title: "Meeting Minutes",
    body: "Decisions, owners and deadlines, minuted as they land.",
  },
  {
    icon: Layers,
    title: "Project Proposals",
    body: "Scope, pricing and delivery matrices that stay aligned.",
  },
  {
    icon: FileCheck2,
    title: "Cover Letters",
    body: "Role-matched narratives with deliberate tone control.",
  },
];

function ChipBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-md border border-line bg-canvas px-2.5 py-1 font-mono text-[10.5px] text-muted">
      {children}
    </span>
  );
}

function FloatingBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-lavender px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-brand">
      {children}
    </span>
  );
}

export function Features() {
  return (
    <section
      id="features"
      className="border-y border-line bg-surface/60 px-6 py-20"
    >
      <div className="mx-auto max-w-6xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">
          Architecture & depth
        </p>
        <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <h2 className="max-w-lg font-display text-[32px] font-semibold leading-[1.1] tracking-[-0.02em] sm:text-[40px]">
            Engineered for document perfectionists
          </h2>
          <p className="max-w-sm text-[13px] leading-relaxed text-muted">
            Built from the ground up as a structured document model rather than
            raw HTML, guaranteeing typographic presence across platforms.
          </p>
        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {/* Wide card — template matrices */}
          <article className="relative rounded-xl border border-line bg-surface p-6 shadow-l1 md:col-span-2">
            <div className="absolute right-5 top-5">
              <FloatingBadge>Built-in &amp; user-defined</FloatingBadge>
            </div>
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-lavender text-brand">
              <Boxes size={16} />
            </span>
            <h3 className="mt-5 max-w-sm font-display text-[19px] font-semibold tracking-tight">
              Pre-Engineered Document Matrices
            </h3>
            <p className="mt-2 max-w-md text-[13px] leading-relaxed text-muted">
              Skip blank pages. From master service agreements to deep-tech RFC
              specifications, deploy schematics authored by practitioners and
              refined by your own workspace.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {matrixItems.map((item) => (
                <div
                  key={item.title}
                  className="rounded-lg border border-line bg-canvas p-3.5"
                >
                  <div className="flex items-center gap-2">
                    <item.icon size={13} className="text-brand" />
                    <p className="text-[12.5px] font-semibold">{item.title}</p>
                  </div>
                  <p className="mt-1.5 text-[11px] leading-relaxed text-muted">
                    {item.body}
                  </p>
                </div>
              ))}
            </div>
          </article>

          {/* Clause-level card */}
          <article className="rounded-xl border border-line bg-surface p-6 shadow-l1">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-lavender text-brand">
              <PanelRight size={16} />
            </span>
            <h3 className="mt-5 font-display text-[19px] font-semibold tracking-tight">
              Clause-Level Granularity
            </h3>
            <p className="mt-2 text-[13px] leading-relaxed text-muted">
              AI does not rewrite your whole file blindly. Select a single
              subsection, tighten its language, and watch the engine emit a
              compliance check without touching neighbouring clauses.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <ChipBadge>Selection-aware</ChipBadge>
              <ChipBadge>Non-destructive</ChipBadge>
            </div>
          </article>

          {/* Structured outputs card */}
          <article className="rounded-xl border border-line bg-surface p-6 shadow-l1 md:col-span-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-lavender text-brand">
              <GitBranch size={16} />
            </span>
            <h3 className="mt-5 max-w-sm font-display text-[19px] font-semibold tracking-tight">
              True Structured Outputs
            </h3>
            <p className="mt-2 max-w-lg text-[13px] leading-relaxed text-muted">
              No regex-cracked JSON. The AI engine emits a strict document tree —
              validated and repaired exactly once — then rendered directly into
              editor blocks ready for both export engines.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <ChipBadge>Strict JSON</ChipBadge>
              <ChipBadge>One-pass repair</ChipBadge>
              <ChipBadge>Zero page drift</ChipBadge>
            </div>
          </article>

          {/* Snapshots card */}
          <article className="rounded-xl border border-line bg-surface p-6 shadow-l1">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-lavender text-brand">
              <GitBranch size={16} />
            </span>
            <h3 className="mt-5 font-display text-[19px] font-semibold tracking-tight">
              Snapshots &amp; Checkpoints
            </h3>
            <p className="mt-2 text-[13px] leading-relaxed text-muted">
              Every content save counts. Name a version when it matters —
              checkpoints stay semantic, not raw bytes — and restore to any
              prior state without leaving the editor.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <ChipBadge>Autosave · v7 current</ChipBadge>
              <ChipBadge>Manual · restorable</ChipBadge>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
