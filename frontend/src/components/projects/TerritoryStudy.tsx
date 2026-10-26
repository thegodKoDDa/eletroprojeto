'use client';

import { useEffect, useRef, useState } from 'react';
import { request } from '@/lib/api';
import type { components } from '@/lib/api.generated';
import { formatDate } from '@/lib/format';
import { safeReferenceUrl } from '@/lib/safe-url';
import { MunicipalityStudy } from './MunicipalityStudy';
import { SectionHeading } from '@/components/ui/SectionHeading';

type Lookup = components['schemas']['TerritoryLookup'];
const periods = {
  ended: 'Vigência encerrada no registro — não usar como distribuidora atual',
  not_started: 'Vigência ainda não iniciada no registro',
  within_recorded_period: 'Ponto dentro do período registrado; confirmar vigência atual',
  no_end_recorded: 'Sem fim de vigência informado; confirmar situação atual',
};

export function TerritoryStudy() {
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
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
        `/locations/territory?${new URLSearchParams({ latitude, longitude })}`,
        { signal: pending.signal },
      );
      if (!pending.signal.aborted) setResult(data);
    } catch (cause) {
      if (!pending.signal.aborted)
        setError(
          cause instanceof Error
            ? cause.message
            : 'Não foi possível consultar a referência territorial.',
        );
    } finally {
      if (!pending.signal.aborted) setLoading(false);
    }
  }
  return (
    <section className="panel mt-4" aria-label="Consulta territorial ANEEL">
      <SectionHeading
        eyebrow="REFERÊNCIA / LOCALIZAÇÃO"
        title="Distribuidoras no ponto informado"
        description="Consulta opcional à coleta local de polígonos oficiais ANEEL/SIGEL. Use coordenadas SIRGAS2000 (EPSG4674); não há conversão automática de outro referencial. A busca não seleciona distribuidora e suas coordenadas não são salvas no projeto."
      />
      <MunicipalityStudy />
      <form
        className="mt-3 grid gap-3 md:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void lookup();
        }}
      >
        <label>
          Latitude SIRGAS2000 (graus)
          <input
            type="number"
            step="any"
            min="-90"
            max="90"
            required
            value={latitude}
            onChange={(e) => {
              clear();
              setLatitude(e.target.value);
            }}
          />
        </label>
        <label>
          Longitude SIRGAS2000 (graus)
          <input
            type="number"
            step="any"
            min="-180"
            max="180"
            required
            value={longitude}
            onChange={(e) => {
              clear();
              setLongitude(e.target.value);
            }}
          />
        </label>
        <button type="submit" className="btn self-end" disabled={loading}>
          {loading ? 'Consultando referência…' : 'Consultar distribuidoras no ponto'}
        </button>
      </form>
      {error && (
        <p role="alert" className="mt-3">
          {error}
        </p>
      )}
      {result && (
        <div className="mt-4" role="status">
          <p>{result.reason}</p>
          <p className="mt-2 text-xs muted">
            {result.notice} Geometrias cartográficas simplificadas não substituem levantamento
            cadastral ou confirmação do endereço.
          </p>
          {result.consulted_on && (
            <p className="mt-2 text-xs">
              Coleta consultada em {formatDate(result.consulted_on)}; essa data não comprova
              atualização dos limites ou contratos.
            </p>
          )}
          <ul className="mt-3 space-y-3">
            {result.candidates.map((candidate) => (
              <li key={candidate.object_id}>
                <p className="font-semibold">
                  {candidate.acronym} · {candidate.state}
                </p>
                <p>
                  {candidate.name} · CNPJ {candidate.cnpj}
                </p>
                <p>
                  {candidate.relation === 'boundary'
                    ? 'Ponto na fronteira da feição; atendimento ambíguo'
                    : 'Ponto no interior da feição'}{' '}
                  · {periods[candidate.temporal_status]}
                </p>
                <p>
                  Período registrado: {candidate.recorded_start ?? 'início não informado'} a{' '}
                  {candidate.recorded_end ?? 'fim não informado'}. Ato: {candidate.legal_act}
                </p>
              </li>
            ))}
          </ul>
          <a
            className="mt-3 inline-block text-sm"
            href={safeReferenceUrl(result.source)}
            target="_blank"
            rel="noreferrer"
          >
            Abrir fonte oficial ANEEL/SIGEL
          </a>
        </div>
      )}
    </section>
  );
}
