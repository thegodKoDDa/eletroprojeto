import { expect, test } from 'vitest';
import { duplicateEnvironment, removeProjectLoads } from '@/lib/environments';
import type { Environment, ProjectInput } from '@/lib/api';

test('removing loads clears only their circuit associations without mutating snapshots', () => {
  const input = {
    name: 'Casa',
    municipality: 'Cidade',
    environments: [
      {
        name: 'Sala',
        loads: [
          { id: 'a', name: 'A' },
          { id: 'b', name: 'B' },
        ],
      },
    ],
    circuits: [
      { id: 'one', load_ids: ['a', 'b'] },
      { id: 'two', load_ids: ['missing'] },
    ],
  } as unknown as ProjectInput;
  const original = structuredClone(input);
  const next = removeProjectLoads(input, ['a']);
  expect(next.environments?.[0].loads?.map((load) => load.id)).toEqual(['b']);
  expect(next.circuits?.map((circuit) => circuit.load_ids)).toEqual([['b'], ['missing']]);
  expect(input).toEqual(original);
});

test('copy renews instance identities and preserves independent manual data and snapshots', () => {
  const source = {
    id: 'room',
    name: 'Quarto',
    type: 'bedroom',
    area_m2: '12',
    perimeter_m: '14',
    lighting_points: 2,
    outlets: 5,
    loads: [
      {
        id: 'load',
        name: 'Lâmpada',
        quantity: 3,
        unit_power_w: '12',
        power_user_edited: true,
        manual_override: true,
        parameters: { usage_hours_per_day: '5' },
        catalog_reference: { id: 'catalog-original', reference_power_w: '9' },
      },
    ],
  } as Environment;
  const original = structuredClone(source);
  const copy = duplicateEnvironment(source, [source], 'copy');
  expect(copy.name).toBe('Quarto — cópia');
  expect(copy.id).toBe('copy');
  expect(copy.loads?.[0].id).not.toBe('load');
  expect(copy.loads?.[0]).toMatchObject({
    unit_power_w: '12',
    quantity: 3,
    power_user_edited: true,
    manual_override: true,
    catalog_reference: { id: 'catalog-original' },
  });
  copy.loads![0].parameters!.usage_hours_per_day = '8';
  copy.loads![0].catalog_reference!.reference_power_w = '20';
  expect(source).toEqual(original);
  expect(duplicateEnvironment(source, [source, copy], 'third').name).toBe('Quarto — cópia 2');
});

test('copy name fits the API limit even when repeated and empty rooms are supported', () => {
  const source = { id: 'a', name: 'A'.repeat(200), type: 'living' } as Environment;
  const first = duplicateEnvironment(source, [source], 'b');
  const second = duplicateEnvironment(source, [source, first], 'c');
  expect(first.name).toHaveLength(200);
  expect(second.name).toHaveLength(200);
  expect(second.name).not.toBe(first.name);
  expect(first.loads).toEqual([]);
});
