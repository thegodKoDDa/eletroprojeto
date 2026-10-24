import type { Environment, ProjectInput } from './api';

/** Remove only instance associations belonging to loads the user removed. */
export function removeProjectLoads(input: ProjectInput, ids: readonly string[]): ProjectInput {
  const removed = new Set(ids);
  return {
    ...input,
    environments: input.environments?.map((room) => ({
      ...room,
      loads: room.loads?.filter((load) => !removed.has(load.id!)),
    })),
    circuits: input.circuits?.map((circuit) => ({
      ...circuit,
      load_ids: circuit.load_ids?.filter((id) => !removed.has(id)),
    })),
  };
}

/** Copy project data, preserving catalog snapshots while renewing instance IDs. */
export function duplicateEnvironment(
  source: Environment,
  environments: Environment[],
  id: string,
): Environment {
  const copy = structuredClone(source);
  const names = new Set(environments.map((room) => room.name));
  let index = 1;
  let name: string;
  do {
    const suffix = index === 1 ? ' — cópia' : ` — cópia ${index}`;
    name = `${source.name.slice(0, 200 - suffix.length)}${suffix}`;
    index += 1;
  } while (names.has(name));
  return {
    ...copy,
    id,
    name,
    loads: copy.loads?.map((load) => ({ ...load, id: crypto.randomUUID() })) ?? [],
  };
}
