import { format } from '@/lib/format';
const states: Record<string, string> = {
  calculated: 'Calculada',
  estimated: 'Estimativa',
  pending: 'Dados de entrada pendentes',
  invalid: 'Entradas inválidas',
  out_of_scope: 'Fora do escopo implementado',
  awaiting_technical_validation: 'Cálculo ainda indisponível',
};

export function DemandSummary({
  demand,
  stale,
}: {
  demand?: Record<string, unknown>;
  stale: boolean;
}) {
  const status = String(demand?.status ?? 'pending');
  const hasValue = demand?.value != null && ['calculated', 'estimated'].includes(status);
  return (
    <div className="min-w-0" data-stale={stale}>
      <p className="text-sm muted">Demanda da distribuidora</p>
      <p
        className={`mt-4 text-xl font-semibold ${hasValue ? 'text-emerald-300' : 'text-amber-200'}`}
      >
        {hasValue
          ? `${format(demand.value)} ${String(demand.unit ?? 'kVA')}`
          : demand
            ? (states[status] ?? 'Estado não reconhecido')
            : 'Aguardando resposta da API'}
      </p>
      <p className="mt-2 text-xs muted">
        {stale
          ? 'Resultado anterior · recálculo em andamento'
          : hasValue
            ? states[status]
            : 'Potência instalada permanece disponível separadamente.'}
      </p>
      {demand?.reason != null && (
        <details className="mt-3 text-xs muted">
          <summary className="cursor-pointer">Por que não foi calculada?</summary>
          <p className="mt-2 leading-5">{String(demand.reason)}</p>
        </details>
      )}
    </div>
  );
}
