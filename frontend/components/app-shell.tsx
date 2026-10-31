"use client";

import { FileText, LayoutTemplate, LogOut, Search, Sparkles } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export function AppShell({
  children,
  search,
  actions,
}: {
  children: React.ReactNode;
  search?: React.ReactNode;
  actions?: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const nav = [
    { href: "/dashboard", label: "Documents", icon: FileText },
    { href: "/templates", label: "Templates", icon: LayoutTemplate },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="sticky top-0 z-30 border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-4 px-4 sm:px-6">
          <a href="/dashboard" className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand text-white">
              <Sparkles size={15} />
            </span>
            <span className="font-display text-[15px] font-semibold tracking-tight text-ink">
              DocsDrafter
            </span>
          </a>

          <nav className="ml-2 hidden items-center gap-1 sm:flex">
            {nav.map((item) => {
              const active = pathname?.startsWith(item.href);
              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 font-display text-[13px] font-medium transition-colors",
                    active
                      ? "bg-lavender text-brand"
                      : "text-muted hover:bg-canvas hover:text-ink",
                  )}
                >
                  <item.icon size={14} />
                  {item.label}
                </a>
              );
            })}
          </nav>

          <div className="flex-1" />

          {search ? <div className="hidden md:block">{search}</div> : null}
          {actions}

          <div className="hidden items-center gap-2 border-l border-line pl-3 sm:flex">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-lavender font-display text-[11px] font-semibold text-brand">
              {(user?.name || user?.email || "?").slice(0, 1).toUpperCase()}
            </div>
            <div className="leading-tight">
              <div className="font-display text-[12.5px] font-medium text-ink">
                {user?.name || "Account"}
              </div>
              <button
                type="button"
                onClick={async () => {
                  await logout();
                  router.push("/login");
                }}
                className="flex items-center gap-1 text-[11.5px] text-subtle transition-colors hover:text-danger"
              >
                <LogOut size={11} /> Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
        {children}
      </main>
    </div>
  );
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="relative">
      <Search
        size={14}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
      />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="focus-ring h-9 w-56 rounded-lg border border-line bg-white pl-8 pr-3 text-[13.5px] text-ink placeholder:text-subtle shadow-l1 transition-all focus:w-72"
      />
    </div>
  );
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <div className="flex items-center gap-2 text-[13px] text-muted">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-brand" />
          Loading workspace…
        </div>
      </div>
    );
  }
  return <>{children}</>;
}

export { Button };
