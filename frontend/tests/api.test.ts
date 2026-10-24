import { afterEach, expect, test, vi } from 'vitest';
import { APIError, request, requestReport, setSessionCsrf } from '@/lib/api';
import type { components } from '@/lib/api.generated';

afterEach(() => {
  vi.unstubAllGlobals();
  setSessionCsrf();
});

test.each<{ headers: HeadersInit }>([
  { headers: new Headers({ 'Idempotency-Key': 'key' }) },
  { headers: [['Idempotency-Key', 'key']] },
])('preserves supported header formats alongside CSRF', async ({ headers }) => {
  const fetch = vi.fn().mockResolvedValue(new Response('{}'));
  vi.stubGlobal('fetch', fetch);
  setSessionCsrf('csrf');
  await request('/projects', { method: 'POST', body: '{}', headers });
  const sent = new Headers(fetch.mock.calls[0][1].headers);
  expect(sent.get('Idempotency-Key')).toBe('key');
  expect(sent.get('X-CSRF-Token')).toBe('csrf');
  expect(sent.get('Content-Type')).toBe('application/json');
});

test('report validation exposes the same actionable API errors as forms', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [{ loc: ['body', 'project', 'name'], msg: 'Campo inválido' }],
          notifications: [],
        }),
        { status: 422 },
      ),
    ),
  );
  await expect(
    requestReport('pdf', {} as components['schemas']['PDFExportInput']),
  ).rejects.toMatchObject({ status: 422, message: 'project.name: Campo inválido' });
});

test('malformed gateway errors keep the HTTP status and a useful fallback', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ detail: [null, {}] }), { status: 502 })),
  );
  await expect(request('/health')).rejects.toBeInstanceOf(APIError);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Bad gateway', { status: 502 })));
  await expect(request('/health')).rejects.toMatchObject({
    status: 502,
    message: 'Falha na API (502)',
  });
});
