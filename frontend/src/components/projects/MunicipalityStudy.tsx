'use client';

import { useEffect, useRef, useState } from 'react';
import { request } from '@/lib/api';
import type { components } from '@/lib/api.generated';
import { format, formatDate } from '@/lib/format';
import { safeReferenceUrl } from '@/lib/safe-url';

type Lookup = components['schemas']['MunicipalityLookup'];
export function MunicipalityStudy() {
  const [code, setCode] = useState('');
  const [result, setResult] = useState<Lookup>();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  function clear() {
    controller.current?.abort();
    setResult(undefined);
    setError('');
    setLoading(false);
  }
  async function lookup() {
    clear();
    const pending = new AbortController();
    controller.current = pending;
    setLoading(true);
    try {
      const data = await request<Lookup>(
        `/locations/municipality?${new URLSearchParams({ code })}`,
        { signal: pending.signal },
      );
      if (!pending.signal.aborted) setResult(data);
    } catch (cause) {
      if (!pending.signal.aborted)
        setError(
          cause instanceof Error ? cause.message : 'Não foi possível consultar o município.',
        );
    } finally {
      if (!pending.signal.aborted) setLoading(false);
    }
  }
  return (
    <details className="mt-4">
      <summary>Distribuidoras por município — declarações oficiais ANEEL</summary>
      <p className="mt-2 text-xs muted">
        Consulta opcional por código IBGE. Preserva todas as distribuidoras com consumidores ativos
        declarados no último mês declarado por cada empresa, sem escolher uma empresa ou alterar o
        projeto.
      </p>
      <form
        className="mt-3 flex flex-wrap items-end gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          void lookup();
        }}
      >
        <label>
          Código IBGE do município (7 dígitos)
          <input
            required
            inputMode="numeric"
            pattern="[0-9]{7}"
            minLength={7}
            maxLength={7}
            value={code}
            onChange={(event) => {
              clear();
              setCode(event.target.value);
            }}
          />
        </label>
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Consultando município…' : 'Consultar distribuidoras no município'}
        </button>
        <a
          className="text-sm underline"
          href="https://www.ibge.gov.br/explica/codigos-dos-municipios.php"
          target="_blank"
          rel="noreferrer"
        >
          Consultar códigos no IBGE
        </a>
      </form>
      {error && (
        <p role="alert" className="mt-3">
          {error}
        </p>
      )}
      {result && (
        <div role="status" className="mt-3">
          {result.municipality && (
            <p className="font-semibold">
              {result.municipality.name} · {result.municipality.state} · {result.municipality.code}
            </p>
          )}
          <p>{result.reason}</p>
          <p className="mt-2 text-xs muted">{result.notice}</p>
          {result.reference_month && (
            <p className="mt-2 text-xs">
              Mês mais recente no município: {result.reference_month.slice(0, 7)}. Atrasos na
              declaração não comprovam encerramento de atendimento.
            </p>
          )}
          {result.consulted_on && (
            <p className="text-xs">Coleta: {formatDate(result.consulted_on)}.</p>
          )}
          <ul className="mt-3 space-y-2">
            {result.candidates.map((item) => (
              <li key={item.cnpj}>
                <p>
                  {item.acronym} · {item.name}
                </p>
                <p className="text-xs">
                  CNPJ {item.cnpj} · {item.grant_type} · {format(item.active_units)} unidades ativas
                  declaradas em {item.reference_month.slice(0, 7)}.
                </p>
              </li>
            ))}
          </ul>
          <a
            className="mt-3 inline-block text-sm underline"
            href={safeReferenceUrl(result.source)}
            target="_blank"
            rel="noreferrer"
          >
            Abrir fonte oficial INDGER/ANEEL
          </a>
        </div>
      )}
    </details>
  );
}
