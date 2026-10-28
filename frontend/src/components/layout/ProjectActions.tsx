'use client';
import { useEffect, useRef } from 'react';
import { WorkspaceIcon } from './WorkspaceIcon';

export function ProjectActions({
  saved,
  busy,
  saving,
  automaticSaving = false,
  exporting,
  canExport,
  canExportPdf,
  onNew,
  onSave,
  onSaveAs,
  onPdf,
  onJson,
  onDelete,
  hideNew = false,
}: {
  hideNew?: boolean;
  saved: boolean;
  busy: boolean;
  saving: boolean;
  automaticSaving?: boolean;
  exporting: boolean;
  canExport: boolean;
  canExportPdf: boolean;
  onNew: () => void;
  onSave: () => void;
  onSaveAs: () => void;
  onPdf: () => void;
  onJson: () => void;
  onDelete: () => void;
}) {
  const menu = useRef<HTMLDetailsElement>(null);
  const locked = busy || saving || exporting;
  const menuLocked = (busy && !automaticSaving) || exporting;
  const exportLocked = (busy && !automaticSaving) || exporting;
  useEffect(() => {
    if (menuLocked && menu.current) menu.current.open = false;
  }, [menuLocked]);
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
  function toggleMenu() {
    const element = menu.current;
    if (!element || menuLocked) return;
    if (element.open) {
      closeMenu();
      return;
    }
    element.style.removeProperty('--action-menu-height');
    element.dataset.placement = 'down';
    element.open = true;
    const summary = element.querySelector('summary')!.getBoundingClientRect();
    const height = element.querySelector('.action-menu-content')!.getBoundingClientRect().height;
    const above = summary.top - 12;
    const below = window.innerHeight - summary.bottom - 12;
    const up = below < height && above > below;
    element.dataset.placement = up ? 'up' : 'down';
    element.style.setProperty('--action-menu-height', `${Math.max(44, up ? above : below)}px`);
  }
  function run(action: () => void, readOnly = false) {
    if (readOnly ? exportLocked : locked) return;
    closeMenu();
    menu.current?.querySelector('summary')?.focus({ preventScroll: true });
    action();
  }
  return (
    <div className="project-actions" aria-label="Ações do projeto">
      <button
        id="save-project"
        className="btn primary"
        disabled={locked && !automaticSaving}
        aria-disabled={locked}
        aria-busy={saving}
        onClick={() => {
          if (!locked) onSave();
        }}
        title={locked ? 'Aguarde a operação em andamento.' : 'Salvar as alterações deste projeto.'}
      >
        <WorkspaceIcon name="save" />
        {saving && !automaticSaving ? 'Salvando…' : 'Salvar projeto'}
      </button>
      <button
        className="btn"
        disabled={exportLocked || !canExportPdf}
        onClick={onPdf}
        title={
          exportLocked
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
            menu.current?.querySelector('summary')?.focus({ preventScroll: true });
          }
        }}
      >
        <summary
          className="btn"
          aria-label="Mais ações do projeto"
          aria-disabled={menuLocked}
          title={
            menuLocked ? 'Aguarde a operação em andamento.' : 'Outras opções para este projeto.'
          }
          onClick={(event) => {
            event.preventDefault();
            toggleMenu();
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
            <button
              disabled={locked && !automaticSaving}
              aria-disabled={locked}
              onClick={() => run(onNew)}
            >
              <WorkspaceIcon name="new" />
              <span>Novo projeto</span>
            </button>
          )}
          {saved && (
            <button
              disabled={locked && !automaticSaving}
              aria-disabled={locked}
              onClick={() => run(onSaveAs)}
            >
              <WorkspaceIcon name="copy" />
              <span>Salvar como novo</span>
            </button>
          )}
          <button disabled={exportLocked || !canExport} onClick={() => run(onJson, true)}>
            <WorkspaceIcon name="download" />
            <span>Exportar JSON</span>
          </button>
          {saved && (
            <>
              <button
                className="danger"
                disabled={locked && !automaticSaving}
                aria-disabled={locked}
                onClick={() => run(onDelete)}
              >
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
