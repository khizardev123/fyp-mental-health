import Link from "next/link";

export default function NotFound() {
  return (
    <div className="page-shell flex flex-col items-center justify-center px-6 text-center">
      <span
        className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-section text-3xl"
        aria-hidden
      >
        🌿
      </span>
      <h1 className="section-title text-2xl md:text-3xl">Page not found</h1>
      <p className="mt-3 max-w-sm text-foreground-secondary">
        The page you are looking for does not exist. Let&apos;s get you back to
        a calm place.
      </p>
      <Link href="/" className="btn-primary mt-8">
        Back home
      </Link>
    </div>
  );
}
