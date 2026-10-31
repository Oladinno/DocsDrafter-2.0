"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { ArrowRight, Check } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Category = "Business" | "Career" | "Productivity" | "Technical";

interface Blueprint {
  category: Category;
  sections: number;
  title: string;
  description: string;
  bullets: string[];
}

const filters = [
  "All Templates",
  "Business",
  "Career",
  "Productivity",
  "Technical",
];

const blueprints: Blueprint[] = [
  {
    category: "Business",
    sections: 10,
    title: "Project Proposal",
    description:
      "Full proposal chassis covering executive summary, scope of work, delivery roadmap, resourcing assumptions and pricing schedules in one coherent narrative.",
    bullets: ["Cover-note skeleton included", "Pricing & timeline sections"],
  },
  {
    category: "Career",
    sections: 5,
    title: "Cover Letter",
    description:
      "Role-matched one-pager with a guided field flow — company, role, proof points — so every application opens with intent, not filler.",
    bullets: ["Guided field prompts", "Tone-preserving rewrite ready"],
  },
  {
    category: "Business",
    sections: 8,
    title: "Mutual Non-Disclosure Agreement",
    description:
      "Standard non-disclosure instrument covering mutual obligations, confidential material definition, exclusions and term limits for corporate use.",
    bullets: ["Jurisdiction-agnostic boilerplate", "8-minute field setup"],
  },
  {
    category: "Business",
    sections: 12,
    title: "Enterprise Statement of Work",
    description:
      "Comprehensive scope-of-work documentation covering service level guarantees, deliverable matrices, acceptance criteria and fee retainers.",
    bullets: ["SLA clause blocks", "Acceptance gates built in"],
  },
  {
    category: "Technical",
    sections: 9,
    title: "System RFC & Technical Spec",
    description:
      "Architecture decision record containing interface contracts, rollout phases, rollback markers and risk registers for engineering review.",
    bullets: ["ADR statement format", "Rollout & rollback markers"],
  },
  {
    category: "Productivity",
    sections: 6,
    title: "Meeting Minutes",
    description:
      "Decisions, owners and deadlines captured in a repeatable minuting format that keeps follow-through auditable across teams.",
    bullets: ["Action-owner matrix", "Deadline tracking fields"],
  },
];

export function Blueprints() {
  const [active, setActive] = useState("All Templates");

  const visible = useMemo(
    () =>
      active === "All Templates"
        ? blueprints
        : blueprints.filter((blueprint) => blueprint.category === active),
    [active],
  );

  return (
    <section id="blueprints" className="px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <p className="text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">
          Curated matrix gallery
        </p>
        <h2 className="mx-auto mt-3 max-w-2xl text-center font-display text-[32px] font-semibold leading-[1.1] tracking-[-0.02em] sm:text-[40px]">
          Explore production blueprints
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-center text-[14px] leading-relaxed text-muted">
          Deploy pre-vetted corporate agreements, proposals, technical reports
          and career instruments — each retaining clause-level precision in your
          workspace.
        </p>

        <div className="mt-8 flex justify-center">
          <div className="inline-flex flex-wrap justify-center gap-1 rounded-xl border border-line bg-surface p-1 shadow-l1">
            {filters.map((filter) => (
              <button
                key={filter}
                type="button"
                onClick={() => setActive(filter)}
                className={cn(
                  "rounded-lg px-3.5 py-1.5 text-[12.5px] font-medium transition-colors",
                  active === filter
                    ? "bg-brand text-white"
                    : "text-muted hover:bg-canvas hover:text-ink",
                )}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((blueprint) => (
            <article
              key={blueprint.title}
              className="flex flex-col rounded-xl border border-line bg-surface p-5 shadow-l1"
            >
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-lavender px-2 py-0.5 text-[10.5px] font-semibold text-brand">
                  {blueprint.category}
                </span>
                <span className="text-[11px] text-subtle">
                  Blueprint · {blueprint.sections} sections
                </span>
              </div>
              <h3 className="mt-3 font-display text-[16px] font-semibold tracking-tight">
                {blueprint.title}
              </h3>
              <p className="mt-2 flex-1 text-[13px] leading-relaxed text-muted">
                {blueprint.description}
              </p>
              <ul className="mt-4 space-y-1.5">
                {blueprint.bullets.map((bullet) => (
                  <li
                    key={bullet}
                    className="flex items-start gap-2 text-[12px] text-ink"
                  >
                    <Check size={13} className="mt-0.5 shrink-0 text-brand" />
                    {bullet}
                  </li>
                ))}
              </ul>
              <div className="mt-5 border-t border-line pt-3">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-1.5 text-[12.5px] font-medium text-brand transition-colors hover:text-brand-hover"
                >
                  Use blueprint
                  <ArrowRight size={13} />
                </Link>
              </div>
            </article>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Link
            href="/register"
            className={cn(buttonVariants({ variant: "secondary", size: "lg" }))}
          >
            Try Blueprint Accuracy
          </Link>
        </div>
      </div>
    </section>
  );
}
