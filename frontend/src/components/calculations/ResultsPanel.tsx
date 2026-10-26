'use client';
import { useExperience } from '@/lib/experience';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { safeReferenceUrl } from '@/lib/safe-url';
import { useState } from 'react';
import type { CalculationResult, ProjectInput } from '@/lib/api';
import { format, formatCurrency } from '@/lib/format';
import { CalculationNotices, focusField } from '@/components/calculations-notices';
import { DemandSummary } from './DemandSummary';
import { NormativeAvailability, normativeLabels as ruleLabels } from './NormativeAvailability';
const statusLabels = {
  calculated: 'Calculado',
  estimated: 'Estimado',
  pending: 'Pendente',
  invalid: 'Inválido',
  out_of_scope: 'Fora do escopo',
  awaiting_technical_validation: 'Não validado normativamente',
};

export function ResultsPanel({
  result,
  loading,
  stale,
  scope,
  environments,
  tariff,
  onScopeChange,
}: {
  result?: CalculationResult;
  loading: boolean;
  stale: boolean;
  scope: ProjectInput['analysis_scope'];
  environments?: ProjectInput['environments'];
  tariff?: ProjectInput['energy_tariff_brl_per_kwh'];
  onScopeChange: (scope: ProjectInput['analysis_scope']) => void;
}) {
  const { profile } = useExperience();
  const [detailPreference, setDetailPreference] = useState<{ profile: string; value: boolean }>();
  const technical =
    detailPreference?.profile === profile ? detailPreference.value : profile === 'professional';
  const setTechnical = (value: boolean) => setDetailPreference({ profile, value });
  const notices = result?.notifications ?? [];
  const issues = notices.filter((item) => ['error', 'technical'].includes(item.category));
  function completeEnergy(id = result?.energy_unknown_load_ids?.[0]) {
    if (!id) return;
    const load = environments?.flatMap((room) => room.loads ?? []).find((item) => item.id === id);
    const params = load?.parameters;
    let field = 'parameters.usage_hours_per_day';
    if (result?.unknown_load_ids?.includes(id)) {
      field =
        params?.power_mode === 'mechanical'
          ? params.mechanical_power == null
            ? 'parameters.mechanical_power'
            : 'parameters.efficiency'
          : 'unit_power_w';
    } else if (params?.usage_hours_per_day != null) {
      field =
        params.usage_days_per_month == null
          ? 'parameters.usage_days_per_month'
          : 'parameters.monthly_energy_kwh';
    }
    focusField(`load.${id}.${field}`);
  }
  function loadLocation(id: string) {
    const room = environments?.find((item) => item.loads?.some((load) => load.id === id));
    const load = room?.loads?.find((item) => item.id === id);
    return (
      [room?.name, load?.name ?? result?.load_results?.find((item) => item.load_id === id)?.name]
        .filter(Boolean)
        .join(' → ') || 'Aparelho sem consumo informado'
    );
  }
  const demandAvailable =
    result?.normative.demand?.value != null &&
    ['calculated', 'estimated'].includes(String(result.normative.demand.status));
  return (
    <section
      id="results"
      tabIndex={-1}
      aria-labelledby="results-heading"
      className="panel min-h-64"
      aria-busy={loading}
      data-stale={stale}
    >
      <header className="section-header">
        <SectionHeading
          id="results-heading"
          eyebrow="03 / CONFERÊNCIA"
          title="Confira sua estimativa"
          description="Veja o consumo e o custo mensal dos aparelhos cadastrados."
        />
      </header>
      <p className="mt-3 text-xs muted" role="status">
        {loading
          ? result
            ? 'Recalculando · os valores anteriores estão desatualizados.'
            : 'Calculando as entradas atuais…'
          : stale
            ? 'Valores desatualizados; confira as entradas ou a conexão. Exportação indisponível.'
            : result
              ? 'Resultados correspondem às entradas atuais.'
              : 'Sem resultados atuais.'}
      </p>
      {result ? (
        <div hidden={stale}>
          <div className="result-section" aria-label="Resumo de resultados">
            <div
              className="consumption-summary grid gap-5 md:grid-cols-2"
              aria-label="Consumo e custo mensais"
            >
              <div>
                <p className="text-xs muted">
                  Consumo mensal{' '}
                  {result.energy_unknown_load_ids?.length ? '· subtotal conhecido' : '· estimativa'}
                </p>
                <p
                  className={
                    result.monthly_energy
                      ? 'mt-2 text-2xl font-semibold text-emerald-300'
                      : 'mt-2 text-sm muted'
                  }
                >
                  {result.monthly_energy
                    ? `${format(result.monthly_energy.value)} kWh/mês`
                    : 'Abra Consumo mensal em cada aparelho e informe os horários ou os kWh da etiqueta.'}
                </p>
                {!!result.energy_unknown_load_ids?.length && (
                  <div className="mt-3">
                    <p className="text-xs muted">
                      {result.energy_unknown_load_ids.length} aparelho(s) sem consumo informado. O
                      subtotal não representa a moradia completa.
                    </p>
                    <button className="text-action mt-2" onClick={() => completeEnergy()}>
                      Completar consumo dos aparelhos
                    </button>
                    <details className="mt-3">
                      <summary>Aparelhos com consumo pendente</summary>
                      <ul className="mt-2 space-y-2">
                        {result.energy_unknown_load_ids.map((id) => (
                          <li key={id} className="text-sm">
                            <button className="text-action" onClick={() => completeEnergy(id)}>
                              Informar consumo: {loadLocation(id)}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}
                <p className="mt-1 text-xs muted">
                  A estimativa cobre os equipamentos cadastrados. Horários devem representar
                  funcionamento efetivo; não é medição nem inclui automaticamente standby ou
                  aparelhos ausentes.
                </p>
              </div>
              <div>
                <p className="text-xs muted">Custo mensal da energia cadastrada</p>
                <p
                  className={
                    result.monthly_cost
                      ? 'mt-2 text-2xl font-semibold text-emerald-300'
                      : 'mt-2 text-sm muted'
                  }
                >
                  {result.monthly_cost
                    ? formatCurrency(result.monthly_cost.value)
                    : 'Informe a tarifa no projeto e o consumo dos aparelhos.'}
                </p>
                <p className="mt-1 text-xs muted">
                  Estimativa pela tarifa informada; não é a fatura completa. Não inclui encargos
                  fixos ou tributos adicionais.
                </p>
                {tariff == null && environments && (
                  <button
                    className="text-action mt-2"
                    onClick={() => focusField('project.energy_tariff_brl_per_kwh')}
                  >
                    Informar tarifa para estimar o custo
                  </button>
                )}
              </div>
            </div>
            {result.load_results?.some((item) => item.monthly_energy_kwh != null) && (
              <details className="mt-5">
                <summary>Consumo por aparelho</summary>
                <p className="mt-2 text-xs muted">
                  Valores para a quantidade cadastrada de cada aparelho. Aparelhos sem dados de uso
                  ficam pendentes.
                </p>
                <ul className="mt-3 divide-y divide-slate-700">
                  {result.load_results.map((item) => (
                    <li
                      key={item.load_id}
                      className="flex flex-wrap justify-between gap-2 py-2 text-sm"
                    >
                      <span>{loadLocation(item.load_id)}</span>
                      <span className="muted">
                        {item.monthly_energy_kwh == null
                          ? 'Consumo não informado'
                          : `${format(item.monthly_energy_kwh)} kWh/mês`}
                        {item.monthly_cost_brl != null
                          ? ` · ${formatCurrency(item.monthly_cost_brl)}`
                          : ''}
                      </span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
            <details className="mt-5">
              <summary>Potência dos aparelhos cadastrados</summary>
              <p className="mt-2 mb-3 text-xs muted">
                Potência (W) indica a carga elétrica dos aparelhos. O consumo mensal (kWh) depende
                também de quanto tempo são usados.
              </p>
              <div className="grid gap-5 md:grid-cols-2" aria-label="Potência cadastrada">
                <div>
                  <p className="text-xs muted">
                    {result.unknown_load_ids?.length
                      ? 'Potência conhecida · total incompleto'
                      : 'Potência instalada cadastrada'}
                  </p>
                  <p className="mt-2 text-3xl text-emerald-300">
                    {format(result.installed_power_kw.value)}{' '}
                    <span className="text-sm muted">kW</span>
                  </p>
                  <p className="mt-2 text-xs muted">
                    {statusLabels[result.installed_power.status]} ·{' '}
                    {format(result.installed_power.value)} W
                  </p>
                </div>
                <div>
                  <p className="text-xs muted">Iluminação nominal cadastrada</p>
                  <p className="mt-2 text-2xl">{format(result.lighting_nominal.value)} W</p>
                  <p className="mt-2 text-xs muted">Incluída na potência instalada.</p>
                </div>
              </div>
            </details>
          </div>
          <div className="result-section">
            <h3 className="result-section-title">Dados do projeto a revisar</h3>
            <CalculationNotices notices={issues} stale={stale} />
            {!issues.length && !stale && (
              <p className="text-sm muted">Nenhum dado pendente para o cálculo selecionado.</p>
            )}
          </div>
          <details open={profile === 'professional' || undefined} className="result-details mt-5">
            <summary>Detalhes dos cálculos e previsões técnicas</summary>
            <div className="mt-4 flex flex-wrap gap-4">
              {profile === 'explore' ? (
                <label>
                  Apresentação
                  <select
                    aria-label="Apresentação"
                    value={technical ? 'technical' : 'simple'}
                    onChange={(e) => setTechnical(e.target.value === 'technical')}
                  >
                    <option value="simple">Simples</option>
                    <option value="technical">Técnica</option>
                  </select>
                </label>
              ) : (
                <label className="checkbox-option">
                  <input
                    type="checkbox"
                    checked={technical}
                    onChange={(e) => setTechnical(e.target.checked)}
                  />
                  Mostrar verificações e memória detalhadas
                </label>
              )}
              <label className="max-w-sm">
                Requisitos para
                <select
                  aria-label="Requisitos para"
                  value={scope ?? 'installed'}
                  onChange={(e) => onScopeChange(e.target.value as ProjectInput['analysis_scope'])}
                >
                  <option value="installed">Potência instalada (W)</option>
                  <option value="apparent">Potência aparente (VA)</option>
                  <option value="current">Corrente elétrica (A)</option>
                  <option value="normative">Previsão residencial (luz/TUG)</option>
                </select>
              </label>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs muted">Potência aparente · soma escalar</p>
                <p className="mt-2 text-sm">
                  {result.apparent_power
                    ? `${format(result.apparent_power.value)} VA · ${format(result.apparent_power_kva?.value)} kVA`
                    : 'Sem dados suficientes para VA. A soma em W é independente.'}
                </p>
              </div>
              <div>
                <p className="text-xs muted">Potências por categoria</p>
                {Object.entries(result.by_category_w).map(([category, power]) => (
                  <p key={category} className="mt-1 flex justify-between gap-3 text-sm">
                    <span>{category}</span>
                    <span>{format(power)} W</span>
                  </p>
                ))}
              </div>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {Object.entries(result.normative)
                .filter(([key, rule]) => key !== 'demand' && rule.value != null)
                .map(([key, rule]) => (
                  <div key={key} className="text-xs muted">
                    <p>{ruleLabels[key] ?? key}</p>
                    <p className="mt-1">
                      {rule.value != null
                        ? `${format(rule.value)} ${String(rule.unit ?? '')}`
                        : (statusLabels[String(rule.status) as keyof typeof statusLabels] ??
                          'Indisponível')}
                    </p>
                  </div>
                ))}
            </div>
            {demandAvailable && <DemandSummary demand={result.normative.demand} stale={stale} />}
            {scope === 'normative' && !stale && (
              <div className="result-section" aria-label="Previsão residencial por ambiente">
                <h3 className="result-section-title">
                  Previsão residencial · iluminação e tomadas
                </h3>
                <p className="text-sm muted">
                  Aplicável a ambientes de habitação. Valores em VA separados dos aparelhos em W. A
                  quantidade cadastrada é preservada. Este estudo não verifica localização,
                  proteção, circuitos ou conformidade integral da instalação.
                </p>
                {!result.normative_environments?.length && (
                  <p className="mt-3 text-sm">Adicione um ambiente para calcular.</p>
                )}
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {result.normative_environments?.map((room) => (
                    <article
                      className="rounded-lg border border-slate-700 p-4 text-sm"
                      key={room.environment_id}
                    >
                      <h4 className="font-semibold">{room.name}</h4>
                      <p className="mt-2">
                        Iluminação:{' '}
                        {room.lighting_va == null
                          ? 'Informe a área ou confira o tipo.'
                          : `${format(room.lighting_va)} VA`}
                      </p>
                      <p className="mt-1">
                        Pontos de luz: {room.registered_lighting_points} cadastrado(s) · mínimo{' '}
                        {room.minimum_lighting_points ?? 'não avaliado'}
                      </p>
                      <p className="mt-2">
                        TUG: {room.registered_outlet_points} cadastrado(s) · mínimo{' '}
                        {room.minimum_outlet_points ?? 'não avaliado'}
                      </p>
                      <p className="mt-1">
                        Previsão TUG:{' '}
                        {room.outlets_va == null
                          ? 'Dados ou classificação insuficientes.'
                          : `${format(room.outlets_va)} VA · ${room.outlet_basis_points} ponto(s) considerados`}
                      </p>
                      {!!room.missing_fields.length && (
                        <p className="mt-2 text-amber-200">
                          Informe:{' '}
                          {room.missing_fields
                            .map((field) => (field === 'area_m2' ? 'área (m²)' : 'perímetro (m)'))
                            .join(' e ')}
                          .
                        </p>
                      )}
                      {room.status === 'out_of_scope' && (
                        <p className="mt-2 text-amber-200">{room.reason}</p>
                      )}
                      <details className="mt-3 text-xs muted">
                        <summary className="cursor-pointer">
                          Condições e limites deste ambiente
                        </summary>
                        {room.notes.map((note) => (
                          <p className="mt-2" key={note}>
                            {note}
                          </p>
                        ))}
                      </details>
                    </article>
                  ))}
                </div>
                <details className="mt-4 text-xs muted">
                  <summary className="cursor-pointer">Fontes dos critérios residenciais</summary>
                  {result.normative_capabilities
                    ?.find((item) => item.code === 'lighting')
                    ?.evidence.map(
                      (source) =>
                        safeReferenceUrl(source.url) && (
                          <p className="mt-2" key={source.url}>
                            <a
                              className="underline"
                              href={safeReferenceUrl(source.url)}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {source.title}
                            </a>{' '}
                            · {source.section}
                          </p>
                        ),
                    )}
                </details>
              </div>
            )}
            <h3 className="result-section result-section-title">Memória de cálculo</h3>
            <details open={technical || undefined} className="mt-3">
              <summary className="cursor-pointer text-sm">Memória por equipamento</summary>
              <div className="divide-y divide-slate-700">
                {result.memory.map((entry) => (
                  <div key={entry.load_id} className="py-4">
                    <p className="font-medium">{entry.name}</p>
                    <p className="mt-2 font-mono text-sm text-emerald-300">
                      {entry.inputs.quantity} × {format(entry.inputs.unit_power_w)} W ={' '}
                      {format(entry.result.value)} W
                    </p>
                    <p className="mt-2 text-xs muted">
                      {statusLabels[entry.status]} ·{' '}
                      {entry.manual_override ? 'Valor personalizado · ' : ''}
                      {entry.source}
                    </p>
                  </div>
                ))}
              </div>
            </details>
            <details open={technical || undefined} className="mt-4">
              <summary className="cursor-pointer text-sm">Memória das somas e conversões</summary>
              {result.aggregate_steps?.map((step, index) => (
                <div key={`${step.calculation}-${index}`} className="mt-4 text-sm">
                  <p>{step.calculation}</p>
                  <p className="mt-1 font-mono text-xs text-emerald-300">{step.formula}</p>
                  <p className="mt-1 break-words font-mono text-xs">{step.substituted}</p>
                  <p className="mt-1 text-xs muted">{step.assumptions}</p>
                </div>
              ))}
            </details>
            <details open={technical || undefined} className="mt-4">
              <summary className="cursor-pointer text-sm">Grandezas por equipamento</summary>
              {result.load_results?.map((item) => (
                <div key={item.load_id} className="mt-4">
                  <p className="text-sm font-medium">{item.name}</p>
                  {item.steps.map((step) => (
                    <div key={step.calculation} className="mt-2 text-xs">
                      <p className="text-emerald-300">
                        {step.calculation === 'thermal_capacity'
                          ? 'Capacidade térmica'
                          : step.calculation === 'current'
                            ? 'Corrente por unidade'
                            : step.calculation === 'motor_input'
                              ? 'Entrada elétrica do motor'
                              : step.calculation === 'monthly_energy'
                                ? 'Consumo mensal da quantidade cadastrada'
                                : step.calculation === 'monthly_cost'
                                  ? 'Custo mensal estimado'
                                  : 'Potência aparente'}
                        : {format(step.value)} {step.unit}
                      </p>
                      <p className="mt-1 font-mono">{step.formula}</p>
                      <p className="mt-1 font-mono">{step.substituted}</p>
                      <p className="mt-1 muted">{step.assumptions}</p>
                      {safeReferenceUrl(step.source) && (
                        <a
                          className="underline muted"
                          href={safeReferenceUrl(step.source)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Referência de conversão
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </details>
            <details open={technical || undefined} className="mt-4">
              <summary className="cursor-pointer text-sm">Referências e rastreabilidade</summary>
              <p className="mt-3 break-all text-xs muted">
                Motor {result.engine_version} · Entradas SHA-256: {result.input_digest}
              </p>
            </details>
            <details className="mt-4 text-xs muted">
              <summary className="cursor-pointer">Critério de contagem das cargas</summary>
              <p className="mt-2">{result.counting_policy}</p>
            </details>
            <NormativeAvailability result={result} stale={stale} />
          </details>
        </div>
      ) : (
        <p className="mt-6 text-sm muted">
          {loading || stale
            ? 'Aguardando cálculo das entradas atuais…'
            : 'Corrija os dados ou verifique a conexão com a API.'}
        </p>
      )}
    </section>
  );
}
