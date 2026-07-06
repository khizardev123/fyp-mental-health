"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="page-shell flex flex-col items-center justify-center px-6 text-center">
      <span
        className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-section text-3xl"
        aria-hidden
      >
        🌿
      </span>
      <h1 className="section-title text-2xl md:text-3xl">Something went wrong</h1>
      <p className="mt-3 max-w-md text-foreground-secondary">
        We hit an unexpected problem. You can try again or return to a calm place.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <button type="button" onClick={() => reset()} className="btn-primary">
          Try again
        </button>
        <Link href="/" className="btn-secondary">
          Back home
        </Link>
      </div>
    </div>
  );
}
