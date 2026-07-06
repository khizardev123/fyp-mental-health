/**
 * Maps DB/config errors from connectDB, Mongoose, or JWT signing to HTTP responses.
 * Returns null if the error is not a known infrastructure issue.
 */
export function mapInfrastructureFailure(
  err: unknown,
): { status: number; body: { error: string } } | null {
  const msg = err instanceof Error ? err.message : String(err);

  if (msg.includes("MONGODB_URI")) {
    return {
      status: 503,
      body: {
        error:
          "Database is not configured. Add MONGODB_URI to .env.local (copy from .env.example) and restart the dev server.",
      },
    };
  }

  if (msg.includes("JWT_SECRET")) {
    return {
      status: 500,
      body: {
        error:
          "Server is not configured. Add JWT_SECRET to .env.local (copy from .env.example) and restart the dev server.",
      },
    };
  }

  if (
    /ECONNREFUSED|ENOTFOUND|querySrv|MongoNetworkError|MongooseServerSelectionError|MongoServerSelectionError|Server selection timed out|getaddrinfo/i.test(
      msg,
    )
  ) {
    return {
      status: 503,
      body: {
        error:
          "Cannot connect to MongoDB. In Atlas, open Database & Network Access → IP Access List, add your IP (or 0.0.0.0/0 for dev), then restart the dev server.",
      },
    };
  }

  return null;
}
