import { defineConfig } from '@playwright/test';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const directory = mkdtempSync(join(tmpdir(), 'eletroprojeto-auth-e2e-'));
const cert = join(directory, 'cert.pem');
const key = join(directory, 'key.pem');
const certificate = spawnSync(
  'openssl',
  [
    'req',
    '-x509',
    '-newkey',
    'rsa:2048',
    '-nodes',
    '-days',
    '1',
    '-keyout',
    key,
    '-out',
    cert,
    '-subj',
    '/CN=127.0.0.1',
    '-addext',
    'subjectAltName=IP:127.0.0.1',
  ],
  { encoding: 'utf8' },
);
if (certificate.status !== 0)
  throw new Error('Não foi possível gerar certificado de QA temporário.');
export default defineConfig({
  testDir: './tests/e2e-auth',
  use: { baseURL: 'https://127.0.0.1:3011', ignoreHTTPSErrors: true, trace: 'retain-on-failure' },
  webServer: [
    {
      command: 'node scripts/e2e-api.mjs',
      url: 'https://127.0.0.1:8010/api/v1/health',
      ignoreHTTPSErrors: true,
      reuseExistingServer: false,
      env: {
        DATABASE_URL: `sqlite:///${join(directory, 'qa.db').replaceAll('\\', '/')}`,
        AUTH_MODE: 'remote',
        CORS_ORIGINS: 'https://127.0.0.1:3011',
        ELETROPROJETO_QA_ACCOUNTS: '1',
        QA_TLS_CERT: cert,
        QA_TLS_KEY: key,
      },
    },
    {
      command: `npm run dev -- --port 3011 --experimental-https --experimental-https-key "${key}" --experimental-https-cert "${cert}"`,
      url: 'https://127.0.0.1:3011',
      ignoreHTTPSErrors: true,
      reuseExistingServer: false,
      env: {
        NEXT_PUBLIC_API_URL: 'https://127.0.0.1:8010/api/v1',
        NEXT_PUBLIC_AUTH_MODE: 'remote',
        NEXT_DIST_DIR: '.next/e2e-auth',
      },
    },
  ],
});
