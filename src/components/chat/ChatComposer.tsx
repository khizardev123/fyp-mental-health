"use client";

type ChatComposerProps = {
  className?: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  sending?: boolean;
};

export function ChatComposer({
  className = "",
  value,
  onChange,
  onSubmit,
  disabled,
  sending,
}: ChatComposerProps) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && !sending && value.trim()) onSubmit();
    }
  }

  return (
    <div
      className={`border-t border-border bg-footer px-4 py-4 backdrop-blur-sm ${className}`}
    >
      <div className="mx-auto flex max-w-3xl gap-3">
        <label htmlFor="chat-input" className="sr-only">
          Message
        </label>
        <textarea
          id="chat-input"
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Share what's on your mind…"
          disabled={disabled || sending}
          className="max-h-40 min-h-[48px] flex-1 resize-y rounded-2xl border border-border bg-card px-4 py-3 text-sm text-foreground outline-none transition placeholder:text-foreground-secondary/55 focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || sending || !value.trim()}
          className="btn-primary shrink-0 px-5 py-3"
        >
          {sending ? "Sending…" : "Send"}
        </button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-foreground-secondary/70">
        This is a supportive companion, not a substitute for professional care.
      </p>
    </div>
  );
}
