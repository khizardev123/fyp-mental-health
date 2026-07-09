/** @type {import('next').NextConfig} */
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';
const AVATAR_SERVICE_URL = process.env.AVATAR_SERVICE_URL || 'http://127.0.0.1:8001';

const nextConfig = {
    output: "standalone",
    reactStrictMode: true,
    eslint: {
        ignoreDuringBuilds: true,
    },
    async rewrites() {
        return [
            { source: '/api/ai/:path*', destination: `${AI_SERVICE_URL}/:path*` },
            { source: '/api/auth/:path*', destination: `${AVATAR_SERVICE_URL}/auth/:path*` },
            // /api/chat and /api/avatar use App Router proxy routes (long Ollama/TTS timeouts)
        ];
    }
};

export default nextConfig;
