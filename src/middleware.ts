import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtVerify } from "jose";

function getJwtSecretKey() {
  const secret = process.env.JWT_SECRET;
  if (!secret) return null;
  return new TextEncoder().encode(secret);
}

function jsonUnauthorized() {
  return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
}

function jsonConfigError() {
  return NextResponse.json(
    { error: "Server configuration error." },
    { status: 500 },
  );
}

async function guardApiWithJwt(request: NextRequest) {
  const key = getJwtSecretKey();
  if (!key) return jsonConfigError();
  const token = request.cookies.get("token")?.value;
  if (!token) return jsonUnauthorized();
  try {
    await jwtVerify(token, key, { algorithms: ["HS256"] });
  } catch {
    return jsonUnauthorized();
  }
  return null;
}

async function guardPageWithJwt(request: NextRequest) {
  const key = getJwtSecretKey();
  if (!key) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  const token = request.cookies.get("token")?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  try {
    await jwtVerify(token, key, { algorithms: ["HS256"] });
  } catch {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return null;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (
    pathname.startsWith("/api/profile") ||
    pathname.startsWith("/api/journal") ||
    pathname.startsWith("/api/emotion") ||
    pathname.startsWith("/api/chat") ||
    pathname.startsWith("/api/serenemind/chat") ||
    pathname.startsWith("/api/serenemind/avatar")
  ) {
    const apiBlock = await guardApiWithJwt(request);
    if (apiBlock) return apiBlock;
    return NextResponse.next();
  }

  if (
    pathname === "/profile" ||
    pathname.startsWith("/profile/") ||
    pathname === "/journal" ||
    pathname.startsWith("/journal/") ||
    pathname === "/chat" ||
    pathname.startsWith("/chat/")
  ) {
    const pageBlock = await guardPageWithJwt(request);
    if (pageBlock) return pageBlock;
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/profile",
    "/profile/:path*",
    "/journal",
    "/journal/:path*",
    "/api/profile",
    "/api/profile/:path*",
    "/api/journal",
    "/api/journal/:path*",
    "/api/emotion",
    "/api/emotion/:path*",
    "/chat",
    "/chat/:path*",
    "/api/chat",
    "/api/chat/:path*",
    "/api/serenemind/chat",
    "/api/serenemind/chat/:path*",
    "/api/serenemind/avatar",
    "/api/serenemind/avatar/:path*",
  ],
};
