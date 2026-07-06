import Link from "next/link";

type AuthHeaderProps = {
  ctaHref?: string;
  ctaLabel?: string;
};

export function AuthHeader({
  ctaHref = "/signup",
  ctaLabel = "Get started",
}: AuthHeaderProps) {
  return (
    <header className="border-b border-border bg-navbar backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Link
          href="/"
          className="font-serif text-xl tracking-tight text-foreground transition hover:text-primary"
        >
          <span className="relative inline-block">
            <span
              className="absolute -left-1 -top-2 text-[10px] opacity-70"
              aria-hidden
            >
              ✨
            </span>
            SereneMind
          </span>
        </Link>
        <Link href={ctaHref} className="btn-primary px-5 py-2.5 text-sm">
          {ctaLabel}
        </Link>
      </div>
    </header>
  );
}
