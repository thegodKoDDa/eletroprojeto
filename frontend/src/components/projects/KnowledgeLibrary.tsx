'use client';
import { useEffect, useRef, useState } from 'react';
import type { components } from '@/lib/api.generated';
import { API, request } from '@/lib/api';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { PageHeading } from '@/components/ui/PageHeading';
import { Feedback } from '@/components/ui/Feedback';
import { Pagination } from '@/components/ui/Pagination';
import { safeReferenceUrl } from '@/lib/safe-url';

type Document = components['schemas']['KnowledgeDocument'];
type Stats = components['schemas']['KnowledgeStats'];
type Results = components['schemas']['KnowledgeSearch'];
type Source = components['schemas']['KnowledgeSource'];
type Page = components['schemas']['KnowledgePage'];
const kinds: Record<string, string> = {
  guide: 'Guias de estudo',
  template: 'Modelos e checklists',
  diagram: 'Diagramas didáticos',
  pdf: 'PDFs de referência',
};
const states: Record<string, string> = {
  educational: 'Educacional',
  pending_review: 'Revisão pendente',
  historical: 'Histórico',
  draft: 'Minuta',
  future_effective_candidate: 'Vigência futura a conferir',
  out_of_scope: 'Fora do escopo residencial',
};

function InlineReference({ text }: { text: string }) {
  return text
    .split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g)
    .map((part, index) => {
      const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
      if (link && safeReferenceUrl(link[2]))
        return (
          <a
            key={index}
            className="underline"
            href={safeReferenceUrl(link[2])}
            target="_blank"
            rel="noreferrer"
          >
            {link[1]}
          </a>
        );
      if (part.startsWith('**') && part.endsWith('**'))
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      if (part.startsWith('`') && part.endsWith('`'))
        return <code key={index}>{part.slice(1, -1)}</code>;
      return part;
    });
}

function StudyText({ body }: { body: string }) {
  return (
    <div className="knowledge-markdown">
      {body.split(/\n\s*\n/).map((block, index) => {
        if (/^#{1,6} /.test(block))
          return (
            <h4 key={index} className="font-semibold">
              <InlineReference text={block.replace(/^#{1,6} /, '')} />
            </h4>
          );
        const lines = block.split('\n');
        if (lines.every((line) => /^[-*] /.test(line)))
          return (
            <ul key={index}>
              {lines.map((line, item) => (
                <li key={item}>
                  <InlineReference text={line.slice(2)} />
                </li>
              ))}
            </ul>
          );
        if (lines.every((line) => /^\d+\. /.test(line)))
          return (
            <ol key={index}>
              {lines.map((line, item) => (
                <li key={item}>
                  <InlineReference text={line.replace(/^\d+\. /, '')} />
                </li>
              ))}
            </ol>
          );
        return (
          <p key={index}>
            <InlineReference text={block} />
          </p>
        );
      })}
    </div>
  );
}

function DocumentReader({ document, onClose }: { document: Document; onClose: () => void }) {
  const [pageState, setPageState] = useState<{ key: string; pages?: Page[]; error?: string }>();
  const [offset, setOffset] = useState(0);
  const [pageQuery, setPageQuery] = useState('');
  const [attempt, setAttempt] = useState(0);
  const pageKey = JSON.stringify([document.id, offset, pageQuery, attempt]);
  const pages = pageState?.key === pageKey ? pageState.pages : undefined;
  const error = pageState?.key === pageKey ? pageState.error : undefined;
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, [document.id]);
  useEffect(() => {
    const controller = new AbortController();
    request<Page[]>(
      `/knowledge/documents/${document.id}/pages?${new URLSearchParams({ offset: String(offset), limit: '5', q: pageQuery })}`,
      {
        signal: controller.signal,
      },
    )
      .then((value) => {
        if (!controller.signal.aborted) setPageState({ key: pageKey, pages: value });
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setPageState({ key: pageKey, error: reason.message });
      });
    return () => controller.abort();
  }, [document.id, offset, pageQuery, pageKey]);
  return (
    <section className="panel knowledge-reader" aria-labelledby="reference-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionHeading
          eyebrow="LEITURA / REFERÊNCIA"
          id="reference-title"
          headingRef={heading}
          tabIndex={-1}
          title={document.title}
        />
        <button className="btn subtle" onClick={onClose}>
          Fechar leitura
        </button>
      </div>
      <p className="mt-2 text-xs muted">
        {states[document.review_state] ?? document.review_state} · {document.page_count} páginas ·{' '}
        {document.text_pages} com texto extraído
      </p>
      <p className="mt-2 text-sm muted">{document.provenance.validation}</p>
      {document.text_pages < document.page_count && (
        <p className="mt-2 text-sm muted">
          Há páginas sem texto extraível. Consulte as imagens no arquivo original; a busca não cobre
          essas páginas.
        </p>
      )}
      <a
        className="btn mt-3"
        href={`${API}/knowledge/documents/${document.id}/file`}
        target="_blank"
        rel="noreferrer"
      >
        {document.kind === 'pdf' ? 'Abrir PDF original' : 'Baixar arquivo original'}
      </a>
      {document.kind === 'diagram' && (
        <img
          className="knowledge-diagram"
          src={`${API}/knowledge/documents/${document.id}/file`}
          alt={`Diagrama didático: ${document.title}`}
        />
      )}
      {document.provenance.urls.length > 0 && (
        <details className="mt-3">
          <summary>Fontes e contexto</summary>
          <p className="mt-2 text-xs muted">{document.provenance.territory}</p>
          <p className="mt-2 text-xs muted">
            Grupos: {document.provenance.groups.join(', ') || 'não informados'} · UF de catalogação:{' '}
            {document.provenance.states_catalogued.join(', ') || 'não informada'}
          </p>
          <ul className="mt-2 space-y-2 text-xs break-words">
            {document.provenance.urls.map(
              (url) =>
                safeReferenceUrl(url) && (
                  <li key={url}>
                    <a
                      className="underline"
                      href={safeReferenceUrl(url)!}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {url}
                    </a>
                  </li>
                ),
            )}
          </ul>
          <p className="mt-2 text-xs muted break-all">SHA-256: {document.id}</p>
        </details>
      )}
      <label className="mt-3 block">
        Buscar páginas nesta referência
        <input
          type="search"
          value={pageQuery}
          maxLength={160}
          onChange={(event) => {
            setPageQuery(event.target.value);
            setOffset(0);
          }}
        />
      </label>
      {pages?.length === 0 && (
        <p className="mt-3 muted">Nenhuma página encontrada para este termo.</p>
      )}
      {error && (
        <Feedback tone="error" className="mt-3">
          <p>{error}</p>
          <button
            className="btn subtle mt-3"
            onClick={() => {
              setAttempt((value) => value + 1);
              heading.current?.focus();
            }}
          >
            Tentar leitura novamente
          </button>
        </Feedback>
      )}
      {!pages && !error && (
        <p role="status" className="mt-3 muted">
          Carregando leitura…
        </p>
      )}
      {pages?.map((page) => (
        <article key={page.number} className="knowledge-page">
          <h3 className="eyebrow">
            {document.kind === 'pdf' ? `Página ${page.number}` : 'Conteúdo de estudo'}
          </h3>
          {page.extraction_method === 'ocr_unreviewed' && (
            <p className="mt-2 text-xs muted">
              Texto reconhecido automaticamente por OCR (confiança média{' '}
              {page.ocr_confidence ?? '—'}%). Confira números, símbolos e tabelas no original.
            </p>
          )}
          {page.extraction_method.startsWith('blank') && (
            <p className="mt-2 text-xs muted">
              {page.extraction_note || 'Página identificada como vazia.'}
            </p>
          )}
          <div className="knowledge-text">
            {['guide', 'template'].includes(document.kind) ? (
              <StudyText body={page.body} />
            ) : (
              page.body || 'Página vazia ou sem texto. Consulte a classificação e o original.'
            )}
          </div>
        </article>
      ))}
      <Pagination
        label="Páginas da referência"
        caption={pages ? `${pages.length} página(s) carregada(s)` : 'Leitura'}
        offset={offset}
        pageSize={5}
        hasNext={!!pages && pages.length >= 5 && (!!pageQuery || offset + 5 < document.page_count)}
        busy={!pages || !!error}
        onPrevious={() => setOffset(Math.max(0, offset - 5))}
        onNext={() => setOffset(offset + 5)}
        previousLabel="Páginas anteriores"
        nextLabel="Próximas páginas"
      />
    </section>
  );
}

function SourceRegistry() {
  const [opened, setOpened] = useState(false);
  const [offset, setOffset] = useState(0);
  const [outcome, setOutcome] = useState('falha_download');
  const [attempt, setAttempt] = useState(0);
  const sourceKey = JSON.stringify([offset, outcome, attempt]);
  const [rows, setRows] = useState<{ key: string; items?: Source[]; error?: string }>();
  const items = rows?.key === sourceKey ? rows.items : undefined;
  const error = rows?.key === sourceKey ? rows.error : undefined;
  useEffect(() => {
    if (!opened) return;
    const controller = new AbortController();
    request<Source[]>(
      `/knowledge/sources?outcome=${encodeURIComponent(outcome)}&limit=20&offset=${offset}`,
      {
        signal: controller.signal,
      },
    )
      .then((value) => {
        if (!controller.signal.aborted) setRows({ key: sourceKey, items: value });
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setRows({ key: sourceKey, error: reason.message });
      });
    return () => controller.abort();
  }, [opened, offset, outcome, sourceKey]);
  return (
    <details className="mt-4" onToggle={(event) => setOpened(event.currentTarget.open)}>
      <summary>Fontes e situação dos downloads</summary>
      <p className="mt-2 text-xs muted">
        A lista distingue documentos recebidos e tentativas sem arquivo disponível. A consulta não
        tenta baixar links novamente.
      </p>
      <label className="mt-3 block">
        Situação da coleta
        <select
          value={outcome}
          onChange={(event) => {
            setOutcome(event.target.value);
            setOffset(0);
          }}
        >
          <option value="falha_download">Falha de download</option>
          <option value="">Todos os registros</option>
          <option value="nao_e_pdf">Resposta sem PDF</option>
          <option value="pdf_invalido_ou_cifrado">PDF inválido ou cifrado na coleta</option>
          <option value="pdf_validado">PDF recebido na coleta</option>
          <option value="discarded_out_of_scope">
            Descartado por falta de utilidade no escopo
          </option>
        </select>
      </label>
      {error && (
        <Feedback tone="error" className="mt-3">
          <p>{error}</p>
          <button className="btn subtle mt-3" onClick={() => setAttempt((value) => value + 1)}>
            Tentar fontes novamente
          </button>
        </Feedback>
      )}
      {opened && !items && !error && <p role="status">Consultando fontes…</p>}
      <ul className="mt-2 space-y-3 text-sm">
        {items?.map((source) => (
          <li key={source.id} className="break-words">
            <span>{source.title}</span>
            {safeReferenceUrl(source.url) && (
              <a
                className="ml-2 underline"
                href={safeReferenceUrl(source.url)}
                target="_blank"
                rel="noreferrer"
              >
                Consultar origem
              </a>
            )}
          </li>
        ))}
      </ul>
      {items?.length === 0 && <p className="mt-2 text-sm muted">Nenhum registro nesta página.</p>}
      <Pagination
        label="Paginação das fontes"
        offset={offset}
        pageSize={20}
        hasNext={!!items && items.length >= 20}
        busy={!items || !!error}
        onPrevious={() => setOffset(Math.max(0, offset - 20))}
        onNext={() => setOffset(offset + 20)}
        previousLabel="Fontes anteriores"
        nextLabel="Próximas fontes"
      />
    </details>
  );
}

export function KnowledgeLibrary() {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('');
  const [state, setState] = useState('');
  const [offset, setOffset] = useState(0);
  const [stats, setStats] = useState<Stats>();
  const [resultState, setResultState] = useState<{
    key: string;
    results?: Results;
    error?: string;
  }>();
  const [selected, setSelected] = useState<Document & { queryKey: string }>();
  const [attempt, setAttempt] = useState(0);
  const queryKey = JSON.stringify([query, kind, state, offset, attempt]);
  const results = resultState && resultState.key === queryKey ? resultState.results : undefined;
  const error = resultState && resultState.key === queryKey ? resultState.error : undefined;
  useEffect(() => {
    const controller = new AbortController();
    request<Stats>('/knowledge/stats', { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setStats(value);
      })
      .catch(() => {});
    return () => controller.abort();
  }, [attempt]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const params = new URLSearchParams({ q: query, kind, state, offset: String(offset) });
      request<Results>(`/knowledge/documents?${params}`, { signal: controller.signal })
        .then((value) => {
          if (!controller.signal.aborted) setResultState({ key: queryKey, results: value });
        })
        .catch((reason) => {
          if (!controller.signal.aborted) setResultState({ key: queryKey, error: reason.message });
        });
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, kind, state, offset, attempt, queryKey]);
  return (
    <section className="workspace-library" aria-labelledby="knowledge-heading">
      <header className="page-header">
        <PageHeading
          id="knowledge-heading"
          title="Biblioteca técnica"
          eyebrow="CONSULTA / REFERÊNCIAS"
          description="Guias, modelos, diagramas e documentos do acervo local."
        />
      </header>
      <p className="panel text-sm muted">
        Acervo de consulta. Importar documentos não valida vigência, aplicabilidade territorial ou
        regras de cálculo. Exemplos didáticos não dimensionam uma instalação.
      </p>
      {stats && (
        <p className="mt-3 text-xs muted">
          {stats.documents} documentos · {stats.pages} páginas · {stats.text_pages} páginas com
          texto extraído · {stats.sources} registros de fontes
        </p>
      )}
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <label>
          Buscar no conteúdo e nas fontes
          <input
            type="search"
            value={query}
            maxLength={160}
            placeholder="Ex.: chuveiro, NDU, aterramento"
            onChange={(e) => {
              setQuery(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <label>
          Tipo de material
          <select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Todos os tipos</option>
            {Object.entries(kinds).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Estado da referência
          <select
            value={state}
            onChange={(e) => {
              setState(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Todos os estados</option>
            {Object.entries(states).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <Feedback tone="error" className="mt-4">
          <p>{error}</p>
          <button className="btn mt-2" onClick={() => setAttempt(attempt + 1)}>
            Tentar consulta novamente
          </button>
        </Feedback>
      )}
      {!results && !error && (
        <p role="status" className="mt-4 muted">
          Consultando acervo…
        </p>
      )}
      {results && (
        <>
          <div className="mt-4 space-y-2" aria-label="Referências encontradas">
            {results.items.map((document) => (
              <button
                key={document.id}
                className="knowledge-result"
                onClick={() => setSelected({ ...document, queryKey })}
                aria-pressed={selected?.id === document.id}
              >
                <span className="font-semibold break-words">{document.title}</span>
                <span className="text-xs muted">
                  {kinds[document.kind]} · {states[document.review_state]} · {document.page_count}{' '}
                  páginas
                </span>
              </button>
            ))}
          </div>
          {results.items.length === 0 && (
            <p className="mt-4 muted">
              Nenhuma referência encontrada. Tente outro termo ou filtro.
            </p>
          )}
          <Pagination
            label="Paginação do acervo"
            offset={offset}
            pageSize={20}
            hasNext={results.next_offset !== null}
            onPrevious={() => setOffset(Math.max(0, offset - 20))}
            onNext={() => setOffset(results.next_offset ?? offset)}
            previousLabel="Anteriores"
            nextLabel="Próximas"
          />
        </>
      )}
      <SourceRegistry />
      {selected && selected.queryKey === queryKey && (
        <DocumentReader
          key={selected.id}
          document={selected}
          onClose={() => setSelected(undefined)}
        />
      )}
    </section>
  );
}
