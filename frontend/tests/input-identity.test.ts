import { expect, test } from 'vitest';
import { inputIdentity } from '@/lib/input-identity';

test('normalizes declared defaults and key order from the contract without guessing identities', () => {
  const small = {
    name: 'Casa',
    environments: [
      { id: 'room', name: 'Sala', loads: [{ id: 'load', name: 'Lâmpada', parameters: {} }] },
    ],
  };
  const normalized = {
    environments: [
      {
        loads: [
          {
            name: 'Lâmpada',
            id: 'load',
            unit_power_w: null,
            parameters: {
              power_mode: 'electrical',
              compressor: 'unknown',
              monthly_energy_kwh: null,
              usage_time_unit: null,
              assume_resistive: false,
            },
            quantity: 1,
          },
        ],
        bathroom_geometry: null,
        id: 'room',
        name: 'Sala',
        lighting_points: 0,
        outlets: 0,
      },
    ],
    name: 'Casa',
    notes: '',
  };
  expect(inputIdentity(small)).toBe(inputIdentity(normalized));
  expect(
    inputIdentity({ ...small, environments: [{ ...small.environments[0], id: 'different' }] }),
  ).not.toBe(inputIdentity(small));
});
test('zero, explicit null, invalid non-nullable null, unknown properties and array order remain distinct', () => {
  expect(inputIdentity({ name: 'A', energy_tariff_brl_per_kwh: '0' })).not.toBe(
    inputIdentity({ name: 'A', energy_tariff_brl_per_kwh: null }),
  );
  expect(inputIdentity({ name: 'A', floors: null })).not.toBe(inputIdentity({ name: 'A' }));
  expect(inputIdentity({ name: 'A', custom: 'x' })).not.toBe(inputIdentity({ name: 'A' }));
  expect(inputIdentity({ environments: [{ name: 'A' }, { name: 'B' }] })).not.toBe(
    inputIdentity({ environments: [{ name: 'B' }, { name: 'A' }] }),
  );
  expect(inputIdentity({ name: 'A', circuits: null })).not.toBe(
    inputIdentity({ name: 'A', circuits: [] }),
  );
});
