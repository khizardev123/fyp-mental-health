import Link from "next/link";
import { QuotesCarousel } from "./QuotesCarousel";

const implementedFeatures = [
  {
    icon: "🔐",
    title: "Secure accounts",
    desc: "Create a personal account with protected sign-in so your space stays yours.",
    bg: "bg-hover-bg",
  },
  {
    icon: "📔",
    title: "Private journaling",
    desc: "Write freely and save entries that only you can access.",
    bg: "bg-section",
  },
  {
    icon: "✨",
    title: "Emotion insights",
    desc: "Receive gentle reflections on the emotions detected in your writing.",
    bg: "bg-background-secondary",
  },
  {
    icon: "💬",
    title: "AI support chat",
    desc: "Talk with a caring companion that considers your recent journal mood.",
    bg: "bg-hover-bg",
  },
  {
    icon: "🎯",
    title: "Personal profile",
    desc: "Share your preferences, emotional goals, and bio for a more personal experience.",
    bg: "bg-section",
  },
  {
    icon: "🏠",
    title: "Wellness dashboard",
    desc: "A calm home base to journal, chat, and check in with yourself.",
    bg: "bg-background-secondary",
  },
];

const wellnessTips = [
  {
    icon: "🌿",
    title: "Pause and breathe",
    tip: "Take three slow breaths before you start writing. It helps your mind settle into the moment.",
  },
  {
    icon: "📝",
    title: "Write without editing",
    tip: "Let your thoughts flow freely first. You can always return to reflect later.",
  },
  {
    icon: "☀️",
    title: "Notice small wins",
    tip: "Acknowledge one thing you handled today, no matter how small it may seem.",
  },
  {
    icon: "🤝",
    title: "Reach out when needed",
    tip: "SereneMind supports reflection, but professional care matters when you need more help.",
  },
  {
    icon: "🌙",
    title: "Create a gentle routine",
    tip: "A few minutes of journaling at the same time each day can build a comforting habit.",
  },
  {
    icon: "💚",
    title: "Speak kindly to yourself",
    tip: "Treat your inner voice with the same compassion you would offer a close friend.",
  },
];

const steps = [
  {
    step: "01",
    title: "Create an account",
    desc: "Sign up for your private SereneMind space in just a few moments.",
  },
  {
    step: "02",
    title: "Write a journal entry",
    desc: "Share your thoughts and feelings in a peaceful, distraction-free space.",
  },
  {
    step: "03",
    title: "Receive AI emotion insights",
    desc: "Get a gentle reflection on the emotions noticed in your writing.",
  },
  {
    step: "04",
    title: "Reflect & grow",
    desc: "Chat with your AI companion, revisit entries, and nurture your wellbeing.",
  },
];

export function HomePageSections() {
  return (
    <div className="relative z-10">
      {/* 1. Inspirational Quote */}
      <section
        aria-labelledby="hero-quote-heading"
        className="mx-auto max-w-5xl px-6 py-20"
      >
        <div className="card-padded surface-secondary text-center">
          <p
            id="hero-quote-heading"
            className="mb-6 text-xs font-medium uppercase tracking-[0.22em] text-foreground-secondary"
          >
            Words to carry with you
          </p>
          <blockquote className="mx-auto max-w-2xl font-serif text-2xl leading-relaxed text-foreground md:text-3xl">
            &ldquo;Almost everything will work again if you unplug it for a few
            minutes — including you.&rdquo;
          </blockquote>
          <p className="mt-6 text-sm text-foreground-secondary">
            — Anne Lamott
          </p>
        </div>
      </section>

      {/* 2. Why SereneMind? */}
      <section
        aria-labelledby="why-serenemind-heading"
        className="mx-auto max-w-5xl px-6 py-20"
      >
        <div className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
            Why SereneMind?
          </p>
          <h2
            id="why-serenemind-heading"
            className="section-title mt-4"
          >
            Support for every part of your inner world
          </h2>
          <p className="section-subtitle mx-auto max-w-2xl">
            SereneMind brings together journaling, emotional awareness, and
            supportive conversation — so you have a calm place to understand
            yourself more deeply.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2">
          {[
            {
              icon: "📔",
              title: "Journaling",
              desc: "Express your thoughts in a private, peaceful space designed for honest self-reflection.",
              bg: "bg-hover-bg",
            },
            {
              icon: "✨",
              title: "Emotion analysis",
              desc: "Gentle insights help you notice emotional patterns in your writing without judgment.",
              bg: "bg-section",
            },
            {
              icon: "💬",
              title: "AI support",
              desc: "A caring companion listens with empathy and responds with warmth and understanding.",
              bg: "bg-background-secondary",
            },
            {
              icon: "🪞",
              title: "Self-reflection",
              desc: "Revisit your entries, track how you feel over time, and grow at your own pace.",
              bg: "bg-hover-bg",
            },
          ].map((item) => (
            <div key={item.title} className="card-hover flex gap-5 p-6">
              <span
                className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-xl ${item.bg}`}
                aria-hidden
              >
                {item.icon}
              </span>
              <div>
                <h3 className="font-serif text-xl text-foreground">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Implemented Features */}
      <section
        aria-labelledby="features-heading"
        className="surface-section py-20"
      >
        <div className="mx-auto max-w-5xl px-6">
          <div className="text-center">
            <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
              What you can do today
            </p>
            <h2 id="features-heading" className="section-title mt-4">
              Features already here for you
            </h2>
            <p className="section-subtitle mx-auto max-w-2xl">
              Everything below is available now — thoughtfully built to support
              your emotional wellbeing journey.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {implementedFeatures.map((feature) => (
              <div
                key={feature.title}
                className="card-hover flex flex-col p-6 text-center"
              >
                <span
                  className={`mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl text-xl ${feature.bg}`}
                  aria-hidden
                >
                  {feature.icon}
                </span>
                <h3 className="font-serif text-lg text-foreground">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. How It Works */}
      <section
        aria-labelledby="how-it-works-heading"
        className="mx-auto max-w-5xl px-6 py-20"
      >
        <div className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
            How it works
          </p>
          <h2 id="how-it-works-heading" className="section-title mt-4">
            Your path to emotional clarity
          </h2>
          <p className="section-subtitle mx-auto max-w-2xl">
            A simple, calming flow designed to help you check in, reflect, and
            feel supported.
          </p>
        </div>

        <ol className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {steps.map((item, index) => (
            <li key={item.step} className="card-padded relative text-center">
              <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-semibold text-white">
                {item.step}
              </span>
              <h3 className="mt-4 font-serif text-lg text-foreground">
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
                {item.desc}
              </p>
              {index < steps.length - 1 && (
                <span
                  className="pointer-events-none absolute -right-3 top-1/2 hidden -translate-y-1/2 text-2xl text-primary-secondary lg:block"
                  aria-hidden
                >
                  →
                </span>
              )}
            </li>
          ))}
        </ol>
      </section>

      {/* 5. Daily Wellness Tips */}
      <section
        aria-labelledby="wellness-tips-heading"
        className="surface-secondary py-20"
      >
        <div className="mx-auto max-w-5xl px-6">
          <div className="text-center">
            <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
              Daily wellness
            </p>
            <h2 id="wellness-tips-heading" className="section-title mt-4">
              Small tips, meaningful shifts
            </h2>
            <p className="section-subtitle mx-auto max-w-2xl">
              Gentle reminders to help you care for your mind and heart each day.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {wellnessTips.map((tip) => (
              <div key={tip.title} className="card-hover p-6">
                <span
                  className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-section text-lg"
                  aria-hidden
                >
                  {tip.icon}
                </span>
                <h3 className="font-serif text-lg text-foreground">
                  {tip.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
                  {tip.tip}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Inspirational Quotes Carousel */}
      <section
        aria-labelledby="quotes-carousel-heading"
        className="mx-auto max-w-5xl px-6 py-20"
      >
        <div className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
            Inspiration
          </p>
          <h2 id="quotes-carousel-heading" className="section-title mt-4">
            Motivation for your journey
          </h2>
          <p className="section-subtitle mx-auto max-w-2xl">
            Uplifting words to remind you that healing, growth, and self-compassion
            are always within reach.
          </p>
        </div>

        <div className="card-padded mt-14">
          <QuotesCarousel />
        </div>
      </section>

      {/* 7. AI Companion */}
      <section
        aria-labelledby="ai-companion-heading"
        className="surface-section py-20"
      >
        <div className="mx-auto max-w-5xl px-6">
          <div className="card-padded flex flex-col items-center gap-8 text-center lg:flex-row lg:text-left">
            <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-3xl border border-border bg-gradient-to-br from-section to-hover-bg text-5xl shadow-soft">
              <span role="img" aria-label="AI companion">
                🌸
              </span>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
                Your AI companion
              </p>
              <h2
                id="ai-companion-heading"
                className="section-title mt-3 text-2xl md:text-3xl"
              >
                A listener who never judges
              </h2>
              <p className="mt-4 text-base leading-relaxed text-foreground-secondary">
                SereneMind&apos;s AI companion is here to offer warmth, empathy,
                and encouragement — not clinical advice. Share what&apos;s on your
                mind, and receive thoughtful responses that honor your feelings
                and support your emotional wellbeing.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-foreground-secondary">
                When you&apos;ve journaled recently, your companion gently weaves
                that context into the conversation so support feels more personal.
              </p>
              <Link href="/signup" className="btn-primary mt-6 inline-flex">
                Meet your companion
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 8. Privacy & Security */}
      <section
        aria-labelledby="privacy-heading"
        className="mx-auto max-w-5xl px-6 py-20"
      >
        <div className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-foreground-secondary">
            Privacy & security
          </p>
          <h2 id="privacy-heading" className="section-title mt-4">
            Your thoughts stay yours
          </h2>
          <p className="section-subtitle mx-auto max-w-2xl">
            SereneMind is built around trust. Your journal is a private space
            meant only for you.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-3">
          {[
            {
              icon: "🔒",
              title: "Private journals",
              desc: "Your entries are saved to your account and visible only to you.",
            },
            {
              icon: "🛡️",
              title: "Secure sign-in",
              desc: "Protected authentication helps keep your personal space safe.",
            },
            {
              icon: "🤫",
              title: "Your data, your control",
              desc: "We believe emotional wellbeing begins with feeling safe and respected.",
            },
          ].map((item) => (
            <div key={item.title} className="card-hover p-6 text-center">
              <span
                className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-section text-xl"
                aria-hidden
              >
                {item.icon}
              </span>
              <h3 className="font-serif text-lg text-foreground">
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 9. Final Call to Action */}
      <section
        aria-labelledby="final-cta-heading"
        className="surface-secondary pb-24 pt-20"
      >
        <div className="mx-auto max-w-5xl px-6 text-center">
          <div className="card-padded mx-auto max-w-2xl">
            <span
              className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-hover-bg text-2xl"
              aria-hidden
            >
              🌿
            </span>
            <h2
              id="final-cta-heading"
              className="section-title text-2xl md:text-3xl"
            >
              Your wellness journey begins with a single step
            </h2>
            <p className="mt-4 text-base leading-relaxed text-foreground-secondary">
              You deserve a space that feels calm, supportive, and entirely your
              own. Take a breath, open your journal, and let SereneMind walk
              beside you.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Link href="/signup" className="btn-primary px-8 py-3.5">
                Start journaling
              </Link>
              <Link href="/login" className="btn-secondary px-8 py-3.5">
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
