import { expect, test } from 'vitest';
import { estimateJourney, energyCompletionTarget } from '@/lib/journey';
import type { CalculationResult, ProjectInput } from '@/lib/api';
import fixture from './fixtures/result.json';
import requirements from './fixtures/requirements.json';
const project = (): ProjectInput =>
  ({
    name: 'Minha casa',
    municipality: 'Cidade',
    state: 'SP',
    environments: [
      {
        id: 'room',
        name: 'Sala',
        loads: [{ id: 'lamp', name: 'Lâmpada', quantity: 1, unit_power_w: '9', parameters: {} }],
      },
    ],
  }) as ProjectInput;
const result = (): CalculationResult =>
  ({
    ...fixture,
    input_digest: 'current',
    monthly_energy: { value: '0', unit: 'kWh', status: 'estimated' },
    energy_unknown_load_ids: [],
  }) as unknown as CalculationResult;

test('completion follows current server output, accepts zero and does not require a tariff or normative approval', () => {
  const input = project();
  expect(estimateJourney(input, result(), undefined, false).map((s) => s.complete)).toEqual([
    true,
    true,
    true,
    false,
    false,
  ]);
  expect(estimateJourney(input, result(), 'current', true).every((s) => s.complete)).toBe(true);
  expect(input.energy_tariff_brl_per_kwh).toBeUndefined();
});
test('stale, pending and changed results reopen consumption and review; saving does not confer approval', () => {
  const input = project();
  expect(estimateJourney(input, undefined, 'current', true).map((s) => s.complete)).toEqual([
    true,
    true,
    false,
    false,
    true,
  ]);
  expect(
    estimateJourney(input, { ...result(), energy_unknown_load_ids: ['lamp'] }, 'current', false)[2]
      .complete,
  ).toBe(false);
  expect(
    estimateJourney(input, { ...result(), monthly_energy: null }, 'current', false)[2].complete,
  ).toBe(false);
  expect(
    estimateJourney(input, { ...result(), input_digest: 'new' }, 'current', true)[3].complete,
  ).toBe(false);
});
test('blank and overlong names do not complete identification or inventory; empty inventory is never complete', () => {
  const input = project();
  input.name = ' '.repeat(3);
  expect(estimateJourney(input, result(), undefined, false, requirements)[0]).toMatchObject({
    complete: false,
    target: 'project.name',
  });
  input.name = 'x'.repeat(201);
  expect(estimateJourney(input, result(), undefined, false, requirements)[0].complete).toBe(false);
  input.environments![0].name = '';
  expect(estimateJourney(input, result(), undefined, false, requirements)[1]).toMatchObject({
    complete: false,
    target: 'room.room.name',
  });
  input.environments = [];
  expect(estimateJourney(input, result(), undefined, false)[1].complete).toBe(false);
});
test('help advances to the next pending appliance and missing field without modifying manual inputs', () => {
  const input = project();
  const original = structuredClone(input);
  expect(energyCompletionTarget(input, undefined)).toBe('load.lamp.parameters.usage_hours_per_day');
  expect(
    energyCompletionTarget(input, {
      ...result(),
      unknown_load_ids: ['lamp'],
      energy_unknown_load_ids: ['lamp'],
    }),
  ).toBe('load.lamp.unit_power_w');
  input.environments![0].loads![0].parameters = {
    ...input.environments![0].loads![0].parameters!,
    usage_hours_per_day: '0',
  };
  expect(energyCompletionTarget(input, { ...result(), energy_unknown_load_ids: ['lamp'] })).toBe(
    'load.lamp.parameters.usage_days_per_month',
  );
  expect(original.environments![0].loads![0].parameters).toEqual({});
  expect(energyCompletionTarget({ ...input, environments: [] }, undefined)).toBe('add-environment');
});
