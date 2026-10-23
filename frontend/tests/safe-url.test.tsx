import { expect, test } from 'vitest';
import { safeReferenceUrl } from '../src/lib/safe-url';
test('saved links only allow explicit HTTP(S) without credentials', () => {
  for (const value of [
    'javascript:alert(1)',
    'data:text/html,hello',
    'file:///etc/passwd',
    '/relative',
    'https://user:secret@example.com',
    undefined,
  ])
    expect(safeReferenceUrl(value)).toBeUndefined();
  expect(safeReferenceUrl('https://example.com/source')).toBe('https://example.com/source');
});
