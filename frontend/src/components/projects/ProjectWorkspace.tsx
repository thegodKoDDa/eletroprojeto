'use client';

import { useEffect, useId, useState } from 'react';
import { formatDate } from '@/lib/format';
import { request, type ProjectSummary as Project } from '@/lib/api';
import { PageHeading } from '@/components/ui/PageHeading';
import { Feedback } from '@/components/ui/Feedback';
import { Pagination } from '@/components/ui/Pagination';
import { WorkspaceIcon } from '@/components/layout/WorkspaceIcon';

type Props = {
  archived: boolean;
  busy: boolean;
  revision: number;
  onOpen: (project: Project) => void | boolean | Promise<void | boolean>;
  onDuplicate: (project: Project) => void;
  onDelete: (project: Project) => void;
  onRestore: (project: Project) => void;
  onPurge: (project: Project) => void;
  onNew: () => void;
};

export function ProjectWorkspace({
  archived,
  busy,
  revision,
  onOpen,
  onDuplicate,
  onDelete,
  onRestore,
  onPurge,
  onNew,
}: Props) {
  const [filters, setFilters] = useState({ query: '', sort: 'recent', offset: 0 });
  const [reload, setReload] = useState(0);
  const key = JSON.stringify([archived, filters, revision, reload]);
  const [response, setResponse] = useState<{ key: string; rows: Project[]; error?: string }>();
  const current = response?.key === key;
  const loading = !current;
  const rows = current ? response.rows : [];
  const error = current ? response.error : undefined;
  const titleId = useId();
  const title = archived ? 'Lixeira' : 'Projetos salvos';

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const parameters = new URLSearchParams({
        archived: String(archived),
        limit: '21',
        offset: String(filters.offset),
        q: filters.query,
        sort: filters.sort,
      });
      request<Project[]>(`/projects/summaries?${parameters}`, { signal: controller.signal })
        .then((list) => {
          if (controller.signal.aborted) return;
          // Removing the last item on a page returns to the preceding page.
          if (!list.length && filters.offset > 0) {
            setFilters((old) => ({ ...old, offset: Math.max(0, old.offset - 20) }));
            return;
          }
          setResponse({ key, rows: list });
        })
        .catch((error) => {
          if (!controller.signal.aborted) setResponse({ key, rows: [], error: error.message });
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [archived, filters, key]);

  function search(query: string) {
    setFilters((old) => ({ ...old, query, offset: 0 }));
  }

  return (
    <section aria-labelledby={titleId} className="workspace-library">
      <header className="page-header">
        <PageHeading
          id={titleId}
          title={title}
          eyebrow="ESPAÇO DE TRABALHO"
          description={
            archived
              ? 'Recupere projetos excluídos ou remova-os definitivamente, junto com seu histórico.'
              : 'Encontre um projeto para continuar ou organize os estudos que você já salvou.'
          }
        />
        <button
          className="btn"
          disabled={busy || loading}
          onClick={() => setReload((value) => value + 1)}
        >
          Atualizar lista
        </button>
      </header>
      <div className="panel">
        <div className="workspace-filters">
          <label>
            Pesquisar projetos
            <input
              type="search"
              value={filters.query}
              placeholder="Nome do projeto ou município"
              onChange={(event) => search(event.target.value)}
            />
          </label>
          <label>
            Ordenar projetos
            <select
              value={filters.sort}
              onChange={(event) =>
                setFilters((old) => ({ ...old, sort: event.target.value, offset: 0 }))
              }
            >
              <option value="recent">Mais recentes</option>
              <option value="name">Nome</option>
            </select>
          </label>
        </div>
        {loading && (
          <p role="status" className="workspace-list-status muted">
            Carregando projetos…
          </p>
        )}
        {error && (
          <Feedback tone="error">
            <p>{error}</p>
            <button
              className="btn mt-4"
              disabled={busy}
              onClick={() => setReload((value) => value + 1)}
            >
              Tentar carregar novamente
            </button>
          </Feedback>
        )}
        <div className="workspace-list" aria-busy={loading}>
          {rows.slice(0, 20).map((project) => (
            <article key={project.id} className="workspace-row">
              <div className="min-w-0 flex-1">
                {archived ? (
                  <h2 className="workspace-project-name">{project.name}</h2>
                ) : (
                  <button
                    disabled={busy || loading}
                    onClick={() => onOpen(project)}
                    className="workspace-project-open"
                    title={`Abrir ${project.name}`}
                  >
                    {project.name}
                  </button>
                )}
                <p className="mt-1 text-sm muted">
                  {project.municipality || 'Município não informado'}
                </p>
                <p className="mt-2 text-xs muted">
                  {archived ? 'Excluído em' : 'Atualizado em'}{' '}
                  {formatDate(archived ? project.deleted_at : project.updated_at)} · Brasília
                </p>
              </div>
              <div className="workspace-row-actions">
                {archived ? (
                  <>
                    <button
                      className="btn"
                      disabled={busy || loading}
                      onClick={() => onRestore(project)}
                      aria-label={`Restaurar ${project.name}`}
                    >
                      Restaurar
                    </button>
                    <button
                      className="btn subtle danger"
                      disabled={busy || loading}
                      onClick={() => onPurge(project)}
                      aria-label={`Excluir definitivamente ${project.name}`}
                    >
                      Excluir definitivamente
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className="btn subtle"
                      disabled={busy || loading}
                      onClick={() => onDuplicate(project)}
                      aria-label={`Duplicar ${project.name}`}
                    >
                      Duplicar
                    </button>
                    <button
                      className="btn subtle danger"
                      disabled={busy || loading}
                      onClick={() => onDelete(project)}
                      aria-label={`Excluir ${project.name}`}
                    >
                      Mover para lixeira
                    </button>
                  </>
                )}
              </div>
            </article>
          ))}
        </div>
        {!loading && !error && !rows.length && (
          <div className="workspace-empty">
            <span className="workspace-empty-icon">
              <WorkspaceIcon name={archived ? 'trash' : 'library'} />
            </span>
            <h2 className="mt-4 text-lg font-semibold">
              {filters.query.trim()
                ? 'Nenhum projeto encontrado'
                : archived
                  ? 'Lixeira vazia'
                  : 'Você ainda não tem projetos salvos'}
            </h2>
            <p className="mt-2 text-sm muted">
              {filters.query.trim()
                ? 'Tente outro nome ou município, ou limpe a pesquisa.'
                : archived
                  ? 'Os projetos que você excluir aparecerão aqui.'
                  : 'Crie seu primeiro projeto para estimar o consumo da sua casa.'}
            </p>
            {filters.query ? (
              <button className="btn mt-5" disabled={busy} onClick={() => search('')}>
                Limpar pesquisa
              </button>
            ) : (
              !archived && (
                <button className="btn primary mt-5" disabled={busy} onClick={onNew}>
                  Criar novo projeto
                </button>
              )
            )}
          </div>
        )}
        <Pagination
          label={archived ? 'Paginação da lixeira' : 'Paginação dos projetos'}
          offset={filters.offset}
          pageSize={20}
          hasNext={!error && rows.length > 20}
          busy={busy || loading || !!error}
          onPrevious={() => setFilters((old) => ({ ...old, offset: Math.max(0, old.offset - 20) }))}
          onNext={() => setFilters((old) => ({ ...old, offset: old.offset + 20 }))}
        />
      </div>
    </section>
  );
}
