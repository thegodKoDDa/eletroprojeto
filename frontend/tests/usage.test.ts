import { expect, test } from 'vitest';
import { acceptsUsageRoutine, applyUsageRoutine } from '@/lib/usage';
import { restoreReference, newLoad } from '@/lib/equipment';
import type { Load, CatalogItem } from '@/lib/api';
import catalog from './fixtures/catalog.json';

test('bulk routine fills only empty usage and preserves manual zero, annual data and partial routines', () => {
  const loads = [
    { id: 'empty', parameters: {} },
    { id: 'monthly-zero', parameters: { monthly_energy_kwh: '0' } },
    { id: 'annual', parameters: { annual_energy_kwh: '100' } },
    { id: 'partial', parameters: { usage_days_per_month: 0 } },
    { id: 'minutes', parameters: { usage_minutes_per_day: '0' } },
  ] as Load[];
  const original = structuredClone(loads);
  expect(loads.filter(acceptsUsageRoutine).map((load) => load.id)).toEqual(['empty']);
  const updated = applyUsageRoutine(loads, {
    usage_time_unit: 'minutes',
    usage_minutes_per_day: '15',
    usage_hours_per_day: null,
    usage_days_per_month: 20,
  });
  expect(updated[0].parameters).toMatchObject({
    usage_minutes_per_day: '15',
    usage_days_per_month: 20,
  });
  expect(updated.slice(1)).toEqual(original.slice(1));
  expect(loads).toEqual(original);
});
test('restoring a technical reference preserves new annual consumption and minute routines', () => {
  const reference = catalog[0] as CatalogItem;
  const load = newLoad(reference);
  load.parameters = {
    ...load.parameters!,
    annual_energy_kwh: '80',
    usage_time_unit: 'minutes',
    usage_minutes_per_day: '10',
    usage_days_per_month: 30,
  };
  expect(restoreReference(load, reference).parameters).toMatchObject({
    annual_energy_kwh: '80',
    usage_time_unit: 'minutes',
    usage_minutes_per_day: '10',
    usage_days_per_month: 30,
  });
});
