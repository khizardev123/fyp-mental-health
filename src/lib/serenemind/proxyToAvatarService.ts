import { NextRequest, NextResponse } from "next/server";
import { getBearerTokenFromCookie } from "@/lib/serenemind/proxyAuth";

const AVATAR_SERVICE_URL =
  process.env.AVATAR_SERVICE_URL || "http://127.0.0.1:8001";

type ProxyOptions = {
  timeoutMs: number;
  streamPath?: string;
  audioPathPrefix?: string;
};

export async function proxyToAvatarService(
  req: NextRequest,
  pathPrefix: "chat" | "avatar",
  path: string[],
  options: ProxyOptions,
): Promise<NextResponse> {
  const token = await getBearerTokenFromCookie();
  if (!token) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  const target = `${AVATAR_SERVICE_URL}/${pathPrefix}/${path.join("/")}${req.nextUrl.search}`;
  const pathKey = path.join("/");
  const isStream = options.streamPath !== undefined && pathKey === options.streamPath;

  const init: RequestInit = {
    method: req.method,
    headers: {
      "Content-Type": req.headers.get("content-type") || "application/json",
      Authorization: `Bearer ${token}`,
    },
    signal: AbortSignal.timeout(options.timeoutMs),
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  let res: Response;
  try {
    res = await fetch(target, init);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Avatar service unreachable.";
    return NextResponse.json(
      { error: "Avatar service unavailable.", detail: message },
      { status: 502 },
    );
  }

  if (isStream) {
    return new NextResponse(res.body, {
      status: res.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  }

  const contentType = res.headers.get("content-type") || "application/json";
  const isAudio =
    contentType.includes("audio") ||
    (options.audioPathPrefix !== undefined && path[0] === options.audioPathPrefix);

  if (isAudio) {
    const buffer = await res.arrayBuffer();
    return new NextResponse(buffer, {
      status: res.status,
      headers: { "Content-Type": contentType },
    });
  }

  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": contentType },
  });
}
