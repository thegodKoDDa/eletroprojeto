import { afterEach, expect, test, vi } from 'vitest';
import { request, requestReport } from '@/lib/api';
import { isBrowserRuntime } from '@/lib/browser-backend';
import type { components } from '@/lib/api.generated';

afterEach(() => {
  delete window.__ELETROPROJETO_BROWSER_DISPATCH__;
  window.localStorage.clear();
  vi.unstubAllGlobals();
});

test('detects GitHub Pages runtime and persists project store with backup', async () => {
  expect(isBrowserRuntime()).toBe(false);
  vi.stubGlobal('location', {
    protocol: 'https:',
    hostname: 'thegodkodda.github.io',
    pathname: '/eletroprojeto/',
  });
  expect(isBrowserRuntime()).toBe(true);

  window.__ELETROPROJETO_BROWSER_DISPATCH__ = (method, path, body, _headers, storeJson) => {
    if (method === 'POST' && path === '/projects') {
      const next = JSON.stringify({ saved: JSON.parse(body ?? '{}'), prev: storeJson });
      return {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
        body: { id: 'p1', version: 1 },
        body_base64: null,
        store_json: next,
      };
    }
    if (method === 'POST' && path === '/reports/pdf') {
      return {
        status: 200,
        headers: { 'Content-Type': 'application/pdf' },
        body: null,
        body_base64: btoa('%PDF-1.4 test'),
        store_json: null,
      };
    }
    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: { status: 'ok' },
      body_base64: null,
      store_json: null,
    };
  };

  const first = await request<{ id: string }>('/projects', {
    method: 'POST',
    body: JSON.stringify({ name: 'Casa 1' }),
  });
  expect(first.id).toBe('p1');
  expect(window.localStorage.getItem('eletroprojeto.browser.store.v1')).toContain('Casa 1');

  await request<{ id: string }>('/projects', {
    method: 'POST',
    body: JSON.stringify({ name: 'Casa 2' }),
  });
  expect(window.localStorage.getItem('eletroprojeto.browser.backup.v1')).toContain('Casa 1');
  expect(window.localStorage.getItem('eletroprojeto.browser.store.v1')).toContain('Casa 2');

  const blob = await requestReport('pdf', {} as components['schemas']['PDFExportInput']);
  expect(blob.type).toBe('application/pdf');
  expect(blob.size).toBe('%PDF-1.4 test'.length);
});
