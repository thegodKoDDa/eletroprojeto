'use client';
import { useExperience } from '@/lib/experience';
import { WorkspaceIcon } from '@/components/layout/WorkspaceIcon';

type Props = {
  busy: boolean;
  writing?: boolean;
  projectName?: string;
  onNew: () => void;
  onLibrary: () => void;
  onTrash: () => void;
  onContinue: () => void;
  onKnowledge: () => void;
};

export function WorkspaceHome({
  busy,
  writing = false,
  projectName,
  onNew,
  onLibrary,
  onTrash,
  onContinue,
  onKnowledge,
}: Props) {
  const { profile } = useExperience();
  const guided = profile !== 'explore';
  const professional = profile === 'professional';
  return (
    <section aria-labelledby="workspace-title" className="workspace-home">
      <header className="workspace-welcome">
        <p className="eyebrow">ESPAÇO DE TRABALHO</p>
        <h1
          id="workspace-title"
          data-workspace-heading
          tabIndex={-1}
          className="text-3xl font-semibold tracking-tight sm:text-4xl"
        >
          {professional
            ? 'Um espaço para o seu próximo estudo.'
            : profile === 'beginner'
              ? 'Vamos entender o consumo da sua casa?'
              : 'Seu próximo projeto começa aqui.'}
        </h1>
        <p className="mt-4 max-w-xl text-sm leading-6 muted">
          {professional
            ? 'Organize cargas, consulte a memória de cálculo e aprofunde as verificações técnicas. Comece um estudo ou retome um projeto salvo.'
            : profile === 'beginner'
              ? 'Adicione os aparelhos, conte como usa cada um e acompanhe a estimativa mensal. Os dados essenciais ficam em destaque para ajudar você a começar.'
              : 'Estime o consumo de energia da sua casa, pronta ou em construção. Comece um novo estudo ou continue um projeto salvo.'}
        </p>
      </header>
      <div className="workspace-options">
        <button
          className="workspace-option workspace-option-primary"
          disabled={busy || writing}
          onClick={onNew}
        >
          <span className="workspace-option-icon" aria-hidden="true">
            <WorkspaceIcon name="new" />
          </span>
          <span className="text-lg font-semibold">Criar novo projeto</span>
          <span className="text-sm leading-6 muted">
            Cadastre a residência, os ambientes e os equipamentos.
          </span>
          <span className="workspace-option-link">
            Começar <span aria-hidden="true">→</span>
          </span>
        </button>
        <button className="workspace-option" disabled={busy} onClick={onLibrary}>
          <span className="workspace-option-icon" aria-hidden="true">
            <WorkspaceIcon name="library" />
          </span>
          <span className="text-lg font-semibold">Abrir projetos salvos</span>
          <span className="text-sm leading-6 muted">
            Encontre seus projetos e continue de onde parou.
          </span>
          <span className="workspace-option-link">
            Ver biblioteca <span aria-hidden="true">→</span>
          </span>
        </button>
        <button
          className="workspace-option"
          disabled={busy}
          onClick={guided ? onKnowledge : onTrash}
        >
          <span className="workspace-option-icon" aria-hidden="true">
            <WorkspaceIcon name={guided ? 'project' : 'trash'} />
          </span>
          <span className="text-lg font-semibold">
            {guided ? 'Consultar biblioteca técnica' : 'Acessar lixeira'}
          </span>
          <span className="text-sm leading-6 muted">
            {guided
              ? 'Guias, modelos e fontes de apoio. Consulte a origem e o estado de revisão de cada referência.'
              : 'Restaure projetos excluídos ou remova-os definitivamente.'}
          </span>
          <span className="workspace-option-link">
            {guided ? 'Consultar referências' : 'Ver lixeira'} <span aria-hidden="true">→</span>
          </span>
        </button>
      </div>
      {projectName && (
        <div className="panel mt-6 flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="eyebrow">EDIÇÃO EM ANDAMENTO</p>
            <p className="break-words text-sm">{projectName}</p>
            <p className="mt-2 text-xs muted">Sua edição foi mantida nesta aba.</p>
          </div>
          <button className="btn" disabled={busy} onClick={onContinue}>
            Continuar edição
          </button>
        </div>
      )}
      <p className="mt-8 text-xs leading-6 muted">
        Cadastre os aparelhos e seus horários de uso para ter uma estimativa mensal. Você pode
        ajustar o estudo sempre que precisar.
      </p>
    </section>
  );
}
