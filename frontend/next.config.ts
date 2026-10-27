import type { NextConfig } from 'next';
const isExport = process.env.NEXT_OUTPUT_EXPORT === '1';
const config: NextConfig = {
  output: isExport
    ? 'export'
    : process.env.NEXT_OUTPUT_STANDALONE === '1'
      ? 'standalone'
      : undefined,
  basePath: process.env.NEXT_BASE_PATH || undefined,
  poweredByHeader: false,
  ...(!isExport
    ? {
        async rewrites() {
          return process.env.API_PROXY_TARGET
            ? [
                {
                  source: '/api/:path*',
                  destination: `${process.env.API_PROXY_TARGET}/api/:path*`,
                },
              ]
            : [];
        },
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
      }
    : {}),
  devIndicators: false,
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
};
export default config;
