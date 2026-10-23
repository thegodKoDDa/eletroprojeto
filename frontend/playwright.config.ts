import { defineConfig } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const databaseUrl = `sqlite:///${join(tmpdir(), `eletroprojeto-e2e-${process.pid}-${Date.now()}.db`).replaceAll('\\', '/')}`;
export default defineConfig({
  testDir: './tests/e2e',
  use: { trace: 'retain-on-failure', baseURL: 'http://127.0.0.1:3010' },
  webServer: [
    {
      command: 'node scripts/e2e-api.mjs',
      url: 'http://127.0.0.1:8010/api/v1/health',
      reuseExistingServer: false,
      env: { DATABASE_URL: databaseUrl, CORS_ORIGINS: 'http://127.0.0.1:3010', AUTH_MODE: 'local' },
    },
    {
      command: 'npm run dev -- --port 3010',
      url: 'http://127.0.0.1:3010',
      reuseExistingServer: false,
      env: { NEXT_PUBLIC_API_URL: 'http://127.0.0.1:8010/api/v1', NEXT_DIST_DIR: '.next/e2e' },
    },
  ],
});
