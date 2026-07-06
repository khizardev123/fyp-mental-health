"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/ui/AppHeader";
import { LoadingScreen } from "@/components/ui/LoadingScreen";

type MeResponse =
  | { user: { id: string; email: string; name: string } }
  | { error: string };

export default function DashboardPage() {
  const [state, setState] = useState<"loading" | "authed" | "unauthorized">("loading");
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const res = await fetch("/api/me", {
          credentials: "same-origin",
          signal: ac.signal,
        });
        const data = (await res.json()) as MeResponse;
        if (!res.ok || !("user" in data)) {
          setState("unauthorized");
          return;
        }
        setUser(data.user);
        setState("authed");
      } catch {
        if (ac.signal.aborted) return;
        setState("unauthorized");
      }
    })();
    return () => ac.abort();
  }, []);

  if (state === "loading") {
    return <LoadingScreen message="Loading your space…" />;
  }

  if (state === "unauthorized") {
    return (
      <div className="page-shell flex flex-col items-center justify-center px-6 text-center">
        <span
          className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-section text-2xl"
          aria-hidden
        >
          🔒
        </span>
        <h1 className="section-title text-2xl md:text-3xl">Sign in required</h1>
        <p className="mt-3 max-w-md text-foreground-secondary">
          You need to be signed in to view your personal wellness space.
        </p>
        <Link href="/login" className="btn-primary mt-8">
          Go to sign in
        </Link>
      </div>
    );
  }

  const firstName = user?.name?.split(" ")[0] ?? "there";

  return (
    <div className="page-shell">
      <AppHeader />

      <main className="page-main fade-in">
        <div className="mb-12">
          <p className="text-sm font-medium text-primary">Welcome back</p>
          <h1 className="section-title mt-2">
            Hello, {firstName} 👋
          </h1>
          <p className="section-subtitle">
            This is your personal wellness journal. Take a moment to check in
            with yourself today.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <Link href="/journal" className="card-hover group block">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-hover-bg text-xl transition group-hover:scale-105">
              📔
            </div>
            <p className="text-xs font-medium uppercase tracking-widest text-foreground-secondary">
              Journal
            </p>
            <h2 className="mt-2 font-serif text-xl text-foreground">
              Write a journal entry
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
              Record how you feel today in a peaceful, private space.
            </p>
          </Link>

          <Link href="/chat" className="card-hover group block">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-section text-xl transition group-hover:scale-105">
              💬
            </div>
            <p className="text-xs font-medium uppercase tracking-widest text-foreground-secondary">
              Support chat
            </p>
            <h2 className="mt-2 font-serif text-xl text-foreground">
              Talk to your companion
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
              Share what&apos;s on your mind with your caring AI companion.
            </p>
          </Link>
        </div>

        <div className="card-padded mt-8 surface-secondary">
          <p className="text-sm text-foreground-secondary">
            Signed in as{" "}
            <span className="font-medium text-foreground">{user?.name}</span>
            <span className="text-foreground-secondary/70">
              {" "}
              · {user?.email}
            </span>
          </p>
        </div>

        <p className="mt-10 text-xs text-foreground-secondary/60">
          More features (avatar, analytics) are coming next.
        </p>
      </main>
    </div>
  );
}
