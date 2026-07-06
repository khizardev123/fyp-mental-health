import { cookies } from "next/headers";

/**
 * Reads the main-app JWT from the HTTP-only cookie for avatar-service proxying.
 */
export async function getBearerTokenFromCookie(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get("token")?.value ?? null;
}
