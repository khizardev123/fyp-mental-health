"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/ui/AppHeader";
import { JournalInsightCard } from "@/components/journal/JournalInsightCard";
import { JournalMoodSelector } from "@/components/journal/JournalMoodSelector";
import { JournalWellnessPanel } from "@/components/journal/JournalWellnessPanel";
import {
  MOTIVATIONAL_QUOTES,
  pickRandom,
  REFLECTION_PROMPTS,
  WRITING_REMINDERS,
} from "@/components/journal/journalContent";

type JournalEntryResponse = {
  id: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  emotion: string | null;
  confidence: number | null;
  emotionMessage: string | null;
};

type EmotionInsight = {
  emotion: string;
  confidence: number;
  message: string;
};

function formatEntryDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export default function JournalPage() {
  const [todayLabel, setTodayLabel] = useState("");
  const [content, setContent] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);
  const [insight, setInsight] = useState<EmotionInsight | null>(null);
  const [selectedMood, setSelectedMood] = useState<string | null>(null);

  const [reflectionPrompt] = useState(() => pickRandom(REFLECTION_PROMPTS));
  const [writingReminder] = useState(() => pickRandom(WRITING_REMINDERS));
  const [dailyQuote] = useState(() => pickRandom(MOTIVATIONAL_QUOTES));

  const [entries, setEntries] = useState<JournalEntryResponse[]>([]);
  const [listStatus, setListStatus] = useState<"loading" | "ready" | "error">("loading");
  const [listError, setListError] = useState<string | null>(null);

  const loadEntries = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setListStatus("loading");
    setListError(null);
    try {
      const res = await fetch("/api/journal", { credentials: "same-origin" });
      const data = (await res.json()) as {
        error?: string;
        entries?: JournalEntryResponse[];
      };
      if (!res.ok) {
        setListStatus("error");
        setListError(data.error ?? "Could not load entries.");
        return;
      }
      setEntries(data.entries ?? []);
      setListStatus("ready");
    } catch {
      setListStatus("error");
      setListError("Network error. Please try again.");
    }
  }, []);

  useEffect(() => { void loadEntries(); }, [loadEntries]);

  useEffect(() => {
    setTodayLabel(
      new Date().toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
      }),
    );
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setClientError(null);

    const trimmed = content.trim();
    if (!trimmed) {
      setClientError("Please write something before submitting.");
      return;
    }

    setStatus("saving");
    setInsight(null);
    try {
      const res = await fetch("/api/journal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ content: trimmed }),
      });

      const data = (await res.json()) as {
        error?: string;
        message?: string;
        fieldErrors?: { content?: string[] };
        entry?: JournalEntryResponse;
      };

      if (!res.ok) {
        setStatus("error");
        const fe = data.fieldErrors?.content?.[0];
        setMessage(fe ?? data.error ?? "Could not save your entry.");
        return;
      }

      setStatus("success");
      setMessage(data.message ?? "Journal entry saved.");
      setContent("");

      const entry = data.entry;
      if (entry?.emotion && typeof entry.confidence === "number" && entry.emotionMessage) {
        setInsight({
          emotion: entry.emotion,
          confidence: entry.confidence,
          message: entry.emotionMessage,
        });
      }

      void loadEntries({ silent: true });
    } catch {
      setStatus("error");
      setMessage("Network error. Please try again.");
    }
  }

  return (
    <div className="page-shell">
      <AppHeader
        maxWidth="4xl"
        nav={[
          { href: "/dashboard", label: "Dashboard" },
          { href: "/chat", label: "Chat" },
          { href: "/profile", label: "Profile" },
        ]}
      />

      <main className="fade-in mx-auto max-w-4xl px-6 py-10 md:py-14">
        {/* 1. Welcome Header */}
        <header className="mb-12 text-center md:text-left">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
            {todayLabel || "\u00a0"}
          </p>
          <h1 className="section-title mt-4 max-w-2xl">
            Take a deep breath. This is your safe space.
          </h1>
          <p className="section-subtitle max-w-2xl">
            There is no right or wrong way to journal. Write as much or as
            little as you need — your words are welcome here, exactly as they
            are.
          </p>
        </header>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_272px] lg:items-start">
          {/* Main writing column */}
          <div className="space-y-6">
            {/* 2. Daily Reflection Card */}
            <div className="card-padded bg-gradient-to-br from-section/80 to-hover-bg/50 transition hover:shadow-soft">
              <div className="flex items-start gap-4">
                <span
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-card text-xl shadow-card"
                  aria-hidden
                >
                  💭
                </span>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                    Today&apos;s reflection
                  </p>
                  <p className="mt-2 font-serif text-xl leading-relaxed text-foreground md:text-2xl">
                    {reflectionPrompt}
                  </p>
                </div>
              </div>
            </div>

            {/* 3. Mood Selection (UI only) */}
            <JournalMoodSelector
              selected={selectedMood}
              onSelect={(label) => setSelectedMood(label || null)}
            />

            {/* 4–6. Journal Writing Area */}
            <form
              onSubmit={handleSubmit}
              className="card overflow-hidden bg-card shadow-soft"
            >
              <div className="border-b border-border bg-background-secondary/40 px-6 py-4 md:px-8">
                <label htmlFor="journal-content" className="label-text mb-0">
                  Your journal entry
                </label>
                <p className="mt-1 text-xs text-foreground-secondary">
                  {writingReminder}
                </p>
              </div>

              <div className="space-y-6 p-6 md:p-8">
                {(message || clientError) && (
                  <div
                    role="alert"
                    className={
                      status === "success" && !clientError
                        ? "alert-success"
                        : "alert-error"
                    }
                  >
                    {clientError ?? message}
                  </div>
                )}

                <div className="relative">
                  <textarea
                    id="journal-content"
                    name="content"
                    rows={18}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Write freely… This is your private space to express your thoughts."
                    maxLength={50_000}
                    className="textarea-field min-h-[360px] w-full rounded-2xl border-border bg-background-secondary/30 px-6 py-6 text-base leading-[1.85] shadow-inner transition focus:shadow-card md:min-h-[420px] md:text-lg"
                  />
                  <p className="mt-3 text-right text-xs text-foreground-secondary">
                    {content.length.toLocaleString()} / 50,000
                  </p>
                </div>

                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm italic text-foreground-secondary">
                    &ldquo;There is no perfect way to journal.&rdquo;
                  </p>
                  <button
                    type="submit"
                    disabled={status === "saving"}
                    className="btn-primary shrink-0 px-8"
                  >
                    {status === "saving" ? "Saving & reflecting…" : "Save entry"}
                  </button>
                </div>
              </div>
            </form>

            {/* 6. AI Insight Section */}
            {insight && (
              <JournalInsightCard
                emotion={insight.emotion}
                confidence={insight.confidence}
                message={insight.message}
              />
            )}

            {/* 9. Motivational Quote */}
            <blockquote className="card-padded surface-secondary text-center">
              <p className="font-serif text-xl leading-relaxed text-foreground md:text-2xl">
                &ldquo;{dailyQuote.text}&rdquo;
              </p>
              <footer className="mt-4 text-sm text-foreground-secondary">
                — {dailyQuote.author}
              </footer>
            </blockquote>
          </div>

          {/* 7–8. Wellness Sidebar */}
          <div className="lg:sticky lg:top-6">
            <JournalWellnessPanel />
          </div>
        </div>

        {/* Entry History */}
        <section className="mt-16 border-t border-border pt-14" aria-labelledby="journal-history-heading">
          <div className="mb-8">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-foreground-secondary">
              Your story so far
            </p>
            <h2
              id="journal-history-heading"
              className="mt-2 font-serif text-2xl text-foreground md:text-3xl"
            >
              Past entries
            </h2>
            <p className="mt-2 text-sm text-foreground-secondary">
              Newest first. Only you can see these.
            </p>
          </div>

          {listStatus === "loading" && (
            <p className="text-sm text-foreground-secondary">Loading entries…</p>
          )}

          {listStatus === "error" && listError && (
            <div role="alert" className="alert-error">
              {listError}
            </div>
          )}

          {listStatus === "ready" && entries.length === 0 && (
            <div className="card-padded border-dashed surface-secondary text-center">
              <span
                className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-section text-xl"
                aria-hidden
              >
                📔
              </span>
              <p className="font-serif text-lg text-foreground">
                Your journal awaits your first words
              </p>
              <p className="mt-2 text-sm text-foreground-secondary">
                When you save above, your entries will appear here — a gentle
                record of your journey.
              </p>
            </div>
          )}

          {listStatus === "ready" && entries.length > 0 && (
            <ul className="space-y-5">
              {entries.map((entry) => (
                <li
                  key={entry.id}
                  className="card-padded border-l-4 border-l-primary/50 transition duration-300 hover:-translate-y-0.5 hover:shadow-soft"
                >
                  <time
                    dateTime={entry.createdAt}
                    className="text-xs font-medium uppercase tracking-wide text-foreground-secondary"
                  >
                    {formatEntryDate(entry.createdAt)}
                  </time>
                  <p className="mt-4 whitespace-pre-wrap break-words text-base leading-relaxed text-foreground">
                    {entry.content}
                  </p>
                  <div className="mt-5 rounded-2xl bg-section/60 px-5 py-4 text-sm">
                    <p className="text-foreground-secondary">
                      <span className="font-medium text-foreground">
                        How you seemed to feel:{" "}
                      </span>
                      {entry.emotion ?? "—"}
                    </p>
                    <p className="mt-2 leading-relaxed text-foreground-secondary">
                      <span className="font-medium text-foreground">
                        A note for you:{" "}
                      </span>
                      {entry.emotionMessage ?? "—"}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
