"use client";

import { useCallback, useEffect, useState } from "react";

const quotes = [
  {
    text: "You don't have to control your thoughts. You just have to stop letting them control you.",
    author: "Dan Millman",
  },
  {
    text: "Self-care is giving the world the best of you, instead of what's left of you.",
    author: "Katie Reed",
  },
  {
    text: "Healing takes time, and asking for help is a courageous step.",
    author: "Unknown",
  },
  {
    text: "Your feelings are valid. Your experiences matter. Your healing is important.",
    author: "Unknown",
  },
  {
    text: "Be patient with yourself. Nothing in nature blooms all year.",
    author: "Unknown",
  },
  {
    text: "Talk to yourself like you would to someone you love.",
    author: "Brené Brown",
  },
];

export function QuotesCarousel() {
  const [active, setActive] = useState(0);

  const goTo = useCallback((index: number) => {
    setActive((index + quotes.length) % quotes.length);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((prev) => (prev + 1) % quotes.length);
    }, 7000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="relative">
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-500 ease-out"
          style={{ transform: `translateX(-${active * 100}%)` }}
        >
          {quotes.map((quote) => (
            <figure
              key={quote.text}
              className="w-full shrink-0 px-2 text-center"
            >
              <blockquote className="font-serif text-xl leading-relaxed text-foreground md:text-2xl">
                &ldquo;{quote.text}&rdquo;
              </blockquote>
              <figcaption className="mt-4 text-sm text-foreground-secondary">
                — {quote.author}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>

      <div className="mt-8 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={() => goTo(active - 1)}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card text-foreground-secondary shadow-card transition hover:bg-hover-bg hover:text-foreground"
          aria-label="Previous quote"
        >
          ‹
        </button>
        <div className="flex gap-2" role="tablist" aria-label="Quote navigation">
          {quotes.map((quote, i) => (
            <button
              key={quote.text}
              type="button"
              role="tab"
              aria-selected={i === active}
              aria-label={`Go to quote ${i + 1}`}
              onClick={() => goTo(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === active
                  ? "w-8 bg-primary"
                  : "w-2 bg-border hover:bg-primary-secondary"
              }`}
            />
          ))}
        </div>
        <button
          type="button"
          onClick={() => goTo(active + 1)}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card text-foreground-secondary shadow-card transition hover:bg-hover-bg hover:text-foreground"
          aria-label="Next quote"
        >
          ›
        </button>
      </div>
    </div>
  );
}
