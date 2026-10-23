'use client';
import { SectionHeading } from '@/components/ui/SectionHeading';

import type { CalculationResult, Environment, Load, ProjectInput } from '@/lib/api';
import { format } from '@/lib/format';

const groups = [
  ['d1', 'Iluminação e tomadas de uso geral'],
  ['d2', 'Aquecimento de água (chuveiro, torneira, aquecedor)'],
  ['d3', 'Secadora, micro-ondas, lava-louças ou hidromassagem'],
  ['d4', 'Fogão ou forno elétrico'],
  ['d5', 'Ar-condicionado'],
  ['d6', 'Motores — fora do escopo atual'],
  ['d7', 'Solda transformador ou raios-X — fora do escopo atual'],
] as const;
type Settings = NonNullable<ProjectInput['energisa_demand']>;
type Group = (typeof groups)[number][0];
const defaults: Settings = { enabled: true, unit_type: 'unconfirmed', confirmed_absent_groups: [] };

type Props = {
  input: ProjectInput;
  result?: CalculationResult;
  onChange: (settings: Settings) => void;
  onLoadChange: (room: Environment, id: string, patch: Partial<Load>) => void;
};

export function DemandReview({ input, result, onChange, onLoadChange }: Props) {
  const settings = input.energisa_demand;
  const demand = result?.energisa_demand;
  function change(patch: Partial<Settings>) {
    onChange({ ...defaults, ...settings, ...patch });
  }
  return (
    <section className="panel demand-review" aria-label="Revisão da demanda Energisa">
      <SectionHeading
        eyebrow="REVISÃO / NDU-001"
        title="Demanda Energisa — revisão do inventário"
        description="Residência individual Energisa Sul-Sudeste/SP, até 75 kW, grupos d1–d5. Classifique as cargas e confirme o escopo; este estudo não dimensiona circuitos ou entrada."
      />
      <label className="mt-4 flex items-center gap-2">
        <input
          type="checkbox"
          checked={settings?.enabled ?? false}
          onChange={(event) => change({ enabled: event.target.checked })}
        />
        Estimar demanda com o inventário cadastrado
      </label>
      {settings?.enabled && (
        <>
          {(input.utility !== 'energisa_sul_sudeste' || input.state !== 'SP') && (
            <p role="status" className="mt-3">
              Distribuidora/UF fora do escopo deste método. A demanda ficará indisponível.
            </p>
          )}
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <label>
              Tipo de unidade para demanda
              <select
                value={settings.unit_type ?? 'unconfirmed'}
                onChange={(event) =>
                  change({ unit_type: event.target.value as Settings['unit_type'] })
                }
              >
                <option value="unconfirmed">Confirmar tipo de unidade</option>
                <option value="individual_residential">Residência individual</option>
                <option value="grouped">Unidades agrupadas — fora do escopo</option>
                <option value="non_residential">Não residencial — fora do escopo</option>
              </select>
            </label>
            <label>
              Há letreiros ou iluminação de vitrines?
              <select
                value={
                  settings.has_signage_or_display_lighting == null
                    ? ''
                    : String(settings.has_signage_or_display_lighting)
                }
                onChange={(event) =>
                  change({
                    has_signage_or_display_lighting:
                      event.target.value === '' ? null : event.target.value === 'true',
                  })
                }
              >
                <option value="">Confirmar presença ou ausência</option>
                <option value="false">Não</option>
                <option value="true">Sim — fora do escopo</option>
              </select>
            </label>
            <label>
              Iluminação/TUG em uso simultâneo?
              <select
                value={
                  settings.simultaneous_lighting_outlets == null
                    ? ''
                    : String(settings.simultaneous_lighting_outlets)
                }
                onChange={(event) =>
                  change({
                    simultaneous_lighting_outlets:
                      event.target.value === '' ? null : event.target.value === 'true',
                  })
                }
              >
                <option value="">Confirmar simultaneidade</option>
                <option value="false">Não</option>
                <option value="true">Sim</option>
              </select>
            </label>
          </div>
          <div className="mt-5 space-y-4">
            {(input.environments ?? []).flatMap((room) =>
              (room.loads ?? []).map((load) => {
                const classification = load.energisa_demand;
                function update(patch: Partial<NonNullable<Load['energisa_demand']>>) {
                  onLoadChange(room, load.id!, {
                    energisa_demand: {
                      reserve: false,
                      air_conditioning_type: 'unconfirmed',
                      ...classification,
                      ...patch,
                    },
                  });
                }
                return (
                  <fieldset className="demand-load" key={load.id}>
                    <legend>
                      {room.name} / {load.name}
                    </legend>
                    <p className="text-xs muted">
                      {load.quantity} unidade(s) · {format(load.unit_power_w)} W/unidade adotados
                    </p>
                    <div className="mt-2 grid gap-3 md:grid-cols-2">
                      <label>
                        Grupo NDU de {load.name}
                        <select
                          value={classification?.group ?? ''}
                          onChange={(event) =>
                            update({ group: (event.target.value || null) as Group | null })
                          }
                        >
                          <option value="">Classificar carga</option>
                          {groups.map(([key, name]) => (
                            <option key={key} value={key}>
                              {key} · {name}
                            </option>
                          ))}
                        </select>
                      </label>
                      {classification?.group === 'd5' && (
                        <label>
                          Tipo de ar-condicionado de {load.name}
                          <select
                            value={classification.air_conditioning_type ?? 'unconfirmed'}
                            onChange={(event) =>
                              update({
                                air_conditioning_type: event.target.value as NonNullable<
                                  Load['energisa_demand']
                                >['air_conditioning_type'],
                              })
                            }
                          >
                            <option value="unconfirmed">Confirmar enquadramento</option>
                            <option value="window_or_individual">
                              Janela ou central individual
                            </option>
                            <option value="central_unit">Unidade central — fora do escopo</option>
                          </select>
                        </label>
                      )}
                    </div>
                    <label className="mt-3 flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={classification?.reserve ?? false}
                        onChange={(event) => update({ reserve: event.target.checked })}
                      />
                      {load.name} é aparelho de reserva
                    </label>
                  </fieldset>
                );
              }),
            )}
          </div>
          <fieldset className="mt-5">
            <legend>Confirme somente os grupos sem cargas em operação</legend>
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {groups.map(([key, name]) => (
                <label key={key} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.confirmed_absent_groups?.includes(key) ?? false}
                    onChange={(event) =>
                      change({
                        confirmed_absent_groups: event.target.checked
                          ? [...new Set([...(settings.confirmed_absent_groups ?? []), key])]
                          : settings.confirmed_absent_groups?.filter((item) => item !== key),
                      })
                    }
                  />
                  Ausente: {key} · {name}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="mt-5 flex items-center gap-2">
            <input
              type="checkbox"
              disabled={!demand}
              checked={
                !!settings.reviewed_inventory_digest && (!demand || demand.inventory_reviewed)
              }
              onChange={(event) =>
                change({
                  reviewed_inventory_digest: event.target.checked ? demand?.inventory_digest : null,
                })
              }
            />
            Revisei todas as cargas, potências, quantidades, grupos, reservas e o escopo
          </label>
          <p className="mt-2 text-xs muted">
            Alterações no inventário ou escopo exigem nova revisão. Valores manuais são mantidos;
            classificação não é inferida pelo catálogo.
          </p>
          {demand && (
            <div className="mt-4" role="status">
              <p className="font-semibold">
                {demand.value != null
                  ? `Demanda estimada: ${format(demand.value)} kVA`
                  : demand.status === 'out_of_scope'
                    ? 'Demanda fora do escopo implementado'
                    : 'Demanda pendente de revisão'}
              </p>
              <ul className="mt-2 list-disc pl-5 text-sm">
                {demand.pending_checks.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
              {demand.groups.length > 0 && (
                <details className="mt-3">
                  <summary>Memória da demanda por grupo</summary>
                  {demand.groups.map((group) => (
                    <div key={group.group} className="mt-3 text-sm">
                      <p>
                        {group.group} · Tabela {group.table} · {group.quantity} unidade(s) ·
                        instalada {format(group.installed_power_w)} W · demandada{' '}
                        {format(group.demand_w)} W
                        {group.factor != null ? ` · fator ${format(group.factor)}` : ''}
                      </p>
                      {(group.bands ?? []).map((band, index) => (
                        <p key={index}>
                          Faixa {index + 1}: {format(band.installed_band_w)} W · fator{' '}
                          {format(band.factor)} · demanda {format(band.demand_w)} W
                        </p>
                      ))}
                      {group.reason && <p>{group.reason}</p>}
                    </div>
                  ))}
                </details>
              )}
              <p className="mt-3 text-xs muted">
                NDU-001 7.0, §9.1, Tabelas 5–8/10. Estimativa condicionada ao inventário declarado,
                sem aprovação pela concessionária.
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
