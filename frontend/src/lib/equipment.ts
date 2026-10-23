import type { CatalogItem, Load, TechnicalParameters } from './api';

export const technicalDefaults = (): TechnicalParameters => ({
  power_mode: 'electrical',
  compressor: 'unknown',
  mechanical_unit: 'cv',
  configuration: 'unknown',
  assume_resistive: false,
});

/** Copy a suggestion into a project; never mutate the catalog or its snapshot. */
export function applyReference(load: Load, reference: CatalogItem): Load {
  return {
    ...load,
    name: reference.selection_name ?? reference.name,
    category: reference.category,
    kind: reference.kind,
    equipment_type: reference.equipment_type,
    technology: reference.technology,
    brand: reference.brand ?? '',
    model: reference.model ?? '',
    unit_power_w: reference.reference_power_w ?? null,
    voltage_v: reference.voltage_v ?? null,
    power_factor: reference.power_factor ?? null,
    power_origin:
      reference.selection_name ||
      reference.power_rating === 'estimated' ||
      reference.reference_power_w == null
        ? 'user_estimate'
        : 'manufacturer',
    source: reference.source
      ? `${reference.source} · ${reference.document ?? ''}`
      : 'Informado pelo usuário',
    parameters: { ...technicalDefaults(), ...structuredClone(reference.parameters ?? {}) },
    catalog_reference: structuredClone(reference),
    manual_override: false,
    power_user_edited: false,
    demand_classification: null,
  };
}

/** Restoring technical suggestions must not erase the household's usage study. */
export function restoreReference(load: Load, reference: CatalogItem): Load {
  const restored = applyReference(load, reference);
  restored.parameters = {
    ...technicalDefaults(),
    ...restored.parameters,
    monthly_energy_kwh: load.parameters?.monthly_energy_kwh,
    usage_hours_per_day: load.parameters?.usage_hours_per_day,
    usage_days_per_month: load.parameters?.usage_days_per_month,
  };
  restored.manual_override = differsFromReference(restored, reference);
  return restored;
}

/** A source variant changes suggestions, keeping an explicitly adopted power. */
export function applyVariantReference(load: Load, reference: CatalogItem): Load {
  const updated = restoreReference(load, reference);
  const manualPower =
    load.power_user_edited ||
    load.power_origin === 'nameplate' ||
    (load.catalog_reference?.reference_power_w != null &&
      load.unit_power_w != null &&
      Number(load.unit_power_w) !== Number(load.catalog_reference.reference_power_w));
  if (manualPower && Number(load.unit_power_w) > 0) {
    updated.unit_power_w = load.unit_power_w;
    updated.power_user_edited = true;
    updated.power_origin = load.power_origin;
    updated.source = load.source;
  }
  updated.manual_override = differsFromReference(updated, reference);
  return updated;
}

/** Show common equipment names once; retain every source variant for old projects. */
export function selectionCatalog(catalog: CatalogItem[]): CatalogItem[] {
  const choices = new Map<string, CatalogItem>();
  for (const item of catalog) {
    const label = item.selection_name ?? item.name;
    if (!choices.has(label) || item.selection_default !== false) choices.set(label, item);
  }
  return [...choices.values()];
}

export function newLoad(reference?: CatalogItem): Load {
  const load: Load = {
    id: crypto.randomUUID(),
    name: 'Equipamento personalizado',
    category: 'Outros',
    equipment_type: 'custom',
    kind: 'specific_use',
    technology: '',
    brand: '',
    model: '',
    quantity: 1,
    unit_power_w: null,
    voltage_v: null,
    power_factor: null,
    power_origin: 'user_estimate',
    source: 'Informado pelo usuário',
    manual_override: false,
    power_user_edited: false,
    parameters: technicalDefaults(),
    demand_classification: null,
  };
  return reference ? applyReference(load, reference) : load;
}

/** Presentation-only comparison. The backend independently validates provenance. */
export function differsFromReference(load: Load, reference: CatalogItem): boolean {
  function equivalent(a: unknown, b: unknown) {
    if (a === b || (a == null && b == null)) return true;
    if (a == null || b == null || typeof a === 'boolean' || typeof b === 'boolean') return false;
    return Number.isFinite(Number(a)) && Number.isFinite(Number(b)) && Number(a) === Number(b);
  }
  if (
    load.equipment_type !== reference.equipment_type ||
    load.kind !== reference.kind ||
    load.category !== reference.category ||
    load.technology !== reference.technology ||
    load.brand !== (reference.brand ?? '') ||
    load.model !== (reference.model ?? '')
  )
    return true;
  if (
    !equivalent(load.unit_power_w, reference.reference_power_w) ||
    !equivalent(load.voltage_v, reference.voltage_v) ||
    !equivalent(load.power_factor, reference.power_factor)
  )
    return true;
  const used = { ...technicalDefaults(), ...load.parameters };
  const original = { ...technicalDefaults(), ...reference.parameters };
  return [...new Set([...Object.keys(used), ...Object.keys(original)])].some(
    (key) =>
      !equivalent(
        used[key as keyof TechnicalParameters],
        original[key as keyof TechnicalParameters],
      ),
  );
}
