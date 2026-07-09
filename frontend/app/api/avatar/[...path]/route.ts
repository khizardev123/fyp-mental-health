import { NextRequest, NextResponse } from 'next/server';

const AVATAR_SERVICE_URL = process.env.AVATAR_SERVICE_URL || 'http://127.0.0.1:8001';
const PROXY_TIMEOUT_MS = 120_000;

async function proxyAvatar(req: NextRequest, path: string[]) {
    const target = `${AVATAR_SERVICE_URL}/avatar/${path.join('/')}${req.nextUrl.search}`;
    const auth = req.headers.get('authorization');
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
    const contentType = res.headers.get('content-type') || 'application/json';
    if (contentType.includes('audio') || path[0] === 'audio') {
        const buffer = await res.arrayBuffer();
        return new NextResponse(buffer, { status: res.status, headers: { 'Content-Type': contentType } });
    }
    const body = await res.text();
    return new NextResponse(body, {
        status: res.status,
        headers: { 'Content-Type': contentType },
    });
}

export async function GET(req: NextRequest, ctx: { params: { path: string[] } }) {
    return proxyAvatar(req, ctx.params.path);
}

export async function POST(req: NextRequest, ctx: { params: { path: string[] } }) {
    return proxyAvatar(req, ctx.params.path);
}
