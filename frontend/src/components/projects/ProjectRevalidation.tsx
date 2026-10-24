'use client';

import { useEffect, useRef } from 'react';
import type { components } from '@/lib/api.generated';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { format } from '@/lib/format';

type Review = components['schemas']['ProjectRevalidation'];

export function ProjectRevalidation({
  review,
  busy,
  onRegister,
  onClose,
}: {
  review: Review;
  busy: boolean;
  onRegister: () => void;
  onClose: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), []);
  const result = review.current_result;
  return (
    <section className="panel mb-5" aria-labelledby="revalidation-heading">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SectionHeading
          eyebrow="REVISÃO OPCIONAL"
          id="revalidation-heading"
          headingRef={heading}
          tabIndex={-1}
          title="Revisão das referências do projeto"
        />
        <button className="btn subtle" disabled={busy} onClick={onClose}>
          Fechar revisão
        </button>
      </div>
      <p className="mt-3 text-sm">
        {review.requires_revalidation
          ? 'O motor ou as referências mudaram desde o último cálculo registrado.'
          : 'O cálculo registrado utiliza o motor e as referências atuais.'}
      </p>
      <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="muted">Motor registrado → atual</dt>
          <dd>
            {review.previous_engine_version ?? 'Não registrado'} → {result.engine_version}
          </dd>
        </div>
        <div>
          <dt className="muted">Prévia da potência instalada</dt>
          <dd>
            {format(result.installed_power.value)} W
            {(result.unknown_load_ids?.length ?? 0) > 0 ? ' · subtotal conhecido' : ''}
          </dd>
        </div>
      </dl>
      <p className="mt-3 text-xs muted">
        A prévia usa os dados salvos da versão {review.project_version}. Registrar a revisão cria
        uma nova versão e preserva os resultados anteriores e os valores manuais. Os limites e as
        pendências técnicas continuam aplicáveis.
      </p>
      <details className="mt-3 text-xs muted">
        <summary>Identificação das referências</summary>
        <p className="mt-2 break-all">Registrada: {review.previous_registry_version}</p>
        <p className="mt-2 break-all">Atual: {review.current_registry_version}</p>
        <p className="mt-2">{review.notice}</p>
      </details>
      {review.requires_revalidation && (
        <button className="btn mt-4" disabled={busy} onClick={onRegister}>
          Registrar revalidação com os dados salvos
        </button>
      )}
    </section>
  );
}
