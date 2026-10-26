'use client';
import { useEffect, useRef } from 'react';
import { WorkspaceIcon } from './WorkspaceIcon';

export function ProjectActions({
  saved,
  busy,
  saving,
  exporting,
  canExport,
  canExportPdf,
  onNew,
  onSave,
  onSaveAs,
  onPdf,
  onJson,
  onDelete,
  onCheck,
  hideNew = false,
}: {
  hideNew?: boolean;
  saved: boolean;
  busy: boolean;
  saving: boolean;
  exporting: boolean;
  canExport: boolean;
  canExportPdf: boolean;
  onNew: () => void;
  onSave: () => void;
  onSaveAs: () => void;
  onPdf: () => void;
  onJson: () => void;
  onDelete: () => void;
  onCheck: () => void;
}) {
  const menu = useRef<HTMLDetailsElement>(null);
  const locked = busy || saving || exporting;
  useEffect(() => {
    if (locked && menu.current) menu.current.open = false;
  }, [locked]);
  useEffect(() => {
    function outside(event: PointerEvent) {
      if (
        menu.current?.open &&
        event.target instanceof Node &&
        !menu.current.contains(event.target)
      )
        menu.current.open = false;
    }
    document.addEventListener('pointerdown', outside);
    return () => document.removeEventListener('pointerdown', outside);
  }, []);
  function closeMenu() {
    if (menu.current) menu.current.open = false;
  }
  function run(action: () => void) {
    closeMenu();
    menu.current?.querySelector('summary')?.focus();
    action();
  }
  return (
    <div className="project-actions" aria-label="Ações do projeto">
      <button
        id="save-project"
        className="btn primary"
        disabled={locked}
        onClick={onSave}
        title={locked ? 'Aguarde a operação em andamento.' : 'Salvar as alterações deste projeto.'}
      >
        <WorkspaceIcon name="save" />
        {saving ? 'Salvando…' : 'Salvar projeto'}
      </button>
      <button
        className="btn"
        disabled={locked || !canExportPdf}
        onClick={onPdf}
        title={
          locked
            ? 'Aguarde a operação em andamento.'
            : !canExportPdf
              ? 'Aguarde um cálculo atualizado para exportar.'
              : 'Baixar o relatório do projeto em PDF.'
        }
      >
        <WorkspaceIcon name="download" />
        {exporting ? 'Gerando arquivo…' : 'Exportar PDF'}
      </button>
      <details
        ref={menu}
        className="action-menu"
        onBlur={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget)) closeMenu();
        }}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.preventDefault();
            closeMenu();
            menu.current?.querySelector('summary')?.focus();
          }
        }}
      >
        <summary
          className="btn"
          aria-label="Mais ações do projeto"
          aria-disabled={locked}
          title={locked ? 'Aguarde a operação em andamento.' : 'Outras opções para este projeto.'}
          onClick={(event) => {
            if (locked) event.preventDefault();
          }}
        >
          <span>Mais ações</span>
          <svg
            className="action-menu-chevron"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </summary>
        <div className="action-menu-content">
          {!hideNew && (
            <button disabled={locked} onClick={() => run(onNew)}>
              <WorkspaceIcon name="new" />
              <span>Novo projeto</span>
            </button>
          )}
          {saved && (
            <button disabled={locked} onClick={() => run(onSaveAs)}>
              <WorkspaceIcon name="copy" />
              <span>Salvar como novo</span>
            </button>
          )}
          <button disabled={locked || !canExport} onClick={() => run(onJson)}>
            <WorkspaceIcon name="download" />
            <span>Exportar JSON</span>
          </button>
          {saved && (
            <>
              <button disabled={locked} onClick={() => run(onCheck)}>
                <WorkspaceIcon name="library" />
                <span>Verificar referências</span>
              </button>
              <button className="danger" disabled={locked} onClick={() => run(onDelete)}>
                <WorkspaceIcon name="trash" />
                <span>Mover para lixeira</span>
              </button>
            </>
          )}
        </div>
      </details>
    </div>
  );
}
