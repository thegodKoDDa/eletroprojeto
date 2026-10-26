'use client';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  request,
  requestReport,
  projectInputs,
  APIError,
  type ProjectInput,
  type Project,
  type Environment,
  type Load,
  type CatalogItem,
} from '@/lib/api';
import { duplicateEnvironment, removeProjectLoads } from '@/lib/environments';
import { useWorkspaceResources } from '@/lib/use-workspace-resources';
import { ProjectRevalidation } from '@/components/projects/ProjectRevalidation';
import { draftKey, readDrafts, writeDraft, type Draft } from '@/lib/drafts';
import { ExperienceBoundary, ExperienceSwitcher } from '@/components/projects/ExperienceBoundary';
import { ExperienceGuide } from '@/components/projects/ExperienceGuide';
import { useExperience } from '@/lib/experience';
import { AccessBoundary } from '@/components/projects/AccessBoundary';
import { WorkspaceIcon } from '@/components/layout/WorkspaceIcon';
import { useCalculation } from '@/lib/use-calculation';
import { PageHeading } from '@/components/ui/PageHeading';
import { Feedback, type FeedbackTone } from '@/components/ui/Feedback';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { DemandReview } from '@/components/calculations/DemandReview';
import { EquipmentEditor } from '@/components/equipment/EquipmentEditor';
import { Field, RequirementsContext, CalculationScopeContext } from '@/components/ui/Field';
import type { components } from '@/lib/api.generated';
import { RoomEquipmentPicker } from '@/components/equipment/RoomEquipmentPicker';
import { SectionNavigation } from '@/components/projects/SectionNavigation';
import { TerritoryStudy } from '@/components/projects/TerritoryStudy';
import { BathroomStudy } from '@/components/projects/BathroomStudy';
import { CircuitStudy } from '@/components/projects/CircuitStudy';
import { KnowledgeLibrary } from '@/components/projects/KnowledgeLibrary';
import { WorkspaceHome } from '@/components/projects/WorkspaceHome';
import { ProjectWorkspace } from '@/components/projects/ProjectWorkspace';
import { CalculationNotices, focusField } from '@/components/calculations-notices';
import { ProjectActions } from '@/components/layout/ProjectActions';
import { ResultsPanel } from '@/components/calculations/ResultsPanel';
import { format, formatDate } from '@/lib/format';
import { exportFilename } from '@/lib/export';
import { APP_VERSION } from '@/lib/version';
import { newLoad, selectionCatalog } from '@/lib/equipment';

const initial = (): ProjectInput => ({
  analysis_scope: 'installed',
  name: 'Novo projeto residencial',
  municipality: '',
  state: 'SP',
  utility: 'unconfirmed',
  residence_type: 'Casa',
  built_area_m2: null,
  floors: 1,
  reference_voltage_v: null,
  notes: '',
  environments: [],
});
const environmentTypes = {
  living: 'Sala',
  bedroom: 'Quarto',
  kitchen: 'Cozinha',
  bathroom: 'Banheiro',
  laundry: 'Lavanderia',
  garage: 'Garagem',
  corridor: 'Corredor',
  outdoor: 'Área externa',
  office: 'Escritório',
  other: 'Outro',
};
type Template = CatalogItem;
const searchText = (value: string) =>
  value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLocaleLowerCase('pt-BR');

export default function Home() {
  return (
    <AccessBoundary>
      {(scope, logout) => (
        <ExperienceBoundary key={scope} owner={scope}>
          <Workspace draftOwner={scope} logout={logout} />
        </ExperienceBoundary>
      )}
    </AccessBoundary>
  );
}

function Workspace({ draftOwner, logout }: { draftOwner: string; logout?: () => Promise<void> }) {
  const { profile } = useExperience();
  const professional = profile === 'professional';
  const [view, setView] = useState<'home' | 'project' | 'library' | 'trash' | 'knowledge'>('home');
  const [hasProject, setHasProject] = useState(false);
  const { catalog, utilities, requirements, health, states, initializationIssues, retry } =
    useWorkspaceResources();
  const [input, setInput] = useState<ProjectInput>(initial);
  const [saved, setSaved] = useState<Project>();
  const inputSignature = useMemo(() => JSON.stringify(input), [input]);
  const savedSignature = useMemo(
    () => JSON.stringify(saved ? projectInputs(saved) : initial()),
    [saved],
  );
  const createId = useRef<string | undefined>(undefined);
  const draftSlot = useRef<string | undefined>(undefined);
  const recoveredSource = useRef<{ key: string; data: string } | undefined>(undefined);
  const [recoverableDrafts, setRecoverableDrafts] = useState<{ key: string; draft: Draft }[]>([]);
  const [draftIssue, setDraftIssue] = useState('');
  const [conflict, setConflict] = useState<Project>();
  const [conflictPending, setConflictPending] = useState(false);
  const [review, setReview] = useState<{
    input: ProjectInput;
    data: components['schemas']['ProjectRevalidation'];
  }>();
  useEffect(() => {
    draftSlot.current ??= draftKey(draftOwner);
    let active = true;
    Promise.resolve().then(() => {
      if (!active) return;
      try {
        setRecoverableDrafts(readDrafts(localStorage, draftOwner));
      } catch {
        setDraftIssue(
          'Recuperação local indisponível neste navegador. Salve no servidor antes de fechar.',
        );
      }
    });
    return () => {
      active = false;
    };
  }, [draftOwner]);
  const pendingDraft = useRef<(() => void) | undefined>(undefined);
  useEffect(() => {
    function flush() {
      pendingDraft.current?.();
    }
    function hidden() {
      if (document.visibilityState === 'hidden') flush();
    }
    window.addEventListener('pagehide', flush);
    window.addEventListener('beforeunload', flush);
    document.addEventListener('visibilitychange', hidden);
    return () => {
      flush();
      window.removeEventListener('pagehide', flush);
      window.removeEventListener('beforeunload', flush);
      document.removeEventListener('visibilitychange', hidden);
    };
  }, []);
  useLayoutEffect(() => {
    if (!hasProject || !draftSlot.current) {
      pendingDraft.current = undefined;
      return;
    }
    const slot = draftSlot.current;
    createId.current ??= crypto.randomUUID();
    const creation = createId.current;
    let persisted = false;
    function persist() {
      if (persisted) return;
      try {
        if (saved && savedSignature === inputSignature) localStorage.removeItem(slot);
        else writeDraft(localStorage, slot, input, saved, creation);
        persisted = true;
      } catch {
        queueMicrotask(() =>
          setDraftIssue(
            'Não foi possível proteger o rascunho neste navegador. Salve no servidor antes de fechar.',
          ),
        );
      }
    }
    pendingDraft.current = persist;
    const timer = setTimeout(persist, 250);
    return () => clearTimeout(timer);
  }, [input, saved, hasProject, inputSignature, savedSignature]);
  const [pendingRoom, setPendingRoom] = useState<string>();
  useEffect(() => {
    if (pendingRoom) {
      focusField(`room.${pendingRoom}.name`);
    }
  }, [pendingRoom]);
  const [libraryRevision, setLibraryRevision] = useState(0);
  const [feedback, setFeedback] = useState<{ text: string; tone: FeedbackTone }>({
    text: '',
    tone: 'info',
  });
  const message = feedback.text;
  const setMessage = useCallback(
    (text: string, tone: FeedbackTone = 'info') => setFeedback({ text, tone }),
    [],
  );
  const [operationIssues, setOperationIssues] = useState<{
    input: ProjectInput;
    notices: components['schemas']['Notification'][];
  }>();
  const [exporting, setExporting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [autosave, setAutosave] = useState(true);
  const autosaveAttempt = useRef('');
  const [catalogQuery, setCatalogQuery] = useState('');
  const filteredCatalog = selectionCatalog(catalog).filter((item) =>
    searchText(`${item.category} ${item.selection_name ?? item.name}`).includes(
      searchText(catalogQuery),
    ),
  );
  const currentInput = useRef(input);
  useLayoutEffect(() => {
    currentInput.current = input;
  }, [input]);
  const [calculationScope, setCalculationScope] = useState(0);
  const {
    result: currentResult,
    displayResult: result,
    error,
    loading,
    stale,
    notifications,
    httpStatus,
  } = useCalculation(input, String(calculationScope), view === 'project');
  const dirty = savedSignature !== inputSignature;
  const refresh = useCallback(async () => {
    setLibraryRevision((value) => value + 1);
  }, []);
  useEffect(() => {
    if (view === 'project') focusField('project.name');
    else document.querySelector<HTMLElement>('[data-workspace-heading]')?.focus();
  }, [view, calculationScope]);
  function navigate(next: typeof view) {
    setMessage('');
    if (next === view) document.querySelector<HTMLElement>('[data-workspace-heading]')?.focus();
    else setView(next);
  }
  function showHome() {
    navigate('home');
  }
  function showLibrary() {
    navigate('library');
  }
  function showTrash() {
    navigate('trash');
  }
  function change<K extends keyof ProjectInput>(key: K, value: ProjectInput[K]) {
    setMessage('');
    setInput((old) => ({ ...old, [key]: value }));
  }
  function updateRoom(id: string, patch: Partial<Environment>) {
    setMessage('');
    setInput((old) => ({
      ...old,
      environments: (old.environments ?? []).map((room) =>
        room.id === id ? { ...room, ...patch } : room,
      ),
    }));
  }
  function updateLoad(room: Environment, id: string, patch: Partial<Load>) {
    setMessage('');
    setInput((old) => ({
      ...old,
      environments: (old.environments ?? []).map((current) =>
        current.id === room.id
          ? {
              ...current,
              loads: (current.loads ?? []).map((load) =>
                load.id === id ? { ...load, ...patch } : load,
              ),
            }
          : current,
      ),
    }));
  }
  function duplicateRoom(source: Environment) {
    const id = crypto.randomUUID();
    setInput((old) => {
      const rooms = old.environments ?? [];
      const original = rooms.find((room) => room.id === source.id);
      if (!original) return old;
      const copy = duplicateEnvironment(original, rooms, id);
      const index = rooms.indexOf(original);
      return {
        ...old,
        environments: [...rooms.slice(0, index + 1), copy, ...rooms.slice(index + 1)],
      };
    });
    setPendingRoom(id);
    setMessage('Ambiente duplicado. A cópia pode ser editada independentemente.', 'success');
  }
  function addRoom() {
    const room: Environment = {
      id: crypto.randomUUID(),
      name: 'Novo ambiente',
      type: 'living',
      area_m2: null,
      perimeter_m: null,
      lighting_points: 1,
      outlets: 0,
      loads: [],
    };
    setInput((old) => ({ ...old, environments: [...(old.environments ?? []), room] }));
    setPendingRoom(room.id);
  }
  function addLoad(room: Environment, template?: Template) {
    const load = newLoad(template);
    setInput((old) => ({
      ...old,
      environments: (old.environments ?? []).map((current) =>
        current.id === room.id ? { ...current, loads: [...(current.loads ?? []), load] } : current,
      ),
    }));
  }
  const writeInFlight = useRef(false);
  const save = useCallback(
    async (automatic = false, asNew = false) => {
      if (writeInFlight.current) return;
      if (conflictPending && !asNew) {
        setMessage('Resolva o conflito abaixo ou salve sua edição como novo projeto.');
        return;
      }
      writeInFlight.current = true;
      setBusy(true);
      setSaving(true);
      setMessage('Salvando projeto…');
      setOperationIssues(undefined);
      const startedInput = input;
      const snapshot =
        asNew && saved && input.name === saved.name
          ? { ...input, name: `${input.name.slice(0, 190)} · cópia` }
          : input;
      const creating = !saved || asNew;
      if (creating) {
        createId.current ??= crypto.randomUUID();
        try {
          writeDraft(localStorage, draftSlot.current!, input, saved, createId.current);
        } catch {
          setDraftIssue('Não foi possível proteger o identificador do salvamento neste navegador.');
        }
      }
      try {
        const project = await request<Project>(
          saved && !asNew ? `/projects/${saved.id}?expected_version=${saved.version}` : '/projects',
          {
            method: saved && !asNew ? 'PUT' : 'POST',
            body: JSON.stringify(snapshot),
            headers: creating ? { 'Idempotency-Key': createId.current! } : undefined,
          },
        );
        setSaved(project);
        if (creating) createId.current = undefined;
        try {
          const source = recoveredSource.current;
          if (source && localStorage.getItem(source.key) === source.data)
            localStorage.removeItem(source.key);
          recoveredSource.current = undefined;
        } catch {
          /* The original recovery slot remains available. */
        }
        setConflict(undefined);
        setConflictPending(false);
        // Preserve edits made while the save request was in flight.
        if (currentInput.current === startedInput) setInput(projectInputs(project));
        else if (
          asNew &&
          snapshot.name !== startedInput.name &&
          currentInput.current.name === startedInput.name
        )
          setInput((old) => ({ ...old, name: project.name }));
        setMessage(
          currentInput.current !== startedInput
            ? 'Versão anterior salva. Há alterações mais recentes ainda não salvas.'
            : automatic
              ? 'Alterações salvas automaticamente.'
              : 'Projeto salvo com histórico do cálculo parcial e suas pendências.',
          currentInput.current !== startedInput ? 'warning' : 'success',
        );
        await refresh();
      } catch (e) {
        if (e instanceof APIError && e.status === 409 && creating && createId.current) {
          try {
            const existing = await request<Project>(`/projects/${createId.current}`);
            setSaved(existing);
            if (
              currentInput.current.name === startedInput.name &&
              ((asNew && snapshot.name !== startedInput.name) ||
                startedInput.name.trim() === existing.name)
            )
              setInput((old) => ({ ...old, name: existing.name }));
            createId.current = undefined;
            setConflict(undefined);
            setConflictPending(false);
            setMessage(
              'Primeiro salvamento recuperado. Suas alterações atuais foram mantidas para o próximo salvamento.',
            );
            await refresh();
          } catch {
            setMessage(
              'Não foi possível recuperar o primeiro salvamento. O rascunho foi preservado; confira os projetos salvos antes de tentar novamente.',
            );
          }
        } else if (e instanceof APIError && e.status === 409 && saved && !asNew) {
          setConflictPending(true);
          setMessage(
            'Outra edição alterou este projeto. Salvamento automático pausado; suas alterações locais foram preservadas.',
          );
          try {
            setConflict(await request<Project>(`/projects/${saved.id}`));
          } catch {
            setMessage(
              'Conflito detectado. A versão do servidor está indisponível; salve suas alterações como novo projeto ou tente consultar novamente.',
            );
          }
        } else if (e instanceof APIError && e.notifications.length) {
          setOperationIssues({ input: startedInput, notices: e.notifications });
          setMessage('Não foi possível salvar. Corrija os campos indicados.', 'error');
        } else setMessage((e as Error).message, 'error');
      } finally {
        writeInFlight.current = false;
        setBusy(false);
        setSaving(false);
      }
    },
    [input, saved, refresh, conflictPending, setMessage],
  );
  useEffect(() => {
    if (!autosave || !saved || !dirty || busy || conflictPending || input.name !== saved.name)
      return;
    const attempt = `${saved.id}:${saved.version}:${inputSignature}`;
    if (autosaveAttempt.current === attempt) return;
    const timer = setTimeout(() => {
      autosaveAttempt.current = attempt;
      void save(true);
    }, 1500);
    return () => clearTimeout(timer);
    // save uses exactly the input/version captured by this scheduled effect.
  }, [autosave, saved, input, inputSignature, dirty, busy, save, conflictPending]);

  async function open(project: Pick<Project, 'id'>) {
    if (hasProject && dirty && !window.confirm('Descartar alterações locais e abrir este projeto?'))
      return false;
    const snapshot = currentInput.current;
    setBusy(true);
    setMessage('Abrindo projeto…');
    try {
      const fresh = await request<Project>(`/projects/${project.id}`);
      if (currentInput.current !== snapshot) {
        setMessage(
          'Você editou os dados durante o carregamento. As alterações foram preservadas; abra o projeto novamente quando terminar.',
        );
        return false;
      }
      pendingDraft.current?.();
      createId.current = undefined;
      setCalculationScope((value) => value + 1);
      setSaved(fresh);
      recoveredSource.current = undefined;
      setConflict(undefined);
      setConflictPending(false);
      setInput(projectInputs(fresh));
      setHasProject(true);
      setView('project');
      setMessage('');
      return true;
    } catch (e) {
      setMessage((e as Error).message, 'error');
      return false;
    } finally {
      setBusy(false);
    }
  }
  function newProject() {
    if (
      hasProject &&
      dirty &&
      !window.confirm('Descartar alterações locais e criar outro projeto?')
    )
      return;
    pendingDraft.current?.();
    createId.current = undefined;
    setCalculationScope((value) => value + 1);
    setSaved(undefined);
    recoveredSource.current = undefined;
    setConflict(undefined);
    setConflictPending(false);
    setInput(initial());
    setHasProject(true);
    setView('project');
    setOperationIssues(undefined);
    setMessage('');
  }
  async function remove(project: Pick<Project, 'id' | 'version' | 'name'> | undefined = saved) {
    if (
      !project ||
      !window.confirm(
        `Mover “${project.name}” para projetos excluídos? Você poderá restaurá-lo com seu histórico.${saved?.id === project.id && dirty ? ' As alterações ainda não salvas desta edição serão descartadas.' : ''}`,
      )
    )
      return;
    const snapshot = currentInput.current;
    setBusy(true);
    setMessage('Movendo projeto para a lixeira…');
    try {
      await request(`/projects/${project.id}?expected_version=${project.version}`, {
        method: 'DELETE',
      });
      if (saved?.id === project.id) {
        setCalculationScope((value) => value + 1);
        setSaved(undefined);
        if (currentInput.current === snapshot) {
          setInput(initial());
          setHasProject(false);
          setView((current) => (current === 'project' ? 'home' : current));
        }
      }
      await refresh();
      setMessage('Projeto movido para excluídos. Seu histórico foi preservado.', 'success');
    } catch (e) {
      setMessage((e as Error).message, 'error');
    } finally {
      setBusy(false);
    }
  }
  async function duplicateProject(project: Pick<Project, 'id'>) {
    setBusy(true);
    setMessage('Duplicando projeto…');
    try {
      await request<Project>(`/projects/${project.id}/duplicate`, { method: 'POST' });
      await refresh();
      setMessage(
        'Cópia criada na área de trabalho. O projeto em edição foi preservado.',
        'success',
      );
    } catch (e) {
      setMessage((e as Error).message, 'error');
    } finally {
      setBusy(false);
    }
  }
  async function restoreProject(project: Pick<Project, 'id' | 'version'>) {
    setBusy(true);
    setMessage('Restaurando projeto…');
    try {
      await request(`/projects/${project.id}/restore?expected_version=${project.version}`, {
        method: 'POST',
      });
      await refresh();
      setMessage('Projeto restaurado com seu histórico.', 'success');
    } catch (e) {
      setMessage((e as Error).message, 'error');
    } finally {
      setBusy(false);
    }
  }
  async function checkReferences() {
    if (!saved || busy || exporting) return;
    if (dirty) {
      setMessage('Salve suas alterações antes de comparar as referências do projeto.');
      return;
    }
    setBusy(true);
    setReview(undefined);
    setMessage('Verificando referências do projeto…');
    const snapshot = currentInput.current;
    try {
      const check = await request<components['schemas']['ProjectRevalidation']>(
        `/projects/${saved.id}/revalidation`,
      );
      if (currentInput.current !== snapshot) return;
      if (check.project_version !== saved.version) {
        setMessage('O projeto mudou no servidor. Abra a versão atual antes de revisar.');
        return;
      }
      setReview({ input: snapshot, data: check });
      setMessage(
        check.requires_revalidation
          ? 'Referências alteradas: revalidação necessária. Histórico e valores manuais preservados.'
          : 'Referências correspondem à revisão registrada. Consulte o alcance normativo nos resultados.',
      );
    } catch (e) {
      setMessage((e as Error).message, 'error');
    } finally {
      setBusy(false);
    }
  }
  async function registerRevalidation() {
    if (!saved || !review || dirty || busy || exporting || input !== review.input) return;
    const snapshot = currentInput.current;
    setBusy(true);
    try {
      const project = await request<Project>(
        `/projects/${saved.id}/recalculate?expected_version=${review.data.project_version}`,
        { method: 'POST' },
      );
      setSaved(project);
      if (currentInput.current === snapshot) setInput(projectInputs(project));
      setReview(undefined);
      setMessage(
        'Revalidação registrada em nova versão. Histórico e valores manuais preservados.',
        'success',
      );
      await refresh();
    } catch (reason) {
      setMessage((reason as Error).message, 'error');
    } finally {
      setBusy(false);
    }
  }
  async function purgeProject(project: Pick<Project, 'id' | 'version' | 'name'>) {
    if (
      !window.confirm(
        `Excluir definitivamente “${project.name}” e seu histórico? Esta ação não pode ser desfeita.`,
      )
    )
      return;
    setBusy(true);
    setMessage('Excluindo projeto definitivamente…');
    try {
      await request(`/projects/${project.id}/permanent?expected_version=${project.version}`, {
        method: 'DELETE',
      });
      await refresh();
      setMessage('Projeto e histórico excluídos definitivamente.', 'success');
    } catch (e) {
      setMessage((e as Error).message, 'error');
    } finally {
      setBusy(false);
    }
  }
  async function exportReport(format: 'pdf' | 'json') {
    if (busy || exporting || !currentResult || !currentResult.technical_context?.registry_version)
      return;
    const snapshot = input;
    setOperationIssues(undefined);
    setExporting(true);
    try {
      const blob = await requestReport(format, {
        project: snapshot,
        ...(saved && !dirty
          ? { saved_project_id: saved.id, saved_project_version: saved.version }
          : {}),
        expected_input_digest: currentResult.input_digest,
        expected_registry_version: String(currentResult.technical_context.registry_version),
        expected_engine_version: currentResult.engine_version,
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exportFilename(snapshot.name, format);
      link.click();
      URL.revokeObjectURL(url);
      setMessage(
        currentInput.current === snapshot
          ? `${format.toUpperCase()} exportado com as entradas calculadas.`
          : `${format.toUpperCase()} exportado com os dados do início da exportação; há alterações posteriores.`,
        currentInput.current === snapshot ? 'success' : 'warning',
      );
    } catch (e) {
      if (e instanceof APIError && e.notifications.length) {
        setOperationIssues({ input: snapshot, notices: e.notifications });
        setMessage('Não foi possível exportar. Corrija os campos indicados.', 'error');
      } else setMessage((e as Error).message, 'error');
    } finally {
      setExporting(false);
    }
  }
  return (
    <RequirementsContext.Provider value={requirements}>
      <CalculationScopeContext.Provider value={input.analysis_scope ?? 'installed'}>
        <div
          data-experience={profile}
          className={`app-shell${view === 'home' ? ' app-shell-home' : ''}`}
        >
          <a className="skip-link" href="#workspace-main">
            Ir para o conteúdo
          </a>
          <aside className="workspace-sidebar" aria-label="Navegação do espaço de trabalho">
            <div className="workspace-brand">
              <span className="brand-mark" aria-hidden="true">
                ϟ
              </span>
              <div>
                <p className="brand-name">EletroProjeto</p>
                <p className="brand-caption">Estudos elétricos residenciais</p>
              </div>
            </div>
            <ExperienceSwitcher />
            <p className="sidebar-label">ESPAÇO DE TRABALHO</p>
            <SectionNavigation
              active={view}
              busy={busy || exporting}
              hasProject={hasProject}
              projectName={input.name}
              dirty={dirty || !saved}
              onHome={showHome}
              onNew={newProject}
              onProject={() => navigate('project')}
              onLibrary={showLibrary}
              onTrash={showTrash}
              onKnowledge={() => navigate('knowledge')}
            />
            {view === 'project' && (
              <div className="sidebar-actions">
                <p className="eyebrow">AÇÕES DO PROJETO</p>

                <ProjectActions
                  hideNew
                  saved={!!saved}
                  busy={busy}
                  saving={saving}
                  exporting={exporting}
                  canExport={!!currentResult?.technical_context?.registry_version}
                  canExportPdf={!!currentResult?.technical_context?.registry_version}
                  onNew={newProject}
                  onSave={() => save()}
                  onSaveAs={() => save(false, true)}
                  onPdf={() => exportReport('pdf')}
                  onJson={() => exportReport('json')}
                  onDelete={() => remove()}
                  onCheck={checkReferences}
                />
              </div>
            )}
            <p className="sidebar-note">
              Estimativa de consumo a partir dos aparelhos e do uso que você informar.
            </p>
            {logout && (
              <button
                className="btn"
                disabled={busy || exporting}
                onClick={async () => {
                  try {
                    await logout();
                  } catch {
                    setMessage('Não foi possível encerrar a sessão. Tente novamente.');
                  }
                }}
              >
                Sair da conta
              </button>
            )}
          </aside>
          <main id="workspace-main" className="workspace-main" tabIndex={-1}>
            {draftIssue && (
              <Feedback tone="warning" role="alert" className="mb-5">
                {draftIssue}
              </Feedback>
            )}
            {recoverableDrafts.length > 0 && (
              <section aria-label="Rascunhos recuperados" className="panel mb-5">
                <h2 className="text-lg font-semibold">Rascunhos recuperados neste navegador</h2>
                <p>
                  Estes dados ainda não foram confirmados no servidor. Abra um rascunho para
                  continuar; nenhum envio é feito ao recuperá-lo.
                </p>
                {recoverableDrafts.map(({ key, draft }) => (
                  <div key={key} className="mt-3 flex flex-wrap items-center gap-3">
                    <span>
                      {draft.input.name} · {formatDate(draft.updatedAt)} · Brasília
                    </span>
                    <button
                      className="btn"
                      disabled={busy || exporting}
                      onClick={() => {
                        if (
                          hasProject &&
                          dirty &&
                          !window.confirm('Descartar a edição atual e recuperar este rascunho?')
                        )
                          return;
                        pendingDraft.current?.();
                        createId.current = draft.createId;
                        setInput(draft.input);
                        setSaved(draft.saved);
                        setConflict(undefined);
                        setConflictPending(false);
                        setHasProject(true);
                        setView('project');
                        setCalculationScope((value) => value + 1);
                        // Recovery creates a new slot; another tab may still own the original.
                        draftSlot.current = draftKey(draftOwner);
                        try {
                          const data = localStorage.getItem(key);
                          recoveredSource.current = data === null ? undefined : { key, data };
                        } catch {
                          recoveredSource.current = undefined;
                        }
                        setRecoverableDrafts((items) => items.filter((item) => item.key !== key));
                        setMessage(
                          'Rascunho recuperado. Confira os dados e salve quando estiver pronto.',
                        );
                      }}
                    >
                      Continuar rascunho
                    </button>
                    <button
                      className="btn"
                      onClick={() => {
                        if (!window.confirm('Apagar este rascunho somente deste navegador?'))
                          return;
                        try {
                          localStorage.removeItem(key);
                          setRecoverableDrafts((items) => items.filter((item) => item.key !== key));
                        } catch {
                          setDraftIssue('Não foi possível apagar o rascunho local.');
                        }
                      }}
                    >
                      Apagar rascunho local
                    </button>
                  </div>
                ))}
              </section>
            )}
            {conflictPending && (
              <section
                role="alert"
                className="panel feedback mb-5"
                data-tone="warning"
                aria-label="Resolver conflito de edição"
              >
                <h2 className="text-lg font-semibold">Projeto alterado em outra sessão</h2>
                <p>Sua edição local está preservada. Escolha como continuar.</p>
                {conflict && (
                  <p>
                    Servidor: {conflict.name}, versão {conflict.version}. Sua base: versão{' '}
                    {saved?.version}.
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-3">
                  <button className="btn" disabled={busy} onClick={() => save(false, true)}>
                    Salvar minha edição como novo projeto
                  </button>
                  <button
                    className="btn"
                    disabled={busy || !conflict}
                    onClick={() => {
                      if (
                        !conflict ||
                        !window.confirm(
                          'Substituir a edição atual pela versão do servidor? O rascunho local será mantido para recuperação.',
                        )
                      )
                        return;
                      // Keep the local draft and use a new slot for the server edition.
                      pendingDraft.current?.();
                      try {
                        setRecoverableDrafts(readDrafts(localStorage, draftOwner));
                      } catch {
                        /* Existing draft is retained. */
                      }
                      draftSlot.current = draftKey(draftOwner);
                      setInput(projectInputs(conflict));
                      setSaved(conflict);
                      setConflict(undefined);
                      setConflictPending(false);
                      setCalculationScope((value) => value + 1);
                      setMessage('Versão do servidor carregada.');
                    }}
                  >
                    Usar versão do servidor
                  </button>
                  {!conflict && (
                    <button
                      className="btn"
                      disabled={busy}
                      onClick={async () => {
                        if (!saved) return;
                        try {
                          setConflict(await request<Project>(`/projects/${saved.id}`));
                        } catch {
                          setMessage(
                            'A consulta ainda não está disponível. Sua edição local foi preservada.',
                          );
                        }
                      }}
                    >
                      Consultar versão do servidor
                    </button>
                  )}
                </div>
              </section>
            )}
            {message && (
              <Feedback tone={feedback.tone} data-testid="project-message" className="mb-5">
                {message}
              </Feedback>
            )}
            {!!initializationIssues.length && (
              <Feedback tone="error" className="mb-5">
                <p>{initializationIssues.join(' ')}</p>
                <button
                  className="btn mt-3"
                  disabled={busy}
                  onClick={() => {
                    setMessage('');
                    retry();
                  }}
                >
                  Tentar conexão novamente
                </button>
              </Feedback>
            )}
            {view === 'knowledge' && <KnowledgeLibrary />}
            {view === 'home' && (
              <WorkspaceHome
                busy={busy || exporting}
                projectName={hasProject ? input.name || 'Projeto sem nome' : undefined}
                onNew={newProject}
                onLibrary={showLibrary}
                onTrash={showTrash}
                onKnowledge={() => navigate('knowledge')}
                onContinue={() => setView('project')}
              />
            )}
            {(view === 'library' || view === 'trash') && (
              <ProjectWorkspace
                key={view}
                archived={view === 'trash'}
                revision={libraryRevision}
                busy={busy || exporting}
                onOpen={open}
                onDuplicate={duplicateProject}
                onDelete={remove}
                onRestore={restoreProject}
                onPurge={purgeProject}
                onNew={newProject}
              />
            )}
            {view === 'project' && (
              <>
                {review?.input === input &&
                  review.data.project_id === saved?.id &&
                  review.data.project_version === saved.version && (
                    <ProjectRevalidation
                      review={review.data}
                      busy={busy || exporting}
                      onRegister={registerRevalidation}
                      onClose={() => setReview(undefined)}
                    />
                  )}
                <header className="page-header">
                  <PageHeading
                    title={professional ? 'Estudo da residência' : 'Consumo da residência'}
                    eyebrow={
                      professional ? 'CONSUMO E ESTUDOS TÉCNICOS' : 'SEU CONSUMO EM 3 PASSOS'
                    }
                    description={
                      professional
                        ? 'Organize as cargas, confira os parâmetros e consulte as verificações disponíveis.'
                        : 'Adicione os aparelhos que você usa ou planeja usar e estime o consumo da sua casa.'
                    }
                  />
                </header>
                <ExperienceGuide onKnowledge={() => navigate('knowledge')} />
                {operationIssues?.input === input && !error && (
                  <CalculationNotices
                    stale={false}
                    notices={operationIssues.notices.filter(
                      (notice) =>
                        !currentResult?.notifications?.some(
                          (current) =>
                            current.id === notice.id ||
                            (notice.target_id != null && current.target_id === notice.target_id),
                        ),
                    )}
                  />
                )}
                <p
                  className={loading || error ? 'mb-3 text-xs muted' : 'sr-only'}
                  role="status"
                  data-testid="calculation-status"
                >
                  {loading
                    ? result
                      ? 'Recalculando… Resultados desatualizados ficam ocultos até a atualização.'
                      : 'Recalculando as entradas atuais…'
                    : error
                      ? 'Entradas inválidas ou erro na API. Valores anteriores desatualizados; exportação indisponível.'
                      : 'Resultados atualizados para as entradas atuais.'}
                </p>
                {error && <CalculationNotices notices={notifications} stale={false} />}
                {error && !notifications.length && (
                  <Feedback tone="error" className="mb-5">
                    {error}
                  </Feedback>
                )}
                <section id="project" aria-labelledby="project-heading" className="panel mb-6">
                  <header className="section-header">
                    <SectionHeading
                      id="project-heading"
                      eyebrow="01 / PROJETO"
                      title="Dados do projeto"
                      description="Dê um nome ao estudo. Para estimar o custo, informe também a tarifa da sua conta de luz."
                    />
                    <span
                      className="status-pill"
                      data-state={saved && !dirty ? 'saved' : 'pending'}
                    >
                      {saved
                        ? dirty
                          ? 'Alterações não salvas'
                          : `Salvo · versão ${saved.version}`
                        : dirty
                          ? 'Rascunho não salvo'
                          : 'Novo projeto'}
                    </span>
                  </header>
                  <p className="project-context">
                    {saved
                      ? `Editando projeto salvo: ${saved.name}. Para preservar este registro e criar outro, use Salvar como novo.`
                      : 'Novo projeto independente · o primeiro salvamento criará um registro.'}
                  </p>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Field field="project.name" label="Nome do projeto">
                      <input value={input.name} onChange={(e) => change('name', e.target.value)} />
                    </Field>
                    {saved && input.name !== saved.name && (
                      <p className="text-xs text-amber-200 md:col-span-2">
                        Nome alterado: use Salvar projeto para renomear este registro ou Salvar como
                        novo para criar outro. O salvamento automático está pausado.
                      </p>
                    )}
                    <Field field="project.state" label="Estado">
                      <select
                        value={input.state}
                        onChange={(e) =>
                          setInput((old) => ({
                            ...old,
                            state: e.target.value as ProjectInput['state'],
                            utility: 'unconfirmed',
                          }))
                        }
                      >
                        {(states.length ? states : [input.state ?? 'SP']).map((state) => (
                          <option key={state} value={state}>
                            {state}
                          </option>
                        ))}
                      </select>
                    </Field>
                    <Field field="project.municipality" label="Município">
                      <input
                        value={input.municipality}
                        onChange={(e) => change('municipality', e.target.value)}
                      />
                    </Field>
                    <Field
                      field="project.energy_tariff_brl_per_kwh"
                      label="Tarifa de energia (R$/kWh)"
                    >
                      <input
                        type="number"
                        min="0"
                        step="any"
                        placeholder="Opcional · informe sua tarifa"
                        aria-describedby="energy-tariff-description"
                        value={input.energy_tariff_brl_per_kwh ?? ''}
                        onChange={(e) =>
                          change('energy_tariff_brl_per_kwh', e.target.value || null)
                        }
                      />
                    </Field>
                  </div>
                  <p id="energy-tariff-description" className="field-hint mt-3">
                    Tarifa opcional, em R$/kWh, disponível na conta de luz. Não sabe? Você ainda
                    pode estimar o consumo.
                  </p>
                  <div className="project-preferences">
                    <div className="preference-row">
                      <label className="checkbox-option" htmlFor="project-autosave">
                        <input
                          id="project-autosave"
                          type="checkbox"
                          checked={autosave}
                          aria-describedby="autosave-description"
                          onChange={(e) => setAutosave(e.target.checked)}
                        />
                        <span>Salvar automaticamente após o primeiro salvamento</span>
                      </label>
                      <span
                        className="status-pill"
                        data-state={
                          !autosave
                            ? 'neutral'
                            : !saved || input.name !== saved.name || conflictPending
                              ? 'pending'
                              : 'saved'
                        }
                      >
                        {!autosave
                          ? 'Desativado'
                          : !saved
                            ? 'Após salvar'
                            : input.name !== saved.name || conflictPending
                              ? 'Pausado'
                              : saving
                                ? 'Salvando…'
                                : 'Ativado'}
                      </span>
                    </div>
                    <p id="autosave-description" className="field-hint">
                      {!saved
                        ? 'Salve o projeto uma vez para iniciar o salvamento automático.'
                        : !autosave
                          ? 'As próximas alterações serão salvas somente ao escolher Salvar projeto.'
                          : conflictPending
                            ? 'Pausado: resolva o conflito de edição antes de continuar.'
                            : input.name !== saved.name
                              ? 'Pausado enquanto o nome está alterado. Escolha renomear o projeto ou salvar como novo.'
                              : 'As alterações são salvas após uma breve pausa na edição. Aguarde a confirmação de salvamento.'}
                    </p>
                  </div>
                  <details open={professional || undefined} className="project-extra disclosure">
                    <summary>Outros dados do projeto</summary>
                    <div className="mt-3 grid gap-4 md:grid-cols-3">
                      <Field field="project.utility" label="Concessionária">
                        <select
                          value={input.utility}
                          onChange={(e) =>
                            change('utility', e.target.value as ProjectInput['utility'])
                          }
                        >
                          <option value="unconfirmed">Não confirmada</option>
                          {utilities
                            .filter((item) => item.states.includes(input.state ?? 'SP'))
                            .map((item) => (
                              <option key={item.id} value={item.id}>
                                {item.name} · seleção manual
                              </option>
                            ))}
                        </select>
                      </Field>

                      <Field field="project.built_area_m2" label="Área construída (m²)">
                        <input
                          type="number"
                          min="0.001"
                          step="any"
                          value={input.built_area_m2 ?? ''}
                          onChange={(e) => change('built_area_m2', e.target.value || null)}
                        />
                      </Field>

                      <Field field="project.floors" label="Pavimentos">
                        <input
                          type="number"
                          min="1"
                          step="1"
                          value={input.floors ?? ''}
                          onChange={(e) =>
                            change('floors', e.target.value === '' ? null : Number(e.target.value))
                          }
                        />
                      </Field>

                      <Field field="project.residence_type" label="Tipo de residência">
                        <input
                          value={input.residence_type ?? ''}
                          onChange={(e) => change('residence_type', e.target.value || null)}
                        />
                      </Field>
                    </div>
                    {input.reference_voltage_v != null && (
                      <p className="field-hint mt-3">
                        Tensão de referência cadastrada: {input.reference_voltage_v} V
                        (informativa). Cada equipamento utiliza sua própria tensão.
                      </p>
                    )}
                  </details>
                  <div className="project-notes">
                    <Field field="project.notes" label="Observações">
                      <textarea
                        rows={3}
                        maxLength={10000}
                        placeholder="Registre condições do estudo, equipamentos a conferir e informações úteis para o projeto."
                        aria-describedby="project-notes-description"
                        value={input.notes}
                        onChange={(e) => change('notes', e.target.value)}
                      />
                    </Field>
                    <div className="field-caption">
                      <p id="project-notes-description" className="field-hint">
                        Informações complementares que também aparecem no relatório.
                      </p>
                      <span className="field-hint">
                        {input.notes?.length ?? 0} / 10.000 caracteres
                      </span>
                    </div>
                  </div>
                </section>
                <section
                  id="environments"
                  className="environments-section"
                  aria-labelledby="environments-title"
                >
                  <header className="environments-toolbar section-header">
                    <SectionHeading
                      eyebrow="02 / AMBIENTES"
                      title="Ambientes e equipamentos"
                      id="environments-title"
                      description="Adicione os cômodos, escolha os aparelhos e informe como costuma usá-los."
                    />
                    <button
                      className="btn primary add-environment"
                      id="add-environment"
                      onClick={addRoom}
                      disabled={busy || exporting}
                    >
                      <WorkspaceIcon name="new" /> Adicionar ambiente
                    </button>
                  </header>
                  {!(input.environments ?? []).length && (
                    <div className="panel py-12 text-center">
                      <p className="text-lg">Comece pelos ambientes</p>
                      <p className="mt-2 text-sm muted">
                        Adicione um cômodo e os aparelhos que você usa ou planeja instalar.
                      </p>
                      <button className="btn primary mt-5" onClick={addRoom}>
                        Adicionar primeiro ambiente
                      </button>
                    </div>
                  )}
                  <p className="mb-4 text-sm muted">
                    As potências do catálogo são referências. Ajuste para o seu aparelho e abra
                    <strong> Consumo mensal</strong> para informar horários ou o consumo da
                    etiqueta.
                  </p>
                  <label className="mb-4 max-w-sm">
                    Pesquisar catálogo
                    <input
                      type="search"
                      placeholder="Equipamento ou categoria"
                      value={catalogQuery}
                      onChange={(e) => setCatalogQuery(e.target.value)}
                    />
                  </label>
                  <div className="space-y-5">
                    {(input.environments ?? []).map((room, roomIndex) => (
                      <article
                        className="panel environment-card"
                        key={room.id}
                        aria-label={`Ambiente: ${room.name}`}
                      >
                        <header className="environment-header">
                          <div className="min-w-0">
                            <p className="eyebrow">
                              AMBIENTE {String(roomIndex + 1).padStart(2, '0')}
                            </p>
                            <h3 className="font-semibold break-words">{room.name}</h3>
                          </div>
                          <div className="environment-actions">
                            <button
                              className="btn subtle"
                              aria-label={`Duplicar ambiente ${room.name}`}
                              disabled={busy || exporting}
                              onClick={() => duplicateRoom(room)}
                            >
                              <WorkspaceIcon name="copy" /> Duplicar ambiente
                            </button>
                            <button
                              className="btn subtle danger"
                              aria-label={`Remover ambiente ${room.name}`}
                              onClick={() => {
                                if (
                                  !room.loads?.length ||
                                  window.confirm(`Remover ${room.name} e seus equipamentos?`)
                                )
                                  setInput((old) => {
                                    const updated = removeProjectLoads(
                                      old,
                                      (room.loads ?? []).map((load) => load.id!),
                                    );
                                    return {
                                      ...updated,
                                      environments: updated.environments?.filter(
                                        (item) => item.id !== room.id,
                                      ),
                                    };
                                  });
                              }}
                            >
                              <WorkspaceIcon name="trash" /> Remover ambiente
                            </button>
                          </div>
                        </header>
                        <div className="environment-fields">
                          <Field
                            field="environment.name"
                            label="Nome"
                            path={`room.${room.id}.name`}
                          >
                            <input
                              value={room.name}
                              onChange={(e) => updateRoom(room.id!, { name: e.target.value })}
                            />
                          </Field>
                          <Field
                            field="environment.type"
                            label="Tipo"
                            path={`room.${room.id}.type`}
                          >
                            <select
                              value={room.type}
                              onChange={(e) =>
                                updateRoom(room.id!, {
                                  type: e.target.value as Environment['type'],
                                })
                              }
                            >
                              {Object.entries(environmentTypes).map(([value, name]) => (
                                <option key={value} value={value}>
                                  {name}
                                </option>
                              ))}
                            </select>
                          </Field>
                        </div>
                        <details
                          open={professional || undefined}
                          className="room-measurements mt-3"
                        >
                          <summary>Medidas, iluminação e tomadas (opcional)</summary>
                          <p className="mt-2 text-xs muted">
                            Usados na previsão de pontos de luz e tomadas. Não são necessários para
                            estimar o consumo dos aparelhos.
                          </p>
                          <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                            <Field
                              field="environment.area_m2"
                              label="Área (m²)"
                              path={`room.${room.id}.area_m2`}
                            >
                              <input
                                type="number"
                                min="0.001"
                                step="any"
                                value={room.area_m2 ?? ''}
                                onChange={(e) =>
                                  updateRoom(room.id!, { area_m2: e.target.value || null })
                                }
                              />
                            </Field>
                            <Field
                              field="environment.perimeter_m"
                              label="Perímetro (m)"
                              path={`room.${room.id}.perimeter_m`}
                            >
                              <input
                                type="number"
                                min="0.001"
                                step="any"
                                value={room.perimeter_m ?? ''}
                                onChange={(e) =>
                                  updateRoom(room.id!, { perimeter_m: e.target.value || null })
                                }
                              />
                            </Field>
                            <Field
                              field="environment.lighting_points"
                              label="Pontos de luz"
                              path={`room.${room.id}.lighting_points`}
                            >
                              <input
                                type="number"
                                min="0"
                                value={
                                  Number.isNaN(room.lighting_points) ? '' : room.lighting_points
                                }
                                onChange={(e) =>
                                  updateRoom(room.id!, {
                                    lighting_points:
                                      e.target.value === '' ? NaN : Number(e.target.value),
                                  })
                                }
                              />
                            </Field>
                            <Field
                              field="environment.outlets"
                              label="Pontos de tomadas"
                              path={`room.${room.id}.outlets`}
                            >
                              <input
                                type="number"
                                min="0"
                                value={Number.isNaN(room.outlets) ? '' : room.outlets}
                                onChange={(e) =>
                                  updateRoom(room.id!, {
                                    outlets: e.target.value === '' ? NaN : Number(e.target.value),
                                  })
                                }
                              />
                            </Field>
                          </div>
                        </details>
                        <div className="mt-4 space-y-2">
                          {(room.loads ?? []).map((load) => (
                            <EquipmentEditor
                              key={load.id}
                              load={load}
                              catalog={catalog}
                              memory={result?.memory.find((entry) => entry.load_id === load.id)}
                              stale={stale}
                              onChange={(patch) => updateLoad(room, load.id!, patch)}
                              onRemove={() =>
                                setInput((old) => removeProjectLoads(old, [load.id!]))
                              }
                              onDuplicate={() =>
                                updateRoom(room.id!, {
                                  loads: [
                                    ...(room.loads ?? []),
                                    { ...structuredClone(load), id: crypto.randomUUID() },
                                  ],
                                })
                              }
                            />
                          ))}
                        </div>
                        <div className="environment-equipment-actions">
                          <RoomEquipmentPicker
                            room={room}
                            choices={filteredCatalog}
                            searching={catalogQuery.trim().length > 0}
                            onAdd={(template) => addLoad(room, template)}
                          />
                          {!catalog.length && (
                            <button className="btn" onClick={() => addLoad(room)}>
                              <WorkspaceIcon name="new" /> Equipamento personalizado
                            </button>
                          )}
                          <span className="ml-auto text-sm text-emerald-300">
                            {currentResult
                              ? `${format(currentResult.by_environment_w[room.id!])} W${room.loads?.some((load) => currentResult.unknown_load_ids?.includes(load.id!)) ? ' · subtotal conhecido' : ''}`
                              : loading
                                ? 'Atualizando…'
                                : '—'}
                          </span>
                        </div>
                      </article>
                    ))}
                  </div>
                  {!!input.environments?.length && (
                    <div className="mt-5 flex justify-end">
                      <button
                        className="btn primary add-environment"
                        aria-label="Adicionar ambiente ao final da lista"
                        onClick={addRoom}
                        disabled={busy || exporting}
                      >
                        <WorkspaceIcon name="new" /> Adicionar ambiente
                      </button>
                    </div>
                  )}
                </section>
                <ResultsPanel
                  tariff={input.energy_tariff_brl_per_kwh}
                  result={result}
                  loading={loading}
                  stale={stale}
                  scope={input.analysis_scope}
                  environments={input.environments}
                  onScopeChange={(value) => change('analysis_scope', value)}
                />
                <details
                  key={`technical-${calculationScope}`}
                  open={professional || undefined}
                  className="technical-tools mt-6"
                >
                  <summary>Estudos técnicos (opcional)</summary>
                  <p className="mt-3 mb-4 text-sm muted">
                    Para quem precisa estudar a instalação: demanda, circuitos e entrada de energia.
                    Estes dados não são necessários para estimar o consumo mensal. Estudos salvos
                    são mantidos.
                  </p>
                  <details className="mb-4">
                    <summary id="technical-territory">Referência territorial · ANEEL</summary>
                    <TerritoryStudy />
                  </details>
                  <details className="mb-4">
                    <summary id="technical-demand">Demanda da residência · Energisa</summary>
                    <DemandReview
                      input={input}
                      result={currentResult}
                      onChange={(value) => change('energisa_demand', value)}
                      onLoadChange={updateLoad}
                    />
                  </details>
                  <details className="mb-4">
                    <summary id="technical-bathroom">
                      Localização de componentes no banheiro
                    </summary>
                    <BathroomStudy input={input} result={currentResult} onChange={updateRoom} />
                  </details>
                  <details>
                    <summary id="technical-circuits">Circuitos e entrada de energia</summary>
                    <CircuitStudy
                      key={calculationScope}
                      input={input}
                      result={currentResult}
                      onChange={(value) => change('circuits', value)}
                      onEntryChange={(value) => change('service_entry', value)}
                    />
                  </details>
                </details>
              </>
            )}
            <footer className="workspace-footer">
              <div className="footer-product">
                <span>EletroProjeto</span>
                <span>
                  v{APP_VERSION} · API{' '}
                  {health?.api_version ??
                    (result?.technical_context?.app_version
                      ? String(result.technical_context.app_version)
                      : 'versão não consultada')}
                </span>
              </div>
              <p className="footer-connection">
                {error
                  ? httpStatus
                    ? 'API respondeu · confira as entradas ou a operação'
                    : 'Sem comunicação com a API'
                  : currentResult || health?.status === 'ok'
                    ? 'Última conexão confirmada'
                    : 'Conexão não confirmada'}
              </p>
              <p className="footer-scope">
                Estudo preliminar de cargas residenciais. Consulte o alcance dos resultados e conte
                com a revisão de um profissional habilitado.
              </p>
            </footer>
          </main>
        </div>
      </CalculationScopeContext.Provider>
    </RequirementsContext.Provider>
  );
}
