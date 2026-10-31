"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";

export function AuthCard({
  mode,
}: {
  mode: "login" | "register";
}) {
  const { login, register, user, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [name, setName] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  const isLogin = mode === "login";

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (isLogin) await login(email, password);
      else await register(email, password, name);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-[420px]">
        <div className="mb-6 flex flex-col items-center text-center">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white shadow-l1">
            <Sparkles size={18} />
          </span>
          <h1 className="mt-3 font-display text-[28px] font-semibold leading-9 tracking-tight text-ink">
            {isLogin ? "Sign in to DocsDrafter" : "Create your workspace"}
          </h1>
          <p className="mt-1 text-[14px] text-muted">
            {isLogin
              ? "Draft, refine, version and export documents."
              : "Start from a template or describe what you need."}
          </p>
        </div>

        <form
          onSubmit={onSubmit}
          className="rounded-xl border border-line bg-white p-5 shadow-l1"
        >
          <div className="space-y-4">
            {!isLogin ? (
              <Field label="Name">
                <Input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Ada Lovelace"
                  autoComplete="name"
                />
              </Field>
            ) : null}

            <Field label="Email">
              <Input
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@company.com"
                autoComplete="email"
              />
            </Field>

            <Field
              label="Password"
              hint={isLogin ? undefined : "at least 8 characters"}
            >
              <Input
                type="password"
                required
                minLength={isLogin ? 1 : 8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                autoComplete={isLogin ? "current-password" : "new-password"}
              />
            </Field>
          </div>

          {error ? (
            <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-danger">
              {error}
            </p>
          ) : null}

          <Button
            type="submit"
            variant="primary"
            className="mt-4 w-full"
            size="lg"
            disabled={busy}
          >
            {busy ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
          </Button>

          <p className="mt-4 text-center text-[13px] text-muted">
            {isLogin ? "No account yet?" : "Already have an account?"}{" "}
            <Link
              href={isLogin ? "/register" : "/login"}
              className="font-medium text-brand hover:underline"
            >
              {isLogin ? "Create one" : "Sign in"}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
