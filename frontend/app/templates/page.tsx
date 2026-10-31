"use client";

import { LayoutTemplate } from "lucide-react";
import * as React from "react";

import { AppShell, RequireAuth, SearchInput } from "@/components/app-shell";
import { TemplateDialog } from "@/components/template-dialog";
import { Badge, EmptyState, Spinner } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import type { Template } from "@/lib/types";

export default function TemplatesPage() {
  return (
    <RequireAuth>
      <Templates />
    </RequireAuth>
  );
}

function Templates() {
  const [templates, setTemplates] = React.useState<Template[] | null>(null);
  const [query, setQuery] = React.useState("");
  const [active, setActive] = React.useState<Template | null>(null);

  React.useEffect(() => {
    const params = query ? `?q=${encodeURIComponent(query)}` : "";
    let cancelled = false;
    const timer = window.setTimeout(() => {
      apiGet<Template[]>(`/api/templates${params}`)
        .then((data) => !cancelled && setTemplates(data))
        .catch(() => !cancelled && setTemplates([]));
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  const categories = React.useMemo(() => {
    if (!templates) return [];
    const map = new Map<string, Template[]>();
    for (const template of templates) {
      const list = map.get(template.category) ?? [];
      list.push(template);
      map.set(template.category, list);
    }
    return Array.from(map.entries());
  }, [templates]);

  return (
    <AppShell
      search={
        <SearchInput value={query} onChange={setQuery} placeholder="Search templates…" />
      }
    >
      <div className="mb-5">
        <h1 className="font-display text-[28px] font-semibold leading-9 tracking-tight text-ink">
          Templates
        </h1>
        <p className="mt-1 text-[14.5px] text-muted">
          Start from a structured layout, fill in the details, then refine with AI.
        </p>
      </div>

      {templates === null ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : templates.length === 0 ? (
        <EmptyState
          title="No templates found"
          description="Try a different search term."
        />
      ) : (
        <div className="space-y-8">
          {categories.map(([category, items]) => (
            <section key={category}>
              <h2 className="mb-3 font-display text-[13px] font-medium uppercase tracking-wide text-subtle">
                {category}
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((template) => (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => setActive(template)}
                    className="group rounded-xl border border-line bg-white p-4 text-left shadow-l1 transition-all hover:-translate-y-0.5 hover:border-brand/40"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-lavender text-brand">
                        <LayoutTemplate size={15} />
                      </span>
                      {template.fields.length > 0 ? (
                        <Badge className="bg-white border-line text-muted">
                          {template.fields.length} fields
                        </Badge>
                      ) : (
                        <Badge className="bg-lavender border-transparent text-brand">
                          Blank
                        </Badge>
                      )}
                    </div>
                    <h3 className="mt-3 font-display text-[15px] font-semibold text-ink">
                      {template.name}
                    </h3>
                    <p className="mt-1 text-[13px] leading-5 text-muted">
                      {template.description}
                    </p>
                    <p className="mt-3 line-clamp-2 text-[12.5px] leading-5 text-subtle">
                      {template.preview}
                    </p>
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      <TemplateDialog template={active} onClose={() => setActive(null)} />
    </AppShell>
  );
}
