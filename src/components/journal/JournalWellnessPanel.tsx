import { WELLNESS_REMINDERS } from "./journalContent";

export function JournalWellnessPanel() {
  return (
    <aside className="space-y-5" aria-label="Wellness reminders">
      <div className="card-padded bg-card">
        <p className="label-muted mb-4">Gentle reminders</p>
        <ul className="space-y-3">
          {WELLNESS_REMINDERS.map((item) => (
            <li
              key={item.text}
              className="flex items-center gap-3 rounded-xl bg-background-secondary/50 px-3 py-2.5 text-sm text-foreground-secondary transition hover:bg-hover-bg"
            >
              <span className="text-base" aria-hidden>
                {item.icon}
              </span>
              <span>{item.text}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="card-padded border-l-4 border-l-primary bg-card">
        <div className="flex items-start gap-3">
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-section text-base"
            aria-hidden
          >
            🔒
          </span>
          <div>
            <p className="font-serif text-base text-foreground">
              Your private safe space
            </p>
            <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
              Your journal is private and securely stored. This is your personal
              safe space — only you can read what you write here.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
