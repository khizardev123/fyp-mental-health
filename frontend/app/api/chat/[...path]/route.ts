import { NextRequest, NextResponse } from 'next/server';

const AVATAR_SERVICE_URL = process.env.AVATAR_SERVICE_URL || 'http://127.0.0.1:8001';
const PROXY_TIMEOUT_MS = 180_000;

async function proxyChat(req: NextRequest, path: string[]) {
    const target = `${AVATAR_SERVICE_URL}/chat/${path.join('/')}${req.nextUrl.search}`;
    const auth = req.headers.get('authorization');
    const isStream = path.join('/') === 'message/stream';

    const init: RequestInit = {
        method: req.method,
        headers: {
            'Content-Type': req.headers.get('content-type') || 'application/json',
            ...(auth ? { Authorization: auth } : {}),
        },
        signal: AbortSignal.timeout(PROXY_TIMEOUT_MS),
    };
    if (req.method !== 'GET' && req.method !== 'HEAD') {
        init.body = await req.text();
    }

    const res = await fetch(target, init);

    if (isStream) {
        return new NextResponse(res.body, {
            status: res.status,
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                Connection: 'keep-alive',
                'X-Accel-Buffering': 'no',
            },
        });
    }

    const body = await res.text();
    return new NextResponse(body, {
        status: res.status,
        headers: { 'Content-Type': res.headers.get('content-type') || 'application/json' },
    });
}

export async function GET(req: NextRequest, ctx: { params: { path: string[] } }) {
    return proxyChat(req, ctx.params.path);
}

export async function POST(req: NextRequest, ctx: { params: { path: string[] } }) {
    return proxyChat(req, ctx.params.path);
}
