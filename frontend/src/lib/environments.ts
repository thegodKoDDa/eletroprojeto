import type { Environment } from './api';

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
