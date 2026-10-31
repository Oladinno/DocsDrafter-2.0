import Link from "next/link";
import { FileText } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "#method", label: "Method" },
  { href: "#features", label: "Features" },
  { href: "#blueprints", label: "Blueprints" },
  { href: "#pricing", label: "Pricing" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-canvas/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-6">
        <Link href="/" className="flex shrink-0 items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-white shadow-l1">
            <FileText size={15} strokeWidth={2.2} />
          </span>
          <span className="font-display text-[15px] font-semibold tracking-tight">
            DocsDrafter
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-1.5 text-[13px] text-muted transition-colors hover:bg-surface hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className={cn(
              "hidden text-[13px] text-muted transition-colors hover:text-ink sm:inline-flex sm:items-center",
              buttonVariants({ variant: "ghost" }),
            )}
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className={cn(buttonVariants({ variant: "primary", size: "compact" }))}
          >
            Start Drafting Free
          </Link>
        </div>
      </div>
    </header>
  );
}
