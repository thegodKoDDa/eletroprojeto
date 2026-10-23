'use client';
import { useEffect, useRef } from 'react';

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
  const locked = busy || exporting;
  useEffect(() => {
    if (locked && menu.current) menu.current.open = false;
  }, [locked]);
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
      <button className="btn primary" disabled={locked} onClick={onSave}>
        {saving ? 'Salvando…' : 'Salvar projeto'}
      </button>
      <button className="btn" disabled={locked || !canExportPdf} onClick={onPdf}>
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
          onClick={(event) => {
            if (locked) event.preventDefault();
          }}
        >
          Mais ações <span aria-hidden="true">⌄</span>
        </summary>
        <div className="action-menu-content">
          {!hideNew && (
            <button disabled={locked} onClick={() => run(onNew)}>
              Novo projeto
            </button>
          )}
          {saved && (
            <button disabled={locked} onClick={() => run(onSaveAs)}>
              Salvar como novo
            </button>
          )}
          <button disabled={locked || !canExport} onClick={() => run(onJson)}>
            Exportar JSON
          </button>
          {saved && (
            <>
              <button disabled={locked} onClick={() => run(onCheck)}>
                Verificar referências
              </button>
              <button className="text-red-300" disabled={locked} onClick={() => run(onDelete)}>
                Mover para lixeira
              </button>
            </>
          )}
        </div>
      </details>
    </div>
  );
}
