type JournalInsightCardProps = {
  emotion: string;
  confidence: number;
  message: string;
};

export function JournalInsightCard({
  emotion,
  confidence,
  message,
}: JournalInsightCardProps) {
  return (
    <aside
      className="card-padded fade-in border-l-4 border-l-primary bg-gradient-to-br from-card to-background-secondary/40 shadow-soft"
      aria-live="polite"
    >
      <div className="flex items-start gap-4">
        <span
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-section text-xl shadow-card"
          aria-hidden
        >
          ✨
        </span>
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            A gentle reflection for you
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className="inline-flex rounded-full bg-hover-bg px-4 py-1.5 font-serif text-base text-foreground">
              {emotion}
            </span>
            <span className="text-xs text-foreground-secondary">
              We noticed this with{" "}
              <span className="font-medium text-foreground">
                {(confidence * 100).toFixed(0)}%
              </span>{" "}
              confidence
            </span>
          </div>
          <p className="mt-5 font-serif text-lg leading-relaxed text-foreground">
            {message}
          </p>
          <p className="mt-5 text-xs leading-relaxed text-foreground-secondary">
            This reflection is here to help you notice patterns in your writing.
            It isn&apos;t a clinical assessment — just a caring mirror for your
            thoughts.
          </p>
        </div>
      </div>
    </aside>
  );
}
