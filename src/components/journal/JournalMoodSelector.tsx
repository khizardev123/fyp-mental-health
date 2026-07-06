"use client";

import { MOODS } from "./journalContent";

type JournalMoodSelectorProps = {
  selected: string | null;
  onSelect: (label: string) => void;
};

export function JournalMoodSelector({
  selected,
  onSelect,
}: JournalMoodSelectorProps) {
  return (
    <div className="card-padded bg-card">
      <p className="label-muted mb-4">How are you feeling right now?</p>
      <p className="mb-4 text-xs text-foreground-secondary">
        Optional — choose a mood to guide your reflection. This stays on your
        device and is not saved.
      </p>
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Mood selection"
      >
        {MOODS.map((mood) => {
          const isActive = selected === mood.label;
          return (
            <button
              key={mood.label}
              type="button"
              onClick={() => onSelect(isActive ? "" : mood.label)}
              aria-pressed={isActive}
              className={`inline-flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm transition-all duration-200 ${
                isActive
                  ? "border-primary bg-hover-bg text-foreground shadow-card"
                  : "border-border bg-background-secondary/60 text-foreground-secondary hover:border-primary/40 hover:bg-hover-bg hover:text-foreground"
              }`}
            >
              <span className="text-lg" aria-hidden>
                {mood.emoji}
              </span>
              <span>{mood.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
