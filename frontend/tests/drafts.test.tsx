import { afterEach, expect, test, vi } from 'vitest';
import { DRAFT_PREFIX, draftKey, readDrafts, writeDraft } from '@/lib/drafts';
import type { ProjectInput } from '@/lib/api';

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});
const input: ProjectInput = {
  name: 'Casa recuperável',
  analysis_scope: 'installed',
  municipality: '',
  state: 'SP',
  utility: 'unconfirmed',
  residence_type: 'Casa',
  floors: 1,
  notes: '',
  built_area_m2: null,
  reference_voltage_v: null,
  environments: [],
};

test('independent tabs preserve drafts, manual data and null without changing the server', () => {
  const first = draftKey();
  const second = draftKey();
  expect(first).not.toBe(second);
  writeDraft(localStorage, first, { ...input, built_area_m2: null });
  writeDraft(localStorage, second, { ...input, name: 'Outra aba', notes: 'Manual 140 W' });
  const restored = readDrafts(localStorage);
  expect(restored).toHaveLength(2);
  expect(restored.find((item) => item.key === first)?.draft.input.built_area_m2).toBeNull();
  expect(restored.find((item) => item.key === second)?.draft.input.notes).toBe('Manual 140 W');
});

test('corrupt or unsupported drafts remain untouched and do not crash recovery', () => {
  localStorage.setItem(`${DRAFT_PREFIX}local:bad`, '{');
  localStorage.setItem(`${DRAFT_PREFIX}local:future`, JSON.stringify({ schema: 2 }));
  localStorage.setItem(`${DRAFT_PREFIX}local:shape`, JSON.stringify({ schema: 1, input: null }));
  expect(readDrafts(localStorage)).toEqual([]);
  expect(localStorage.length).toBe(3);
});

test('recovery only lists drafts in the authenticated account scope', () => {
  writeDraft(localStorage, draftKey('user:alice'), input);
  writeDraft(localStorage, draftKey('user:bob'), { ...input, name: 'Casa de Bob' });
  expect(readDrafts(localStorage)).toEqual([]);
  expect(readDrafts(localStorage, 'user:alice').map((item) => item.draft.input.name)).toEqual([
    'Casa recuperável',
  ]);
});

test('storage failures propagate so the editor can tell the user recovery is unavailable', () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
    throw new Error('Quota');
  });
  expect(() => writeDraft(localStorage, draftKey(), input)).toThrow('Quota');
});
