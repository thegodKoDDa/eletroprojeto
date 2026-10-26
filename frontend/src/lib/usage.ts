import type { Load, TechnicalParameters } from './api';

/** A partial routine is intentional user data too; never replace it in bulk. */
export function acceptsUsageRoutine(load: Load) {
  const params = load.parameters;
  return (
    params?.monthly_energy_kwh == null &&
    params?.annual_energy_kwh == null &&
    params?.usage_hours_per_day == null &&
    params?.usage_minutes_per_day == null &&
    params?.usage_days_per_month == null
  );
}
export function applyUsageRoutine(
  loads: Load[],
  routine: Pick<
    TechnicalParameters,
    'usage_time_unit' | 'usage_hours_per_day' | 'usage_minutes_per_day' | 'usage_days_per_month'
  >,
) {
  return loads.map((load) =>
    acceptsUsageRoutine(load) ? { ...load, parameters: { ...load.parameters!, ...routine } } : load,
  );
}
