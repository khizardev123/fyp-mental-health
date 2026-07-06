import Link from "next/link";

type NavItem = {
  href: string;
  label: string;
};

type AppHeaderProps = {
  title?: string;
  subtitle?: string;
  maxWidth?: "3xl" | "4xl";
  nav?: NavItem[];
};

const defaultNav: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/journal", label: "Journal" },
  { href: "/profile", label: "Profile" },
];

export function AppHeader({
  title,
  subtitle,
  maxWidth = "4xl",
  nav = defaultNav,
}: AppHeaderProps) {
  const maxW = maxWidth === "3xl" ? "max-w-3xl" : "max-w-4xl";

  return (
    <header className="border-b border-border bg-navbar backdrop-blur-sm">
      <div
        className={`mx-auto flex ${maxW} flex-wrap items-center justify-between gap-4 px-6 py-5`}
      >
        <div>
          <Link
            href="/"
            className="font-serif text-xl tracking-tight text-foreground transition hover:text-primary"
          >
            SereneMind
          </Link>
          {title && (
            <h1 className="mt-1 font-serif text-lg text-foreground-secondary md:text-xl">
              {title}
            </h1>
          )}
          {subtitle && (
            <p className="mt-0.5 text-xs text-foreground-secondary">{subtitle}</p>
          )}
        </div>
        <nav className="flex flex-wrap items-center gap-5">
          {nav.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">
              {item.label}
            </Link>
          ))}
          <Link href="/" className="nav-link">
            Home
          </Link>
        </nav>
      </div>
    </header>
  );
}
