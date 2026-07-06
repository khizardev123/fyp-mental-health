type ChatAvatarProps = {
  variant: "user" | "assistant";
  className?: string;
};

export function ChatAvatar({ variant, className = "" }: ChatAvatarProps) {
  if (variant === "user") {
    return (
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-background-secondary text-xs font-semibold text-foreground ${className}`}
        aria-hidden
      >
        You
      </div>
    );
  }

  return (
    <div
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-border bg-gradient-to-br from-section to-hover-bg text-lg shadow-card ${className}`}
      aria-hidden
    >
      <span role="img" aria-label="Support companion">
        🌸
      </span>
    </div>
  );
}
