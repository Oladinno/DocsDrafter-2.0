import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ArrowRight } from "lucide-react";

export function ClosingCta() {
  return (
    <section className="px-6 pb-20">
      <div className="relative mx-auto max-w-6xl overflow-hidden rounded-2xl bg-brand p-10 sm:p-14">
        <div
          aria-hidden
          className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -bottom-32 -left-16 h-72 w-72 rounded-full bg-white/5 blur-3xl"
        />

        <div className="relative">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/60">
            From solo drafts to enterprise rollouts
          </p>
          <h2 className="mt-4 max-w-2xl font-display text-[32px] font-semibold leading-[1.08] tracking-[-0.02em] text-white sm:text-[44px]">
            Stop wrestling with word processors. Start drafting like an
            architect.
          </h2>
          <p className="mt-4 max-w-2xl text-[14px] leading-relaxed text-white/75">
            Join thousands of executives, consultancies, and product teams
            building their most consequential documents with DocsDrafter 2.0.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              href="/register"
              className="inline-flex h-10 items-center gap-2 rounded-lg bg-white px-4 font-display text-[14px] font-medium text-brand shadow-l1 transition-colors hover:bg-canvas"
            >
              Get started with DocsDrafter Free
              <ArrowRight size={14} />
            </Link>
            <Link
              href="#pricing"
              className="inline-flex h-10 items-center gap-2 rounded-lg border border-white/30 px-4 font-display text-[14px] font-medium text-white transition-colors hover:bg-white/10"
            >
              <ArrowLeft size={14} />
              Compare plans
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
