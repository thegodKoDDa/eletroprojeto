'use client';
import { WorkspaceIcon, type WorkspaceIconName } from '@/components/layout/WorkspaceIcon';

type Props = {
  active: 'home' | 'project' | 'library' | 'trash' | 'knowledge';
  busy: boolean;
  hasProject: boolean;
  projectName?: string;
  dirty?: boolean;
  onHome: () => void;
  onNew: () => void;
  onProject: () => void;
  onLibrary: () => void;
  onTrash: () => void;
  onKnowledge?: () => void;
};

export function SectionNavigation({
  active,
  busy,
  hasProject,
  projectName,
  dirty,
  onHome,
  onNew,
  onProject,
  onLibrary,
  onTrash,
  onKnowledge,
}: Props) {
  const items = [
    { id: 'home', label: 'Início', icon: 'home', action: onHome },
    { id: 'new', label: 'Novo projeto', icon: 'new', action: onNew },
    { id: 'library', label: 'Projetos salvos', icon: 'library', action: onLibrary },
    { id: 'trash', label: 'Lixeira', icon: 'trash', action: onTrash },
    ...(onKnowledge
      ? [{ id: 'knowledge', label: 'Biblioteca técnica', icon: 'project', action: onKnowledge }]
      : []),
    ...(hasProject
      ? [{ id: 'project', label: 'Projeto em edição', icon: 'project', action: onProject }]
      : []),
  ];
  return (
    <nav aria-label="Espaço de trabalho" className="workspace-navigation">
      {items.map((item) => (
        <button
          key={item.id}
          disabled={busy}
          onClick={item.action}
          data-project={item.id === 'project' || undefined}
          aria-current={active === item.id ? 'page' : undefined}
        >
          <span aria-hidden="true">
            <WorkspaceIcon name={item.icon as WorkspaceIconName} />
          </span>
          <span className="workspace-nav-label">
            <span>{item.label}</span>
            {item.id === 'project' && projectName && (
              <span className="workspace-nav-description" aria-hidden="true">
                {projectName} · {dirty ? 'Não salvo' : 'Salvo'}
              </span>
            )}
          </span>
        </button>
      ))}
    </nav>
  );
}
