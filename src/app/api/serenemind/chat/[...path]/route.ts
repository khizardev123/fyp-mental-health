import { NextRequest } from "next/server";
import { proxyToAvatarService } from "@/lib/serenemind/proxyToAvatarService";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const CHAT_PROXY_TIMEOUT_MS = 180_000;

type RouteContext = { params: Promise<{ path: string[] }> };

async function handle(req: NextRequest, ctx: RouteContext) {
  const { path } = await ctx.params;
  return proxyToAvatarService(req, "chat", path, {
    timeoutMs: CHAT_PROXY_TIMEOUT_MS,
    streamPath: "message/stream",
  });
}

export async function GET(req: NextRequest, ctx: RouteContext) {
  return handle(req, ctx);
}

export async function POST(req: NextRequest, ctx: RouteContext) {
  return handle(req, ctx);
}
