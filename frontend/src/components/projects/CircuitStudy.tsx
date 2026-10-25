'use client';
import { useId, useState } from 'react';
import type { components } from '@/lib/api.generated';
import type { ProjectInput, CalculationResult } from '@/lib/api';
import { safeReferenceUrl } from '@/lib/safe-url';
import { format } from '@/lib/format';
import { SectionHeading } from '@/components/ui/SectionHeading';

type Circuit = components['schemas']['CircuitInput'];
type Entry = components['schemas']['ServiceEntryInput'];
function Numeric({
  label,
  value,
  onChange,
}: {
  label: string;
  value?: string | number | null;
  onChange: (value: string | null) => void;
}) {
  return (
    <label>
      {label}
      <input
        type="number"
        step="any"
        min="0"
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value || null)}
      />
    </label>
  );
}
function Ratings({
  value,
  onChange,
}: {
  value: (number | string)[];
  onChange: (value: (number | string)[]) => void;
}) {
  const errorId = useId();
  const signature = JSON.stringify(value);
  const [draft, setDraft] = useState({ signature, text: value.join('; ') });
  const text = draft.signature === signature ? draft.text : value.join('; ');
  const parts = text
    .split(';')
    .map((part) => part.trim())
    .filter(Boolean);
  const valid = (part: string) =>
    /^\+?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:e[+-]?\d+)?$/i.test(part) &&
    Number.isFinite(Number(part.replace(',', '.'))) &&
    Number(part.replace(',', '.')) > 0;
  const invalid = parts.some((part) => !valid(part));
  return (
    <label>
      Correntes nominais disponíveis (A; separe por ;)
      <input
        value={text}
        aria-invalid={invalid || undefined}
        aria-describedby={invalid ? errorId : undefined}
        placeholder="Valores dos produtos consultados"
        onChange={(event) => {
          const raw = event.target.value;
          const items = raw
            .split(';')
            .map((part) => part.trim())
            .filter(Boolean);
          const ratings = items.every(valid) ? items.map((item) => item.replace(',', '.')) : [];
          setDraft({ signature: JSON.stringify(ratings), text: raw });
          onChange(ratings);
        }}
      />
      {invalid && (
        <span id={errorId} className="field-error">
          Use correntes positivas separadas por ponto e vírgula.
        </span>
      )}
    </label>
  );
}
type Protection = components['schemas']['CircuitProtectionInput'];
const protectionFields = [
  ['device_rated_a', 'In do disjuntor dos dados consultados (A)'],
  ['cable_k', 'Coeficiente k do cabo (A·√s/mm²)'],
  ['let_through_a2s', 'Energia passante máxima I²t (A²s)'],
  ['short_duration_s', 'Duração do curto (s; até5s)'],
  ['phase_earth_voltage_v', 'Tensão fase-terra U0 (V)'],
  ['fault_loop_ohm', 'Impedância do laço Zs (Ω)'],
  ['trip_current_a', 'Corrente de atuação assegurada Ia (A)'],
  ['trip_time_s', 'Tempo assegurado para Ia (s)'],
  ['tt_ra_ohm', 'RA: eletrodo + PE no TT (Ω)'],
  ['rcd_sensitivity_ma', 'Sensibilidade nominal do DR (mA)'],
] as const;
function ProtectionFields({
  value,
  onChange,
}: {
  value?: Protection | null;
  onChange: (value: Protection) => void;
}) {
  const data: Protection = value ?? {
    earthing_system: 'unknown',
    rcd_type_compatible_confirmed: false,
  };
  const patch = (change: Partial<Protection>) => onChange({ ...data, ...change });
  return (
    <details className="mt-3">
      <summary>Curto térmico, desligamento e DR — dados complementares</summary>
      <p className="mt-2 text-xs muted">
        Use dados documentados do mesmo produto e do circuito avaliado. Não há corrente de curto,
        curva, tipo de DR ou resistência de terra presumidos.
      </p>
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <label>
          Fonte das curvas e verificações
          <input
            maxLength={200}
            value={data.source ?? ''}
            onChange={(event) => patch({ source: event.target.value || null })}
          />
        </label>
        <label>
          Esquema de aterramento
          <select
            value={data.earthing_system}
            onChange={(event) =>
              patch({ earthing_system: event.target.value as Protection['earthing_system'] })
            }
          >
            <option value="unknown">Não confirmado</option>
            <option value="TN">TN — PE separado, sem TN-C</option>
            <option value="TT">TT — proteção por DR</option>
          </select>
        </label>
        {protectionFields.map(([field, label]) => (
          <Numeric
            key={field}
            label={label}
            value={data[field]}
            onChange={(next) => patch({ [field]: next })}
          />
        ))}
        <label>
          Situação TN no anexo C
          <select
            value={data.tn_situation ?? ''}
            onChange={(event) =>
              patch({
                tn_situation: event.target.value ? (Number(event.target.value) as 1 | 2) : null,
              })
            }
          >
            <option value="">Conferir influências externas</option>
            <option value="1">Situação1</option>
            <option value="2">Situação2</option>
          </select>
        </label>
        <label>
          Tensão de contato limite UL (V)
          <select
            value={data.touch_limit_v ?? ''}
            onChange={(event) =>
              patch({
                touch_limit_v: event.target.value
                  ? (Number(event.target.value) as 12 | 25 | 50)
                  : null,
              })
            }
          >
            <option value="">Conferir anexo C</option>
            <option value="12">12V</option>
            <option value="25">25V</option>
            <option value="50">50V</option>
          </select>
        </label>
      </div>
      <label className="checkbox-option mt-3 text-xs">
        <input
          type="checkbox"
          checked={data.rcd_type_compatible_confirmed}
          onChange={(event) => patch({ rcd_type_compatible_confirmed: event.target.checked })}
        />
        Conferi tipo, funções e compatibilidade do DR com as cargas e instruções dos aparelhos.
      </label>
      <label className="checkbox-option mt-2 text-xs">
        <input
          type="checkbox"
          checked={data.rcd_additional_required ?? false}
          onChange={(event) =>
            patch({ rcd_additional_required: event.target.checked ? true : null })
          }
        />
        Confirmei exigência de DR adicional de alta sensibilidade de§5.1.3.2.
      </label>
    </details>
  );
}

const numericFields = [
  ['voltage_v', 'Tensão do circuito (V)'],
  ['length_m', 'Comprimento de ida (m)'],
  ['breaker_i2_factor', 'Relação I2/In do fabricante'],
  ['prospective_short_circuit_ka', 'Curto presumido (kA)'],
  ['breaking_capacity_ka', 'Capacidade de interrupção (kA)'],
  ['upstream_drop_percent', 'Queda a montante (%)'],
] as const;

export function CircuitStudy({
  input,
  result,
  onChange,
  onEntryChange,
}: {
  input: ProjectInput;
  result?: CalculationResult;
  onChange: (value: Circuit[]) => void;
  onEntryChange: (value: Entry | null) => void;
}) {
  const circuits = input.circuits ?? [];
  const loads = (input.environments ?? []).flatMap((room) =>
    (room.loads ?? [])
      .filter((load) => !!load.id)
      .map((load) => ({
        id: load.id!,
        name: `${room.name} · ${load.name} · ${load.quantity ?? 1} unidade(s)`,
      })),
  );
  const edit = (index: number, patch: Partial<Circuit>) =>
    onChange(circuits.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  const entry = input.service_entry;
  const assigned = new Map<string, string[]>();
  for (const circuit of circuits)
    for (const id of circuit.load_ids ?? [])
      assigned.set(id, [...(assigned.get(id) ?? []), circuit.name ?? 'Circuito sem nome']);
  const loadIds = new Set(loads.map((load) => load.id));
  const unassigned = loads.filter((load) => !assigned.has(load.id));
  const entryResult = result?.service_entry;
  const patchEntry = (patch: Partial<Entry>) => onEntryChange({ ...entry, ...patch } as Entry);
  return (
    <>
      <section className="panel circuit-study mb-6" aria-labelledby="circuits-heading">
        <SectionHeading
          eyebrow="ESTUDO OPCIONAL"
          id="circuits-heading"
          title="Estudo de circuitos"
          description="Associe cargas e confira corrente, seção, sobrecarga e queda de tensão no escopo suportado."
        />
        <p className="mt-3 text-xs muted">
          Cobre/PVC70°C, métodos B1/B2, seções de 1,5 a 95 mm², dois condutores carregados, 50/60Hz.
          Resultados condicionados às informações reais; partida, harmônicas, curto térmico,
          proteção contra choque e seletividade exigem verificação específica.
        </p>
        <button
          className="btn mt-3"
          disabled={circuits.length >= 200}
          onClick={() =>
            onChange([
              ...circuits,
              {
                id: crypto.randomUUID(),
                name: `Circuito ${circuits.length + 1}`,
                purpose: 'sockets',
                load_ids: [],
                method: 'unknown',
                breaker_ratings_a: [],
                scope_confirmed: false,
                voltage_drop_model_confirmed: false,
                overload_duration_confirmed: false,
                supply_origin: 'unknown',
              } as Circuit,
            ])
          }
        >
          Adicionar circuito
        </button>
        {circuits.length > 0 && (
          <p className="mt-3 text-xs muted" role="status">
            {loads.length === 0
              ? 'Cadastre cargas para associar aos circuitos.'
              : unassigned.length > 0
                ? `${unassigned.length} carga(s) ainda sem circuito. A associação é manual; não confirma a distribuição física da instalação.`
                : 'Todas as cargas cadastradas estão associadas. Confira as pendências de cada circuito.'}
          </p>
        )}
        <div className="mt-3 space-y-3">
          {circuits.map((c, index) => {
            const row = result?.circuit_results?.find((item) => item.circuit_id === c.id);
            const missingIds = (c.load_ids ?? []).filter((id) => !loadIds.has(id));
            return (
              <details key={c.id} className="equipment-card" data-testid="circuit-editor" open>
                <summary>
                  {c.name || 'Circuito sem nome'} ·{' '}
                  {row?.phase_section_mm2 ? 'seleção condicionada' : 'dados pendentes'}
                </summary>
                <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <label>
                    Nome do circuito
                    <input
                      value={c.name ?? ''}
                      maxLength={200}
                      onChange={(event) => edit(index, { name: event.target.value })}
                    />
                  </label>
                  <label>
                    Uso do circuito
                    <select
                      value={c.purpose}
                      onChange={(event) =>
                        edit(index, { purpose: event.target.value as Circuit['purpose'] })
                      }
                    >
                      <option value="lighting">Iluminação</option>
                      <option value="sockets">Tomadas</option>
                      <option value="dedicated">Equipamento específico</option>
                    </select>
                  </label>
                  <label>
                    Método de instalação
                    <select
                      value={c.method}
                      onChange={(event) =>
                        edit(index, { method: event.target.value as Circuit['method'] })
                      }
                    >
                      <option value="unknown">Confirmar método</option>
                      <option value="B1">
                        B1 — condutores isolados/cabos unipolares em eletroduto
                      </option>
                      <option value="B2">B2 — cabo multipolar em eletroduto</option>
                    </select>
                  </label>
                  {numericFields.map(([field, label]) => (
                    <Numeric
                      key={field}
                      label={label}
                      value={c[field]}
                      onChange={(value) => edit(index, { [field]: value })}
                    />
                  ))}
                  <label>
                    Temperatura ambiente (°C)
                    <select
                      value={c.ambient_temperature_c ?? ''}
                      onChange={(event) =>
                        edit(index, {
                          ambient_temperature_c: event.target.value
                            ? (Number(event.target.value) as Circuit['ambient_temperature_c'])
                            : null,
                        })
                      }
                    >
                      <option value="">Confirmar temperatura</option>
                      {[10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60].map((value) => (
                        <option key={value} value={value}>
                          {value} °C
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Circuitos no agrupamento homogêneo
                    <select
                      value={c.grouped_circuits ?? ''}
                      onChange={(event) =>
                        edit(index, {
                          grouped_circuits: event.target.value ? Number(event.target.value) : null,
                        })
                      }
                    >
                      <option value="">Confirmar agrupamento</option>
                      {[1, 2, 3, 4, 5, 6, 7, 8].map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Origem para limite de queda total
                    <select
                      value={c.supply_origin ?? 'unknown'}
                      onChange={(event) =>
                        edit(index, {
                          supply_origin: event.target.value as Circuit['supply_origin'],
                        })
                      }
                    >
                      <option value="unknown">Confirmar origem</option>
                      <option value="public_lv_delivery">
                        Ponto de entrega em baixa tensão — 5%
                      </option>
                      <option value="own_transformer">Transformador próprio — 7%</option>
                      <option value="delivery_at_transformer">
                        Entrega nos terminais do transformador da distribuidora — 7%
                      </option>
                      <option value="generator">Gerador próprio — 7%</option>
                    </select>
                  </label>
                  <Ratings
                    value={c.breaker_ratings_a ?? []}
                    onChange={(value) => edit(index, { breaker_ratings_a: value })}
                  />
                  <label>
                    Fonte dos dados da proteção
                    <input
                      maxLength={200}
                      value={c.breaker_source ?? ''}
                      onChange={(event) =>
                        edit(index, { breaker_source: event.target.value || null })
                      }
                      placeholder="Fabricante, produto, revisão e página"
                    />
                  </label>
                </div>
                <fieldset className="mt-3">
                  <legend className="text-sm font-semibold">Cargas deste circuito</legend>
                  <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {loads.map((load) => (
                      <label key={load.id} className="checkbox-option">
                        <input
                          type="checkbox"
                          checked={c.load_ids?.includes(load.id) ?? false}
                          disabled={!c.load_ids?.includes(load.id) && assigned.has(load.id)}
                          onChange={(event) =>
                            edit(index, {
                              load_ids: event.target.checked
                                ? [...(c.load_ids ?? []), load.id]
                                : (c.load_ids ?? []).filter((key) => key !== load.id),
                            })
                          }
                        />
                        {load.name}
                        {!c.load_ids?.includes(load.id) && assigned.has(load.id) && (
                          <span className="text-xs muted">
                            {' '}
                            — associado a {assigned.get(load.id)!.join(', ')}
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                  {loads.length === 0 && (
                    <p className="text-xs muted">Cadastre os equipamentos primeiro.</p>
                  )}
                  {missingIds.length > 0 && (
                    <div className="mt-3 text-xs">
                      <p>
                        Este circuito aponta para {missingIds.length} carga(s) que não existem mais
                        no projeto.
                      </p>
                      <button
                        className="btn mt-2"
                        onClick={() =>
                          edit(index, { load_ids: c.load_ids?.filter((id) => loadIds.has(id)) })
                        }
                      >
                        Remover associações de cargas ausentes
                      </button>
                    </div>
                  )}
                </fieldset>
                <div className="mt-3 space-y-2 text-xs">
                  <label className="checkbox-option">
                    <input
                      type="checkbox"
                      checked={c.scope_confirmed ?? false}
                      onChange={(event) => edit(index, { scope_confirmed: event.target.checked })}
                    />
                    Conferi instalação fixa, cobre/PVC70°C, método, dois condutores carregados,
                    conduto não magnético, PE no mesmo conduto, cargas indutivas/resistivas
                    senoidais e agrupamento homogêneo nas condições mais desfavoráveis do percurso.
                  </label>
                  <label className="checkbox-option">
                    <input
                      type="checkbox"
                      checked={c.voltage_drop_model_confirmed ?? false}
                      onChange={(event) =>
                        edit(index, { voltage_drop_model_confirmed: event.target.checked })
                      }
                    />
                    Aceito estimativa de queda em regime: modelo Prysmian, ρ=0,0225 Ω·mm²/m e
                    reatância=0,08 mΩ/m; cargas concentradas no fim do trecho, sem avaliar partida.
                  </label>
                  <label className="checkbox-option">
                    <input
                      type="checkbox"
                      checked={c.overload_duration_confirmed ?? false}
                      onChange={(event) =>
                        edit(index, { overload_duration_confirmed: event.target.checked })
                      }
                    />
                    Conferi a condição de duração de sobrecarga de 5.3.4.1 (100h/12meses ou
                    500h/vida útil). Sem confirmação, o cálculo aplica I2 ≤ Iz.
                  </label>
                </div>
                <ProtectionFields
                  value={c.protections}
                  onChange={(value) => edit(index, { protections: value })}
                />
                <div className="mt-3 border-t border-slate-700 pt-3" data-testid="circuit-result">
                  <p className="text-sm">
                    Ib: {format(row?.design_current_a)} A · In: {format(row?.breaker_a)} A · fase:{' '}
                    {format(row?.phase_section_mm2)} mm² · PE: {format(row?.pe_section_mm2)} mm²
                  </p>
                  <p className="mt-1 text-xs muted">
                    Iz corrigida: {format(row?.capacity_a)} A · queda estimada:{' '}
                    {format(row?.voltage_drop_percent)}% · queda total:{' '}
                    {format(row?.total_drop_percent)}%
                  </p>
                  {row && (
                    <p className="mt-2 text-xs muted">
                      Capacidade de interrupção:{' '}
                      {row.breaking_capacity_ok === true
                        ? 'atende ao curto presumido informado'
                        : row.breaking_capacity_ok === false
                          ? 'não atende ao curto presumido informado'
                          : 'pendente de dados'}
                      .
                    </p>
                  )}
                  <ul className="mt-2 space-y-1 text-xs muted">
                    {row?.pending_checks.map((message) => (
                      <li key={message}>{message}</li>
                    ))}
                  </ul>
                  {row?.protection_checks?.map((check) => (
                    <p key={check.code} className="mt-2 text-xs muted">
                      {check.label}:{' '}
                      {check.passed === true
                        ? 'atende ao critério informado'
                        : check.passed === false
                          ? 'não atende'
                          : 'pendente'}
                      . {check.reason}
                    </p>
                  ))}
                  {row && (
                    <details className="mt-3">
                      <summary>Fontes e limites do método</summary>
                      <p className="mt-2 text-xs muted">{row.reference}</p>
                      <ul className="mt-2 space-y-1 text-xs muted">
                        {row.limitations.map((limitation) => (
                          <li key={limitation}>{limitation}</li>
                        ))}
                      </ul>
                      <ul className="mt-2 space-y-2 text-xs break-words">
                        {row.reference_urls?.map(
                          (url) =>
                            safeReferenceUrl(url) && (
                              <li key={url}>
                                <a
                                  className="underline"
                                  href={safeReferenceUrl(url)}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  {url}
                                </a>
                              </li>
                            ),
                        )}
                      </ul>
                    </details>
                  )}
                  {!row && (
                    <p role="status" className="text-xs muted">
                      Aguardando cálculo das entradas atuais.
                    </p>
                  )}
                </div>
                <button
                  className="btn subtle mt-3"
                  onClick={() => onChange(circuits.filter((_, i) => i !== index))}
                >
                  Remover circuito
                </button>
              </details>
            );
          })}
        </div>
      </section>
      <section className="panel circuit-study mb-6" aria-labelledby="entry-heading">
        <SectionHeading
          eyebrow="ESTUDO OPCIONAL"
          id="entry-heading"
          title="Referência de padrão de entrada"
          description="Enquadramento limitado à Energisa Sul-Sudeste/SP, rede 220/127V, unidade residencial individual até75kW."
        />
        <p className="mt-3 text-xs muted">
          Tabela16 da NDU-0017.0. Seções mínimas de tabela não concluem dimensionamento. A aprovação
          do atendimento depende da distribuidora.
        </p>
        {!entry ? (
          <button
            className="btn mt-3"
            onClick={() =>
              onEntryChange({
                network: 'unknown',
                route: 'unknown',
                insulation: 'unknown',
                scope_confirmed: false,
                special_loads_reviewed: false,
              })
            }
          >
            Estudar entrada de energia
          </button>
        ) : (
          <>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <label>
                Rede confirmada
                <select
                  value={entry.network}
                  onChange={(event) =>
                    patchEntry({ network: event.target.value as Entry['network'] })
                  }
                >
                  <option value="unknown">Não confirmada</option>
                  <option value="220_127">220/127V</option>
                </select>
              </label>
              <label>
                Ramal de entrada
                <select
                  value={entry.route}
                  onChange={(event) => patchEntry({ route: event.target.value as Entry['route'] })}
                >
                  <option value="unknown">Confirmar percurso</option>
                  <option value="embedded">Embutido</option>
                  <option value="underground">Subterrâneo</option>
                </select>
              </label>
              <label>
                Isolação do ramal
                <select
                  value={entry.insulation}
                  onChange={(event) =>
                    patchEntry({ insulation: event.target.value as Entry['insulation'] })
                  }
                >
                  <option value="unknown">Confirmar isolação</option>
                  <option value="PVC70">PVC70°C — 0,6/1kV</option>
                  <option value="XLPE90">XLPE/HEPR/EPR90°C — 0,6/1kV</option>
                </select>
              </label>
              <label>
                Fases solicitadas
                <select
                  value={entry.requested_phases ?? ''}
                  onChange={(event) =>
                    patchEntry({
                      requested_phases: event.target.value
                        ? (Number(event.target.value) as 1 | 2 | 3)
                        : null,
                    })
                  }
                >
                  <option value="">Enquadrar por carga e tensão</option>
                  <option value="1">Uma fase e neutro</option>
                  <option value="2">Duas fases e neutro</option>
                  <option value="3">Três fases e neutro</option>
                </select>
              </label>
            </div>
            <label className="checkbox-option mt-3 text-xs">
              <input
                type="checkbox"
                checked={entry.scope_confirmed}
                onChange={(event) => patchEntry({ scope_confirmed: event.target.checked })}
              />
              Confirmei fornecimento ESS no endereço, rede220/127V e escopo residencial individual
              da NDU0017.0.
            </label>
            <label className="checkbox-option mt-2 text-xs">
              <input
                type="checkbox"
                checked={entry.special_loads_reviewed}
                onChange={(event) => patchEntry({ special_loads_reviewed: event.target.checked })}
              />
              Revisei as restrições de motores, solda, cargas especiais e limites de atendimento
              de§6.6.
            </label>
            <div className="mt-3" data-testid="entry-result">
              <p className="text-sm">
                Categoria: {entryResult?.category ?? '—'} · fases: {format(entryResult?.phases)}
              </p>
              <p className="mt-1 text-xs muted">
                Mínimos fase/neutro/aterramento: {format(entryResult?.minimum_phase_mm2)} /{' '}
                {format(entryResult?.minimum_neutral_mm2)} /{' '}
                {format(entryResult?.minimum_earthing_mm2)} mm²
              </p>
              {entryResult?.basis_value != null && (
                <p className="mt-2 text-xs muted">
                  Base do enquadramento: {format(entryResult.basis_value)} {entryResult.basis_unit}.{' '}
                  Disjuntores no limite superior da faixa:{' '}
                  {entryResult.band_breaker_references_a.map((value) => format(value)).join(' / ')}{' '}
                  A. São referências da tabela, não uma proteção escolhida para o projeto.
                </p>
              )}
              <ul className="mt-2 space-y-1 text-xs muted">
                {entryResult?.pending_checks.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
              {entryResult && (
                <details className="mt-3 text-xs muted">
                  <summary>Fonte do enquadramento</summary>
                  <p className="mt-2 break-words">{entryResult.reference}</p>
                </details>
              )}
            </div>
            <button className="btn subtle mt-3" onClick={() => onEntryChange(null)}>
              Remover estudo da entrada
            </button>
          </>
        )}
      </section>
    </>
  );
}
