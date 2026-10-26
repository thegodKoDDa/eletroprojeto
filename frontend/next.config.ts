import type { NextConfig } from 'next';
const config: NextConfig = {
  output: process.env.NEXT_OUTPUT_STANDALONE === '1' ? 'standalone' : undefined,
  poweredByHeader: false,
  async rewrites() {
    return process.env.API_PROXY_TARGET
      ? [{ source: '/api/:path*', destination: `${process.env.API_PROXY_TARGET}/api/:path*` }]
      : [];
  },
  devIndicators: false,
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'no-referrer' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        ],
      },
    ];
  },
};
export default config;
