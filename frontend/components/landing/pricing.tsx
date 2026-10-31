import Link from "next/link";
import { Check } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Tier {
  name: string;
  audience: string;
  price: string;
  note?: string;
  features: string[];
  cta: string;
  highlighted: boolean;
}

const tiers: Tier[] = [
  {
    name: "Starter",
    audience: "For solo founders & researchers",
    price: "$0",
    features: [
      "5 AI drafting jobs / month",
      "20 document exports / month",
      "Standard DOCX & PDF output",
      "Core blueprint library",
    ],
    cta: "Start Drafting Free",
    highlighted: false,
  },
  {
    name: "Pro",
    audience: "For consultants & growing companies",
    price: "$29",
    note: "Per seat / month",
    features: [
      "Unlimited AI drafting & revisions",
      "DOCX + PDF export with priority queue",
      "Semantic version history & checkpoints",
      "Template studio & field builder",
      "14-day free trial included",
    ],
    cta: "Start Your Free Trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    audience: "For agencies requiring strict governance",
    price: "$79",
    features: [
      "Custom templates & branding controls",
      "Dedicated export workers",
      "Managed Celery & storage backends",
      "Priority support & onboarding",
    ],
    cta: "Talk to the Drafting Team",
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <p className="text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">
          Predictable pricing
        </p>
        <h2 className="mx-auto mt-3 max-w-2xl text-center font-display text-[32px] font-semibold leading-[1.1] tracking-[-0.02em] sm:text-[40px]">
          Transparent pricing for ambitious teams
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-center text-[14px] leading-relaxed text-muted">
          Start for free, scale when your volume demands unlimited compliance.
        </p>

        <div className="mt-12 grid items-start gap-5 md:grid-cols-3">
          {tiers.map((tier) => (
            <article
              key={tier.name}
              className={cn(
                "relative flex flex-col rounded-xl border bg-surface p-6",
                tier.highlighted
                  ? "border-brand shadow-l3"
                  : "border-line shadow-l1",
              )}
            >
              {tier.highlighted && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand px-3 py-1 text-[11px] font-semibold text-white">
                  Most Popular
                </span>
              )}
              <h3 className="font-display text-[15px] font-semibold">
                {tier.name}
              </h3>
              <p className="mt-1 text-[12px] text-muted">{tier.audience}</p>

              <div className="mt-5 flex items-baseline gap-1.5">
                <span className="font-display text-[38px] font-semibold tracking-[-0.02em]">
                  {tier.price}
                </span>
                <span className="text-[12px] text-muted">{tier.note}</span>
              </div>

              <ul className="mt-5 flex-1 space-y-2.5">
                {tier.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-2 text-[13px] text-ink"
                  >
                    <Check size={14} className="mt-1 shrink-0 text-brand" />
                    {feature}
                  </li>
                ))}
              </ul>

              <Link
                href="/register"
                className={cn(
                  buttonVariants({
                    variant: tier.highlighted ? "primary" : "secondary",
                    size: "lg",
                  }),
                  "mt-6 w-full",
                )}
              >
                {tier.cta}
              </Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
