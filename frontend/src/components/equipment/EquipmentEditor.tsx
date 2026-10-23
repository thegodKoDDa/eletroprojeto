'use client';
import { EnergyFields } from './EnergyFields';
import { safeReferenceUrl } from '@/lib/safe-url';
import { useContext } from 'react';
import { CalculationScopeContext, Field } from '@/components/ui/Field';
import type { CatalogItem, Load, TechnicalParameters, CalculationMemory } from '@/lib/api';
import {
  applyReference,
  technicalDefaults,
  differsFromReference,
  selectionCatalog,
  applyVariantReference,
  restoreReference,
} from '@/lib/equipment';

type Props = {
  load: Load;
  catalog: CatalogItem[];
  onChange: (patch: Partial<Load>) => void;
  onRemove: () => void;
  onDuplicate: () => void;
  memory?: CalculationMemory;
  stale?: boolean;
};
const types: Record<Load['equipment_type'], string> = {
  lighting: 'Iluminação',
  air_conditioner: 'Ar-condicionado',
  shower: 'Chuveiro',
  refrigeration: 'Geladeira / freezer',
  motor: 'Motor / bomba',
  microwave: 'Micro-ondas',
  television: 'Televisor',
  appliance: 'Eletrodoméstico',
  custom: 'Personalizado',
};
const rating = {
  nominal: 'Nominal do modelo',
  maximum: 'Máxima do modelo',
  estimated: 'Estimativa genérica',
  unknown: 'Potência desconhecida',
};

export function EquipmentEditor({
  load,
  catalog,
  onChange,
  onRemove,
  onDuplicate,
  memory,
  stale = false,
}: Props) {
  const scope = useContext(CalculationScopeContext);
  const params = { ...technicalDefaults(), ...load.parameters };
  const ref = load.catalog_reference;
  const sourceUrl = safeReferenceUrl(ref?.source_url);
  const options = selectionCatalog(catalog);
  const variants = ref
    ? catalog.filter(
        (item) =>
          item.equipment_type === ref.equipment_type &&
          (item.selection_name ?? item.name) === (ref.selection_name ?? ref.name),
      )
    : [];
  const selectedId = ref?.equipment_type === load.equipment_type ? ref.id : '';
  const currentLabel =
    (selectedId
      ? (catalog.find((item) => item.id === selectedId)?.selection_name ?? ref?.selection_name)
      : undefined) ?? load.name;
  const missingFp =
    !(Number(load.power_factor) > 0 && Number(load.power_factor) <= 1) && !params.assume_resistive;
  const missingCurrent =
    missingFp || !(Number(load.voltage_v) > 0) || params.configuration === 'unknown';
  function edit(patch: Partial<Load>, manual = true) {
    const changes = {
      ...patch,
      ...(Object.hasOwn(patch, 'unit_power_w')
        ? {
            ...(manual ? { power_user_edited: true } : {}),
            power_origin: patch.power_origin ?? ('user_estimate' as const),
            source: patch.source ?? 'Potência substituída manualmente pelo usuário',
          }
        : {}),
    };
    const updated = { ...load, ...changes };
    onChange({ ...changes, manual_override: ref ? differsFromReference(updated, ref) : false });
  }
  function technical(patch: Partial<TechnicalParameters>) {
    // A capacity suggestion must come from an actual matching catalog entry.
    const manualPower =
      load.power_user_edited ||
      load.power_origin === 'nameplate' ||
      (ref &&
        load.unit_power_w != null &&
        Number(load.unit_power_w) !== Number(ref.reference_power_w));
    const nextParams = { ...params, ...patch };
    const acIdentityChanged =
      load.equipment_type === 'air_conditioner' &&
      Object.keys(patch).some((key) =>
        ['cooling_capacity_btu_h', 'compressor', 'ac_type'].includes(key),
      );
    if (acIdentityChanged && nextParams.cooling_capacity_btu_h != null && !manualPower) {
      const match = catalog.find(
        (item) =>
          item.equipment_type === 'air_conditioner' &&
          item.parameters?.cooling_capacity_btu_h != null &&
          Number(item.parameters.cooling_capacity_btu_h) ===
            Number(nextParams.cooling_capacity_btu_h) &&
          (!nextParams.ac_type || item.parameters.ac_type === nextParams.ac_type) &&
          (nextParams.compressor === 'unknown' ||
            item.parameters.compressor === nextParams.compressor),
      );
      if (match) {
        const suggestion = applyReference(load, match);
        const editedVoltage = ref && Number(load.voltage_v) !== Number(ref.voltage_v);
        const editedFp = ref && Number(load.power_factor) !== Number(ref.power_factor);
        const editedName = ref && load.name !== (ref.selection_name ?? ref.name);
        const editedCategory = ref && load.category !== ref.category;
        const manualCurrents = Object.fromEntries(
          (['nameplate_current_a', 'maximum_current_a'] as const)
            .filter(
              (key) =>
                params[key] != null && String(params[key]) !== String(ref?.parameters?.[key] ?? ''),
            )
            .map((key) => [key, params[key]]),
        );
        const updated: Load = {
          ...suggestion,
          ...(editedName ? { name: load.name } : {}),
          ...(editedCategory ? { category: load.category } : {}),
          demand_classification: load.demand_classification,
          ...(editedVoltage ? { voltage_v: load.voltage_v } : {}),
          ...(editedFp ? { power_factor: load.power_factor } : {}),
          parameters: {
            ...suggestion.parameters!,
            ...manualCurrents,
            configuration: params.configuration,
            assume_resistive: params.assume_resistive,
            usage_hours_per_day: params.usage_hours_per_day,
            usage_days_per_month: params.usage_days_per_month,
            monthly_energy_kwh: params.monthly_energy_kwh,
          },
        };
        onChange({ ...updated, manual_override: differsFromReference(updated, match) });
        return;
      }
    }
    // No thermal-to-electrical formula or extrapolation lives in this component.
    const identityChanged = Object.keys(patch).some((key) =>
      ['cooling_capacity_btu_h', 'compressor', 'ac_type', 'screen_inches'].includes(key),
    );
    const manualFp =
      load.power_factor != null &&
      (!ref || ref.power_factor == null || Number(load.power_factor) !== Number(ref.power_factor));
    edit(
      {
        parameters: { ...params, ...patch },
        ...(identityChanged && ref ? { power_factor: manualFp ? load.power_factor : null } : {}),
        ...(patch.power_mode === 'mechanical'
          ? {
              unit_power_w: null,
              power_origin: 'user_estimate',
              source:
                'Entrada elétrica calculada a partir da potência mecânica e do rendimento informados',
            }
          : {}),
        ...(identityChanged && ref && !manualPower
          ? {
              unit_power_w: null,
              power_origin: 'user_estimate',
              model: '',
              source: 'Características alteradas; potência elétrica requer confirmação',
            }
          : {}),
      },
      false,
    );
  }
  const specific = load.equipment_type;
  return (
    <div className="equipment-card" data-testid="equipment-editor">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6" data-testid="equipment-essential">
        <label className="sm:col-span-2">
          Equipamento
          <select
            value={selectedId}
            onChange={(e) => {
              const item = catalog.find((item) => item.id === e.target.value);
              if (item) onChange(applyReference(load, item));
            }}
          >
            {!options.some((item) => item.id === selectedId) && (
              <option value={selectedId}>
                {currentLabel}
                {selectedId ? ' · cadastrado' : ''}
              </option>
            )}
            {options.map((item) => (
              <option key={item.id} value={item.id}>
                {item.selection_name ?? item.name}
              </option>
            ))}
          </select>
        </label>
        {specific === 'custom' && (
          <Field
            field="load.name"
            label="Descrição"
            path={`load.${load.id}.name`}
            parameters={params}
            className="sm:col-span-2"
          >
            <input value={load.name} onChange={(e) => edit({ name: e.target.value })} />
          </Field>
        )}
        <Field
          field="load.quantity"
          label="Quantidade"
          path={`load.${load.id}.quantity`}
          parameters={params}
        >
          <input
            type="number"
            min="1"
            step="1"
            value={Number.isNaN(load.quantity) ? '' : load.quantity}
            onChange={(e) =>
              edit({ quantity: e.target.value === '' ? NaN : Number(e.target.value) })
            }
          />
        </Field>
        {params.power_mode === 'mechanical' ? (
          <Field
            field="load.parameters.mechanical_power"
            label="Potência mecânica de saída"
            path={`load.${load.id}.parameters.mechanical_power`}
            parameters={params}
          >
            <input
              type="number"
              min="0.000001"
              step="any"
              value={params.mechanical_power ?? ''}
              onChange={(e) => technical({ mechanical_power: e.target.value || null })}
            />
          </Field>
        ) : (
          <Field
            field="load.unit_power_w"
            label="Potência unitária (W)"
            path={`load.${load.id}.unit_power_w`}
            parameters={params}
          >
            <input
              type="number"
              min="0.000001"
              step="any"
              placeholder="Desconhecida"
              value={load.unit_power_w ?? ''}
              onChange={(e) => edit({ unit_power_w: e.target.value || null })}
            />
          </Field>
        )}
        {scope === 'current' && (
          <>
            <Field
              field="load.voltage_v"
              label="Tensão nominal (V)"
              path={`load.${load.id}.voltage_v`}
              parameters={params}
            >
              <input
                type="number"
                min="1"
                step="any"
                placeholder="Desconhecida"
                value={load.voltage_v ?? ''}
                onChange={(e) => edit({ voltage_v: e.target.value || null })}
              />
            </Field>
          </>
        )}

        {specific === 'air_conditioner' && (
          <>
            <Field
              field="load.parameters.cooling_capacity_btu_h"
              label="Capacidade térmica (BTU/h)"
              path={`load.${load.id}.parameters.cooling_capacity_btu_h`}
              parameters={params}
            >
              <input
                id={`load.${load.id}.parameters.cooling_capacity_btu_h`}
                list={`btu-${load.id}`}
                type="number"
                min="1"
                step="any"
                value={params.cooling_capacity_btu_h ?? ''}
                onChange={(e) => technical({ cooling_capacity_btu_h: e.target.value || null })}
              />
              <datalist id={`btu-${load.id}`}>
                {[7000, 9000, 12000, 18000, 24000, 30000, 36000].map((value) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
            </Field>
          </>
        )}
        {specific === 'motor' && (
          <>
            <label>
              Unidade da potência
              <select
                value={params.power_mode === 'electrical' ? 'W' : params.mechanical_unit}
                onChange={(e) =>
                  technical(
                    e.target.value === 'W'
                      ? { power_mode: 'electrical' }
                      : {
                          power_mode: 'mechanical',
                          mechanical_unit: e.target.value as 'cv' | 'hp',
                        },
                  )
                }
              >
                <option value="W">W · entrada elétrica</option>
                <option value="cv">cv · saída mecânica</option>
                <option value="hp">HP · saída mecânica</option>
              </select>
            </label>
            {params.power_mode === 'mechanical' && (
              <Field
                field="load.parameters.efficiency"
                label="Rendimento do motor (0 a 1)"
                path={`load.${load.id}.parameters.efficiency`}
                parameters={params}
              >
                <input
                  type="number"
                  min="0.000001"
                  max="1"
                  step="any"
                  placeholder="Obrigatório"
                  value={params.efficiency ?? ''}
                  onChange={(e) => technical({ efficiency: e.target.value || null })}
                />
              </Field>
            )}
          </>
        )}
      </div>
      {ref?.id === 'enel-computer' && (
        <p className="mt-2 text-xs muted">
          Informe a potência elétrica adotada. A capacidade da fonte do computador não é
          necessariamente seu consumo.
        </p>
      )}
      <details className="mt-3" data-testid="equipment-advanced">
        <summary className="cursor-pointer text-xs muted">
          Configurações avançadas
          {!load.name.trim() || !load.category?.trim() || !load.source?.trim()
            ? ' · identificação/fonte pendente'
            : ''}
          {['apparent', 'current'].includes(scope) && missingFp
            ? ' · FP necessário para o cálculo selecionado'
            : scope === 'current' && missingCurrent
              ? ' · dados necessários para corrente'
              : ''}
        </summary>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {variants.length > 1 && (
            <label className="sm:col-span-2">
              Variante de referência
              <select
                aria-label="Variante de referência"
                value={ref?.id ?? ''}
                onChange={(event) => {
                  const variant = variants.find((item) => item.id === event.target.value);
                  if (variant) onChange(applyVariantReference(load, variant));
                }}
              >
                {!variants.some((item) => item.id === ref?.id) && (
                  <option value={ref?.id}>Referência salva</option>
                )}
                {variants.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} · {item.reference_power_w ?? '—'} W
                    {item.voltage_v ? ` · ${item.voltage_v} V` : ''}
                  </option>
                ))}
              </select>
              <span className="mt-1 block text-xs muted">
                A variante atualiza as sugestões técnicas. Potência editada manualmente e dados de
                consumo são preservados.
              </span>
            </label>
          )}
          {scope !== 'current' && (
            <>
              <Field
                field="load.voltage_v"
                label="Tensão nominal (V)"
                path={`load.${load.id}.voltage_v`}
                parameters={params}
              >
                <input
                  type="number"
                  min="1"
                  step="any"
                  placeholder="Desconhecida"
                  value={load.voltage_v ?? ''}
                  onChange={(e) => edit({ voltage_v: e.target.value || null })}
                />
              </Field>
            </>
          )}
          <Field
            field="load.power_factor"
            label="Fator de potência"
            path={`load.${load.id}.power_factor`}
            parameters={params}
          >
            <input
              type="number"
              min="0.000001"
              max="1"
              step="any"
              placeholder="Desconhecido"
              value={load.power_factor ?? ''}
              onChange={(e) =>
                edit({
                  power_factor: e.target.value || null,
                  parameters: { ...params, assume_resistive: false },
                })
              }
            />
          </Field>
          <label>
            Tipo de equipamento
            <select
              value={specific}
              onChange={(e) =>
                edit({
                  equipment_type: e.target.value as Load['equipment_type'],
                  name: types[e.target.value as Load['equipment_type']],
                  kind:
                    e.target.value === 'lighting'
                      ? 'lighting'
                      : load.kind === 'lighting'
                        ? 'specific_use'
                        : load.kind,
                  unit_power_w: null,
                  power_factor: null,
                  power_origin: 'user_estimate',
                  model: '',
                  power_user_edited: false,
                  source: 'Tipo alterado; parâmetros precisam ser confirmados',
                  parameters: technicalDefaults(),
                })
              }
            >
              {Object.entries(types).map(([value, text]) => (
                <option key={value} value={value}>
                  {text}
                </option>
              ))}
            </select>
          </label>
          <label>
            Natureza
            <select
              disabled={specific === 'lighting'}
              value={load.kind}
              onChange={(e) => edit({ kind: e.target.value as Load['kind'] })}
            >
              {(specific === 'lighting' || load.kind === 'lighting') && (
                <option value="lighting">Iluminação</option>
              )}
              <option value="general_use">Uso geral</option>
              <option value="specific_use">Uso específico</option>
            </select>
          </label>
          <label>
            Origem da potência
            <select
              value={load.power_origin}
              onChange={(e) => edit({ power_origin: e.target.value as Load['power_origin'] })}
            >
              <option value="user_estimate">Estimativa do usuário</option>
              <option value="nameplate">Placa do equipamento</option>
              <option value="manufacturer">Fabricante</option>
            </select>
          </label>
          {specific !== 'custom' && (
            <Field
              field="load.name"
              label="Identificação da carga"
              path={`load.${load.id}.name`}
              parameters={params}
              className="sm:col-span-2"
            >
              <input value={load.name} onChange={(e) => edit({ name: e.target.value })} />
            </Field>
          )}
          <Field
            field="load.category"
            label="Categoria"
            path={`load.${load.id}.category`}
            parameters={params}
          >
            <input value={load.category} onChange={(e) => edit({ category: e.target.value })} />
          </Field>
          <Field
            field="load.source"
            label="Fonte técnica"
            path={`load.${load.id}.source`}
            parameters={params}
            className="sm:col-span-2"
          >
            <input value={load.source} onChange={(e) => edit({ source: e.target.value })} />
          </Field>
          {specific === 'lighting' ? (
            <label>
              Tecnologia da lâmpada
              <select
                value={load.technology}
                onChange={(e) =>
                  edit({
                    technology: e.target.value,
                    unit_power_w: null,
                    power_factor: null,
                    power_origin: 'user_estimate',
                    source: 'Tecnologia alterada; selecione uma referência ou informe a placa',
                  })
                }
              >
                <option value="">Não informada</option>
                {['LED', 'Incandescente', 'Fluorescente', 'Halógena', 'Outra'].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
          ) : null}
          {specific === 'air_conditioner' && (
            <>
              <label>
                Tipo de ar-condicionado
                <select
                  value={params.ac_type ?? ''}
                  onChange={(e) =>
                    technical({
                      ac_type: (e.target.value as TechnicalParameters['ac_type']) || null,
                    })
                  }
                >
                  <option value="">Não informado</option>
                  <option value="split">Split</option>
                  <option value="window">Janela</option>
                  <option value="portable">Portátil</option>
                  <option value="other">Outro</option>
                </select>
              </label>
              <label>
                Compressor
                <select
                  value={params.compressor}
                  onChange={(e) =>
                    technical({ compressor: e.target.value as TechnicalParameters['compressor'] })
                  }
                >
                  <option value="unknown">Desconhecido</option>
                  <option value="inverter">Inverter</option>
                  <option value="conventional">Convencional</option>
                </select>
              </label>
            </>
          )}
          <Field
            field="load.parameters.configuration"
            label="Configuração para corrente"
            path={`load.${load.id}.parameters.configuration`}
            parameters={params}
          >
            <select
              value={params.configuration}
              onChange={(e) =>
                technical({ configuration: e.target.value as TechnicalParameters['configuration'] })
              }
            >
              <option value="unknown">Não informada</option>
              <option value="single_phase">Monofásica · tensão nos terminais</option>
              <option value="balanced_three_phase">Trifásica equilibrada · tensão de linha</option>
            </select>
          </Field>
          {(specific === 'shower' ||
            (specific === 'appliance' && load.category === 'Aquecimento de água') ||
            (specific === 'lighting' &&
              ['Incandescente', 'Halógena'].includes(load.technology))) && (
            <label className="self-center">
              <input
                className="mr-2 !w-auto"
                type="checkbox"
                checked={params.assume_resistive}
                onChange={(e) =>
                  edit({
                    parameters: { ...params, assume_resistive: e.target.checked },
                    ...(e.target.checked ? { power_factor: null } : {}),
                  })
                }
              />
              Adotar hipótese de carga resistiva (FP=1)
            </label>
          )}
        </div>
      </details>
      <EnergyFields load={load} onChange={technical} />
      <div className="mt-3 flex flex-wrap items-start gap-x-4 gap-y-2 text-xs muted">
        <details className="min-w-0 flex-1" data-testid="equipment-reference">
          <summary className="cursor-pointer">
            {ref ? 'Valor de referência' : 'Origem dos dados'}
            {load.power_origin === 'user_estimate' ? ' · estimado' : ''}
            {load.manual_override ? ' · editado' : ''}
          </summary>
          <div className="mt-2 space-y-1 break-words leading-5">
            {ref && (
              <>
                <p>
                  {ref.selection_name && ref.brand
                    ? 'Referência de categoria baseada em um modelo documentado; não é potência universal.'
                    : rating[ref.power_rating]}
                </p>
                <p>
                  {ref.name} · {ref.reference_power_w ?? '—'} W
                  {ref.voltage_range ? ` · ${ref.voltage_range}` : ''}
                </p>
                <p>{ref.note}</p>
                {sourceUrl && (
                  <a
                    className="text-emerald-300 underline"
                    href={sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {ref.source} · {ref.document} · consulta {ref.verified_on}
                  </a>
                )}
              </>
            )}
            {(load.brand || load.model) && (
              <p>Dados salvos: {[load.brand, load.model].filter(Boolean).join(' · ')}</p>
            )}
            <p>Fonte utilizada: {load.source}</p>
            {(
              [
                ['screen_inches', 'Tela (polegadas)'],
                ['maximum_power_w', 'Potência máxima (W)'],
                ['microwave_output_w', 'Saída de aquecimento (W)'],
                ['nameplate_current_a', 'Corrente nominal de placa (A)'],
                ['starting_current_a', 'Corrente de partida (A)'],
                ['maximum_current_a', 'Corrente máxima (A)'],
              ] as const
            ).map(([key, label]) =>
              params[key] != null ? (
                <p key={key}>
                  {label}: {params[key]} · dado informativo preservado
                </p>
              ) : null,
            )}
          </div>
        </details>
        {ref && (
          <button
            className="hover:text-emerald-300"
            aria-label="Restaurar sugestão"
            onClick={() => onChange(restoreReference(load, ref))}
          >
            Restaurar
          </button>
        )}
        <button
          className="hover:text-emerald-300"
          aria-label="Duplicar equipamento"
          onClick={onDuplicate}
        >
          Duplicar
        </button>
        <button
          className="hover:text-red-300"
          aria-label="Remover carga"
          onClick={() => {
            if (window.confirm(`Remover ${load.name}?`)) onRemove();
          }}
        >
          Remover
        </button>
        <span className="text-emerald-300" data-stale={stale}>
          {memory && memory.status !== 'pending'
            ? `${stale ? 'Último total' : 'Total'}: ${Number(memory.result.value).toLocaleString('pt-BR', { maximumFractionDigits: 3 })} W`
            : 'Total pendente'}
        </span>
      </div>
    </div>
  );
}
