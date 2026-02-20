/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    reactStrictMode: true,
    eslint: {
        ignoreDuringBuilds: true,
    },
    async rewrites() {
        return [
            { source: '/api/ai/:path*', destination: 'http://127.0.0.1:8000/:path*' },
            { source: '/api/avatar/:path*', destination: 'http://127.0.0.1:8001/avatar/:path*' }
        ];
    }
};

export default nextConfig;
