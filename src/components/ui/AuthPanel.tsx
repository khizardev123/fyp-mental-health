"use client";

import { useState } from "react";
import {
  AUTH_FEATURES,
  AUTH_QUOTES,
  AUTH_VARIANTS,
  pickRandom,
} from "./authPanelContent";

type AuthPanelProps = {
  variant?: "login" | "signup";
  accent?: "lavender" | "blue" | "peach";
};

const accentStyles = {
  lavender: "from-section to-background-secondary",
  blue: "from-background-secondary to-hover-bg",
  peach: "from-hover-bg to-section",
};

function FeatureIcon({ id }: { id: (typeof AUTH_FEATURES)[number]["id"] }) {
  const className = "h-4 w-4 text-primary";
  if (id === "journal") {
    return (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    );
  }
  if (id === "insights") {
    return (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    );
  }
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
    </svg>
  );
}

export function AuthPanel({
  variant = "login",
  accent = "lavender",
}: AuthPanelProps) {
  const [quote] = useState(() => pickRandom(AUTH_QUOTES));
  const content = AUTH_VARIANTS[variant];

  return (
    <div
      className={`relative hidden min-h-[440px] flex-1 overflow-hidden rounded-3xl border border-border bg-gradient-to-br shadow-soft lg:block ${accentStyles[accent]}`}
      aria-hidden
    >
      <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-primary/20 blur-2xl" />
      <div className="absolute -bottom-12 -left-8 h-48 w-48 rounded-full bg-primary-secondary/30 blur-3xl" />
      <span
        className="animate-float-gentle pointer-events-none absolute right-10 top-10 text-base opacity-20"
        aria-hidden
      >
        🌿
      </span>

      <div className="relative flex h-full min-h-[440px] flex-col justify-end p-10">
        <p className="fade-in mb-3 text-xs font-medium uppercase tracking-[0.2em] text-primary">
          SereneMind
        </p>

        <div className="max-w-sm space-y-4">
          <div className="fade-in-delay-1">
            <h2 className="font-serif text-2xl leading-relaxed text-foreground">
              {content.heading}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
              {content.message}
            </p>
            <p className="mt-1.5 font-serif text-xs italic leading-relaxed text-foreground-secondary/90">
              {content.calm}
            </p>
          </div>

          <blockquote className="fade-in-delay-2 border-l-2 border-primary/45 pl-3">
            <p className="font-serif text-lg leading-relaxed text-foreground">
              &ldquo;{quote}&rdquo;
            </p>
          </blockquote>

          <ul className="fade-in-delay-2 space-y-2">
            {AUTH_FEATURES.map((feature) => (
              <li
                key={feature.id}
                className="group flex items-center gap-2.5 text-sm text-foreground-secondary transition-colors duration-300 hover:text-foreground"
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-card/50 transition-transform duration-300 group-hover:scale-105">
                  <FeatureIcon id={feature.id} />
                </span>
                <span>{feature.label}</span>
              </li>
            ))}
          </ul>

          <p className="fade-in-delay-3 flex items-start gap-2 text-xs leading-relaxed text-foreground-secondary">
            <span className="mt-0.5 shrink-0" aria-hidden>
              <svg className="h-3.5 w-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </span>
            <span>Private and secure — only you can read your entries.</span>
          </p>
        </div>

        <div className="mt-8 flex gap-2">
          <span className="h-1.5 w-8 rounded-full bg-primary/60" />
          <span className="h-1.5 w-4 rounded-full bg-primary/30" />
          <span className="h-1.5 w-4 rounded-full bg-primary/20" />
        </div>
      </div>
    </div>
  );
}
