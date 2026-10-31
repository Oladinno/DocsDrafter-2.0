import Link from "next/link";
import {
  ArrowUpRight,
  Check,
  ClipboardList,
  Coins,
  FileDown,
  FileText,
  History,
  Info,
  Layers,
  Play,
  Sparkles,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

const trustChecks = [
  "No credit card required",
  "Free tier included",
  "DOCX & PDF export built in",
  "Your documents stay yours",
];

interface StructureItem {
  icon: LucideIcon;
  label: string;
}

const structureItems: StructureItem[] = [
  { icon: FileText, label: "1.0 Executive Summary & Materials" },
  { icon: Layers, label: "2.0 Deliverable Governance & Templates" },
  { icon: Users, label: "3.1 Liability Limitations & Escalatory Caps" },
  { icon: Coins, label: "4.2 Financial Schedules & Fee Retainers" },
];

const trustedBy = [
  "Meridian Legal",
  "Vantage Advisory",
  "Northwind Labs",
  "Aperture Group",
  "Statline Consulting",
  "Kite & Partners",
];

function ProductPreview() {
  return (
    <div
      aria-hidden
      className="relative mx-auto mt-14 max-w-5xl overflow-hidden rounded-xl border border-line bg-surface shadow-l3"
    >
      {/* Window chrome */}
      <div className="flex h-11 items-center justify-between gap-3 border-b border-line bg-canvas/60 px-3">
        <div className="flex min-w-0 items-center gap-2 rounded-md border border-line bg-surface px-2.5 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          <span className="truncate text-[11px] text-muted">
            Proposal — Strategic Enterprise Rollout 2026 · client-ready
          </span>
        </div>
        <div className="hidden items-center gap-2 sm:flex">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-surface px-2 py-1 text-[10.5px] text-muted">
            <History size={11} />
            Autosave · Saved
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md bg-brand px-2 py-1 text-[10.5px] font-medium text-white">
            <FileDown size={11} />
            Export draft
          </span>
        </div>
      </div>

      <div className="grid md:grid-cols-[340px_1fr]">
        {/* Left rail */}
        <div className="hidden border-r border-line bg-lavender/40 p-3 md:flex md:flex-col md:gap-3">
          <div className="rounded-lg border border-line bg-surface p-3 shadow-l1">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-md bg-lavender text-brand">
                <Sparkles size={11} />
              </span>
              <span className="text-[11px] font-semibold">Assistant Prompt</span>
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-muted">
              Draft a full proposal outline (cover note + 3-year implementation
              roadmap) for the Apex Advisory enterprise pitch. Keep a coherent
              executive narrative and cap the delivery logic clearly.
            </p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              <span className="rounded-md bg-lavender px-2 py-0.5 text-[10px] font-medium text-brand">
                Draft new section
              </span>
              <span className="rounded-md border border-line px-2 py-0.5 text-[10px] text-muted">
                logical v2
              </span>
            </div>
          </div>

          <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-subtle">
            Document structure
          </p>

          <div className="space-y-1.5">
            {structureItems.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 rounded-md border border-line bg-surface px-2.5 py-2"
              >
                <item.icon size={12} className="shrink-0 text-brand" />
                <span className="truncate text-[11px] text-ink">{item.label}</span>
              </div>
            ))}
          </div>

          <div className="mt-auto flex items-center justify-between gap-2 pt-1">
            <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-surface px-2 py-1 text-[10.5px] text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              9,380 / 24 pages
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-lavender px-2 py-1 text-[10.5px] font-medium text-brand">
              <ClipboardList size={10} />
              Ask AI →
            </span>
          </div>
        </div>

        {/* Document pane */}
        <div className="p-5" >
          <div className="flex items-center justify-between gap-2">
            <span className="rounded-md border border-line px-2 py-0.5 text-[10px] text-subtle">
              Outline ready
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-lavender px-2.5 py-1 text-[10.5px] font-medium text-brand">
              <History size={10} />
              Manual snapshot · v12
            </span>
          </div>

          <div className="mt-4 flex items-baseline justify-between gap-6 border-b border-line pb-3">
            <h3 className="font-display text-[17px] font-semibold tracking-tight">
              Apex Advisory Master Services Agreement
            </h3>
            <span className="hidden shrink-0 text-[10px] text-subtle sm:block">
              © 2026 Apex Advisory
            </span>
          </div>
          <p className="mt-1.5 flex items-center justify-between text-[10px] text-subtle">
            <span>Doc ID: 0087-C · Page 14 of 15</span>
            <span className="hidden sm:block">Plan v: 15</span>
          </p>

          <h4 className="mt-5 text-[12px] font-semibold">
            1.0 Executive Summary & Operational Matrix
          </h4>
          <p className="mt-2 text-[11px] leading-relaxed text-muted">
            The document sets forth the framework and timetable terms under which
            the Recipient may submit Treasury Notices reference Agency Checklist
            counts and the Entente Client Service scoring during Fiscal Year 2025.
            Recipient acknowledges the full internal audit pathway.
          </p>

          <h4 className="mt-5 text-[12px] font-semibold">
            2.0 Service Level Guarantees (SLA)
          </h4>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {[
              { label: "Delivery confidence", value: "92.4%", width: "92%" },
              { label: "Approvals (v12)", value: "8 of 9", width: "89%" },
              { label: "SLA adherence", value: "480h", width: "76%" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-md border border-line p-2.5"
              >
                <p className="text-[9px] uppercase tracking-[0.08em] text-subtle">
                  {stat.label}
                </p>
                <p className="mt-1 font-display text-[13px] font-semibold">
                  {stat.value}
                </p>
                <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-lavender">
                  <div
                    className="h-full rounded-full bg-brand"
                    style={{ width: stat.width }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex gap-2 rounded-md border border-brand/15 bg-lavender/50 p-2.5">
            <Info size={12} className="mt-0.5 shrink-0 text-brand" />
            <p className="text-[10.5px] leading-relaxed text-brand">
              NOTE: The latest Q1 engagement benchmarks slipped past the framing
              date — rebalance the figures in section 12 before the final DOCX
              export.
            </p>
          </div>

          <div className="mt-5 flex items-center justify-between border-t border-line pt-3">
            <span className="inline-flex items-center gap-1.5 text-[10px] text-muted">
              <Check size={11} className="text-success" />
              Automated approval: verified
            </span>
            <span className="text-[10px] text-subtle">DocDR03 · Final ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 pb-8 pt-16">
      <div className="relative mx-auto max-w-6xl">
        <div className="text-center">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3.5 py-1.5 text-[12px] shadow-l1 transition-colors hover:border-brand/40"
          >
            <span className="font-medium text-ink">
              DocsDrafter 2.0 is live — Synthesized Document Workspace
            </span>
            <ArrowUpRight size={13} className="text-muted" />
          </Link>

          <h1 className="mx-auto mt-7 max-w-4xl font-display text-[42px] font-semibold leading-[1.06] tracking-[-0.03em] sm:text-[52px] lg:text-[60px]">
            From idea to publication-grade document in seconds.
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-[15px] leading-relaxed text-muted">
            The unified workspace combining placeholder-driven templates, AI
            co-authoring, version checkpoints, and pixel-perfect DOCX / PDF
            output — so high-stakes teams never start from a blank page again.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/register">
              <Button variant="primary" size="lg">
                Start Drafting Free
              </Button>
            </Link>
            <Link href="#method">
              <Button variant="secondary" size="lg">
                <Play size={13} />
                Watch the 3-min tour
              </Button>
            </Link>
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
            {trustChecks.map((item) => (
              <span
                key={item}
                className="inline-flex items-center gap-1.5 text-[12.5px] text-muted"
              >
                <Check size={13} className="text-success" />
                {item}
              </span>
            ))}
          </div>
        </div>

        {/* Glow behind mockup */}
        <div
          aria-hidden
          className="pointer-events-none absolute -top-16 left-1/2 h-[420px] w-[840px] -translate-x-1/2 rounded-full bg-brand/10 blur-3xl"
        />

        <ProductPreview />
      </div>

      {/* Trusted-by strip */}
      <section className="mt-16 border-y border-line bg-surface py-8">
        <div className="mx-auto max-w-6xl">
          <p className="text-center text-[10px] font-semibold uppercase tracking-[0.2em] text-subtle">
            Trusted by consultants, counsel and technical teams under deadline
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
            {trustedBy.map((name) => (
              <span
                key={name}
                className="font-display text-[15px] font-semibold text-subtle"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      </section>
    </section>
  );
}
