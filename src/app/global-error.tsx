"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily: "system-ui, sans-serif",
          background: "#faf8f5",
          color: "#2d2a26",
        }}
      >
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "2rem",
            textAlign: "center",
          }}
        >
          <h1 style={{ fontSize: "1.5rem", marginBottom: "0.75rem" }}>
            Something went wrong
          </h1>
          <p style={{ maxWidth: "28rem", color: "#6b6560", marginBottom: "2rem" }}>
            A critical error occurred. Please try again.
          </p>
          <button
            type="button"
            onClick={() => reset()}
            style={{
              padding: "0.75rem 1.5rem",
              borderRadius: "0.75rem",
              border: "none",
              background: "#7c9a82",
              color: "#fff",
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
