'use client';
import type { CalculationResult } from '@/lib/api';
import { safeReferenceUrl } from '@/lib/safe-url';

export const normativeLabels: Record<string, string> = {
  lighting: 'Previsão mínima de iluminação',
  outlets: 'Previsão de tomadas',
  demand: 'Demanda da distribuidora',
};

/** Product coverage stays separate from errors the user can actually correct. */
export function NormativeAvailability({
  result,
  stale,
}: {
  result: CalculationResult;
  stale: boolean;
}) {
  const capabilities = result.normative_capabilities?.length
    ? result.normative_capabilities
    : Object.entries(result.normative)
        .filter(([, rule]) => rule.value == null)
        .map(([code, rule]) => ({
          code,
          label: normativeLabels[code] ?? code,
          available: false,
          purpose: '',
          reason: String(rule.reason ?? 'Cálculo ainda indisponível neste estudo.'),
          evidence: [],
          pending_checks: [],
          status: String(rule.status),
        }));
  const unavailable = capabilities.filter((item) => !item.available);
  if (!unavailable.length) return null;
  return (
    <aside
      className="result-section text-sm muted"
      aria-label="Cobertura normativa"
      data-stale={stale}
    >
      <details>
        <summary className="cursor-pointer">
          Recursos normativos ainda indisponíveis ({unavailable.length})
        </summary>
        {stale ? (
          <p className="mt-3">Atualizando a cobertura para as entradas atuais…</p>
        ) : (
          <>
            <p className="mt-3">
              Estas são limitações do sistema. Não indicam erros na sua instalação e não são
              resolvidas preenchendo mais campos. Os cálculos de cargas disponíveis continuam
              independentes.
            </p>
            <div className="mt-4 space-y-5">
              {unavailable.map((item) => (
                <section key={item.code}>
                  <h4 className="font-semibold text-slate-200">{item.label}</h4>
                  {item.purpose && <p className="mt-1 text-xs leading-5">{item.purpose}</p>}
                  <p className="mt-1 text-xs leading-5">{item.reason}</p>
                  {!!item.evidence.length && (
                    <details className="mt-2 text-xs">
                      <summary className="cursor-pointer">
                        Pesquisa e fontes de {item.label.toLocaleLowerCase('pt-BR')}
                      </summary>
                      {item.evidence.map((evidence, index) => (
                        <div
                          key={`${evidence.url}-${index}`}
                          className="mt-3 break-words leading-5"
                        >
                          <p>
                            {safeReferenceUrl(evidence.url) ? (
                              <a
                                className="text-emerald-300 underline"
                                href={safeReferenceUrl(evidence.url)}
                                target="_blank"
                                rel="noreferrer"
                              >
                                {evidence.title}
                              </a>
                            ) : (
                              evidence.title
                            )}
                          </p>
                          <p>{evidence.finding}</p>
                          {evidence.section && <p>{evidence.section}</p>}
                          <p>
                            Consulta: {evidence.consulted_on} ·{' '}
                            {evidence.access === 'official_index'
                              ? 'Trecho indexado; leitura integral não confirmada'
                              : 'Metadados oficiais; não equivalem ao texto completo'}
                          </p>
                        </div>
                      ))}
                      {!!item.pending_checks.length && (
                        <>
                          <p className="mt-3 font-medium">Falta para habilitar este cálculo:</p>
                          <ul className="mt-1 list-disc space-y-1 pl-5">
                            {item.pending_checks.map((check) => (
                              <li key={check}>{check}</li>
                            ))}
                          </ul>
                        </>
                      )}
                    </details>
                  )}
                </section>
              ))}
            </div>
          </>
        )}
      </details>
    </aside>
  );
}
