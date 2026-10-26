import type { CalculationResult, ProjectInput } from './api';
import type { components } from './api.generated';
type Requirements = Record<string, components['schemas']['FieldRequirement']>;
function filled(value: string | null | undefined, field: string, requirements: Requirements) {
  const maximum = requirements[field]?.max_length;
  return !!value?.trim() && (maximum == null || value.length <= maximum);
}

/** Chooses an existing form control; no energy calculation or default is introduced here. */
export function energyCompletionTarget(
  input: Pick<ProjectInput, 'environments'>,
  result?: CalculationResult,
  id?: string,
) {
  const loadId =
    id ??
    result?.energy_unknown_load_ids?.[0] ??
    input.environments?.flatMap((room) => room.loads ?? [])[0]?.id;
  const load = input.environments
    ?.flatMap((room) => room.loads ?? [])
    .find((item) => item.id === loadId);
  if (!loadId || !load) return 'add-environment';
  const params = load.parameters;
  let field = 'parameters.monthly_energy_kwh';
  if (result?.unknown_load_ids?.includes(loadId)) {
    field =
      params?.power_mode === 'mechanical'
        ? params.mechanical_power == null
          ? 'parameters.mechanical_power'
          : 'parameters.efficiency'
        : 'unit_power_w';
  } else if (params?.usage_hours_per_day == null) {
    field = 'parameters.usage_hours_per_day';
  } else if (params.usage_days_per_month == null) {
    field = 'parameters.usage_days_per_month';
  }
  return `load.${loadId}.${field}`;
}

export type JourneyStep = {
  id: string;
  title: string;
  help: string;
  target: string;
  complete: boolean;
};

/** Completion describes the current estimate only, never normative conformity. */
export function estimateJourney(
  input: ProjectInput,
  result: CalculationResult | undefined,
  reviewedDigest: string | undefined,
  saved: boolean,
  requirements: Requirements = {},
): JourneyStep[] {
  const rooms = input.environments ?? [];
  const loads = rooms.flatMap((room) => room.loads ?? []);
  const identification =
    filled(input.name, 'project.name', requirements) &&
    filled(input.municipality, 'project.municipality', requirements) &&
    !!input.state &&
    !result?.notifications?.some(
      (notice) =>
        notice.category === 'error' &&
        ['project.name', 'project.state', 'project.municipality'].includes(notice.target_id ?? ''),
    );
  const inventory =
    loads.length > 0 &&
    rooms.every((room) => filled(room.name, 'environment.name', requirements)) &&
    loads.every((load) => filled(load.name, 'load.name', requirements));
  const incompleteRoom = rooms.find((room) => !filled(room.name, 'environment.name', requirements));
  const incompleteLoad = loads.find((load) => !filled(load.name, 'load.name', requirements));
  const energy =
    inventory &&
    result?.monthly_energy?.value != null &&
    result.energy_unknown_load_ids?.length === 0;
  const reviewed = energy && !!result && reviewedDigest === result.input_digest;
  return [
    {
      id: 'identity',
      title: 'Identificar o projeto',
      help: 'Preencha nome, estado e município. A tarifa é opcional e permite estimar o custo.',
      target: !filled(input.name, 'project.name', requirements)
        ? 'project.name'
        : !filled(input.municipality, 'project.municipality', requirements)
          ? 'project.municipality'
          : 'project.state',
      complete: identification,
    },
    {
      id: 'inventory',
      title: 'Cadastrar ambientes e aparelhos',
      help: 'Adicione os ambientes e os aparelhos que deseja incluir. Confira nomes e quantidades; você pode ampliar a lista depois.',
      target: incompleteRoom
        ? `room.${incompleteRoom.id}.name`
        : incompleteLoad
          ? `load.${incompleteLoad.id}.name`
          : 'add-environment',
      complete: inventory,
    },
    {
      id: 'energy',
      title: 'Informar o uso dos aparelhos',
      help: result
        ? 'Em cada aparelho, informe os kWh mensais da etiqueta ou a potência e os horários efetivos de uso. Não sabe? Deixe pendente, sem inventar valores.'
        : 'Aguarde o cálculo atual. Os dados anteriores não concluem esta tarefa.',
      target: energyCompletionTarget(input, result),
      complete: energy,
    },
    {
      id: 'review',
      title: 'Conferir a estimativa',
      help: 'Confira aparelhos, consumo e avisos nos resultados. Ao terminar, use Já conferi a estimativa. O custo depende da tarifa e não representa a fatura completa.',
      target: 'results',
      complete: reviewed,
    },
    {
      id: 'save',
      title: 'Salvar o projeto',
      help: 'Use Salvar projeto para guardar esta edição. Depois você pode reabrir, revisar ou exportar o relatório.',
      target: 'save-project',
      complete: saved,
    },
  ];
}
