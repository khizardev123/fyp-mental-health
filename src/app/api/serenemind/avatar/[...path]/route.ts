import { NextRequest } from "next/server";
import { proxyToAvatarService } from "@/lib/serenemind/proxyToAvatarService";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const AVATAR_PROXY_TIMEOUT_MS = 120_000;

type RouteContext = { params: Promise<{ path: string[] }> };

async function handle(req: NextRequest, ctx: RouteContext) {
  const { path } = await ctx.params;
  return proxyToAvatarService(req, "avatar", path, {
    timeoutMs: AVATAR_PROXY_TIMEOUT_MS,
    audioPathPrefix: "audio",
  });
}

export async function GET(req: NextRequest, ctx: RouteContext) {
  return handle(req, ctx);
}

export async function POST(req: NextRequest, ctx: RouteContext) {
  return handle(req, ctx);
}
