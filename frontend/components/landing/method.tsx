import { Bot, FileOutput, PenLine } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Phase {
  icon: LucideIcon;
  phase: string;
  title: string;
  body: string;
  footer: string;
}

const phases: Phase[] = [
  {
    icon: PenLine,
    phase: "Phase 01",
    title: "Describe & Schematize",
    body: "Expose your mandate in natural language. DocsDrafter maps it into placeholder-bound structure — sections, fields and intent — before a single word is drafted.",
    footer: "input: brief → outline → v1",
  },
  {
    icon: Bot,
    phase: "Phase 02",
    title: "Structured Co-Authoring",
    body: "Collaborate with the AI assistant in a live ProseMirror canvas. Tighten a clause, expand a section, or draft the whole brief — selection-aware and non-destructive.",
    footer: "job: ai.draft → apply",
  },
  {
    icon: FileOutput,
    phase: "Phase 03",
    title: "Multi-Engine Export",
    body: "Compile a pixel-perfect PDF or fully-styled native DOCX — including embedded template skeletons — ready for the boardroom in one click.",
    footer: "output: .docx / .pdf",
  },
];

export function Method() {
  return (
    <section id="method" className="px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <p className="text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">
          Executive cadence
        </p>
        <h2 className="mx-auto mt-3 max-w-2xl text-center font-display text-[32px] font-semibold leading-[1.1] tracking-[-0.02em] sm:text-[40px]">
          Three steps from briefing to execution
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-center text-[14px] leading-relaxed text-muted">
          Structured input, co-authored drafting, and a deterministic export
          pipeline keep every handover inspection-grade.
        </p>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {phases.map((item) => (
            <article
              key={item.title}
              className="flex flex-col rounded-xl border border-line bg-surface p-6 shadow-l1"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-lavender text-brand">
                <item.icon size={16} />
              </span>
              <p className="mt-5 text-[10px] font-semibold uppercase tracking-[0.18em] text-subtle">
                {item.phase}
              </p>
              <h3 className="mt-2 font-display text-[17px] font-semibold tracking-tight">
                {item.title}
              </h3>
              <p className="mt-2 flex-1 text-[13px] leading-relaxed text-muted">
                {item.body}
              </p>
              <p className="mt-6 font-mono text-[11px] text-subtle">
                {item.footer}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
