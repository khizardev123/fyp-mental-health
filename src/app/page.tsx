import Link from "next/link";
import { HomePageSections } from "@/components/home/HomePageSections";

export default function HomePage() {
  return (
    <div className="page-shell relative overflow-hidden">
      {/* Soft decorative blobs */}
      <div
        className="pointer-events-none absolute -left-24 top-20 h-72 w-72 rounded-full bg-primary-secondary/40 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-16 top-40 h-64 w-64 rounded-full bg-section/80 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute bottom-20 left-1/3 h-56 w-56 rounded-full bg-hover-bg/70 blur-3xl"
        aria-hidden
      />

      <header className="relative z-10 border-b border-border bg-navbar backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
          <Link
            href="/"
            className="font-serif text-xl tracking-tight text-foreground"
          >
            SereneMind
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login" className="nav-link px-2 py-1">
              Sign in
            </Link>
            <Link href="/signup" className="btn-primary px-5 py-2.5 text-sm">
              Get started
            </Link>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col items-center justify-center px-6 py-16 text-center">
        <p className="fade-in mb-6 text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
          Your wellness companion
        </p>

        <div className="fade-in-delay-1 mb-6 flex items-center justify-center gap-3">
          <span
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-section text-2xl shadow-card"
            aria-hidden
          >
            🌸
          </span>
          <h1 className="section-title max-w-2xl text-left md:text-center">
            A calm space for your
            <br />
            <span className="text-primary">emotional wellbeing</span>
          </h1>
        </div>

        <p className="fade-in-delay-2 mb-12 max-w-xl text-lg leading-relaxed text-foreground-secondary">
          SereneMind offers gentle journaling, supportive AI conversations, and
          thoughtful emotional insights — designed to help you feel heard, safe,
          and understood.
        </p>

        <div className="fade-in-delay-2 flex flex-wrap items-center justify-center gap-4">
          <Link href="/signup" className="btn-primary px-8 py-3.5">
            Begin your journey
          </Link>
          <Link href="/login" className="btn-secondary px-8 py-3.5">
            I already have an account
          </Link>
        </div>

        <div className="fade-in-delay-2 mt-20 grid w-full max-w-3xl grid-cols-1 gap-5 sm:grid-cols-3">
          {[
            {
              icon: "📔",
              title: "Journal",
              desc: "Write freely in a peaceful space",
              bg: "bg-hover-bg",
            },
            {
              icon: "💬",
              title: "Support chat",
              desc: "Talk with a caring AI companion",
              bg: "bg-section",
            },
            {
              icon: "✨",
              title: "Insights",
              desc: "Gentle reflections on how you feel",
              bg: "bg-background-secondary",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="card-hover flex flex-col items-center p-6 text-center"
            >
              <span
                className={`mb-4 flex h-12 w-12 items-center justify-center rounded-2xl text-xl ${feature.bg}`}
                aria-hidden
              >
                {feature.icon}
              </span>
              <h2 className="font-serif text-lg text-foreground">
                {feature.title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </main>

      <HomePageSections />
    </div>
  );
}
