import { afterEach, expect, test, vi } from 'vitest';
import { exportFilename } from '../src/lib/export';
import { requestReport } from '../src/lib/api';
import type { components } from '../src/lib/api.generated';

afterEach(() => vi.unstubAllGlobals());

test('filenames retain the project name and neutralize path characters', () => {
  expect(exportFilename('Residência São José', 'pdf')).toBe('Residência São José.pdf');
  expect(exportFilename('../Casa: A/B\\C', 'json')).toBe('_Casa_ A_B_C.json');
  expect(exportFilename(' ... ', 'pdf')).toBe('Projeto sem nome.pdf');
});

test('both exports send the same snapshot guards and reject unexpected document types', async () => {
  const body = {
    expected_input_digest: 'a'.repeat(64),
    expected_registry_version: 'b'.repeat(64),
    expected_engine_version: '0.6.0',
    project: { name: 'Casa' },
  } as components['schemas']['PDFExportInput'];
  const fetch = vi.fn(
    async (url: string) =>
      new Response('{}', {
        headers: { 'Content-Type': url.endsWith('json') ? 'application/json' : 'application/pdf' },
      }),
  );
  vi.stubGlobal('fetch', fetch);
  await requestReport('json', body);
  await requestReport('pdf', body);
  expect(fetch.mock.calls[0][0]).toMatch(/\/reports\/json$/);
  expect(fetch.mock.calls[1][0]).toMatch(/\/reports\/pdf$/);
  expect(
    JSON.parse(String((fetch.mock.calls[0] as unknown as [string, RequestInit])[1].body)),
  ).toEqual(body);
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('<html>', { headers: { 'Content-Type': 'text/html' } })),
  );
  await expect(requestReport('json', body)).rejects.toThrow('JSON válido');
});

test('export timezone keeps the actual Brasilia instant', async () => {
  const { formatDate } = await import('../src/lib/format');
  expect(formatDate('2026-10-22T01:30:00Z')).toContain('21/10/2026');
  expect(formatDate('2026-10-22T01:30:00Z')).toContain('22:30');
});
