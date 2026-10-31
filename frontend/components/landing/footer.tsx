import Link from "next/link";
import { FileText, ShieldCheck } from "lucide-react";

interface FooterColumn {
  heading: string;
  links: { label: string; href: string }[];
}

const columns: FooterColumn[] = [
  {
    heading: "Product",
    links: [
      { label: "Templates", href: "/templates" },
      { label: "AI Assistant", href: "#features" },
      { label: "Version History", href: "#features" },
      { label: "DOCX & PDF Export", href: "#pricing" },
      { label: "Pricing", href: "#pricing" },
    ],
  },
  {
    heading: "Solutions",
    links: [
      { label: "Consultants", href: "#blueprints" },
      { label: "Legal Teams", href: "#blueprints" },
      { label: "Startups", href: "#blueprints" },
      { label: "Engineering", href: "#blueprints" },
    ],
  },
  {
    heading: "Company",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Register", href: "/register" },
      { label: "Sign in", href: "/login" },
    ],
  },
  {
    heading: "Legal & Trust",
    links: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
      { label: "Security", href: "#" },
      { label: "Sandbox Workspace", href: "#" },
    ],
  },
];

function StatusChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-canvas px-2.5 py-1 text-[11px] text-muted">
      {children}
    </span>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_repeat(4,1fr)]">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-white shadow-l1">
                <FileText size={15} strokeWidth={2.2} />
              </span>
              <span className="font-display text-[15px] font-semibold tracking-tight">
                DocsDrafter
              </span>
            </div>
            <p className="mt-4 max-w-xs text-[13px] leading-relaxed text-muted">
              The precision document workbench for product strategists, legal
              counsel and technical architects.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <StatusChip>
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                All systems operational
              </StatusChip>
              <StatusChip>
                <ShieldCheck size={12} className="text-success" />
                GDPR Compliant
              </StatusChip>
            </div>
          </div>

          {columns.map((column) => (
            <nav key={column.heading}>
              <p className="text-[12px] font-semibold">{column.heading}</p>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-[13px] text-muted transition-colors hover:text-ink"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t border-line pt-5 sm:flex-row sm:items-center">
          <p className="text-[12px] text-subtle">
            © 2026 DocsDrafter Technologies Inc. All rights reserved.
          </p>
          <div className="flex items-center gap-4 text-[12px] text-subtle">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              All systems operational
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ShieldCheck size={12} className="text-success" />
              GDPR Compliant
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
