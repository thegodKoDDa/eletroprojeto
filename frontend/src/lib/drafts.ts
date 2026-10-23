import type { Project, ProjectInput } from './api';

export const DRAFT_PREFIX = 'eletroprojeto:draft:v1:';
export type Draft = {
  schema: 1;
  updatedAt: string;
  input: ProjectInput;
  saved?: Project;
};

// Each mounted editor owns a slot: simultaneous tabs never overwrite each other.
export function draftKey(scope = 'local') {
  return `${DRAFT_PREFIX}${encodeURIComponent(scope)}:${crypto.randomUUID()}`;
}

export function readDrafts(storage: Storage, scope = 'local'): { key: string; draft: Draft }[] {
  const drafts: { key: string; draft: Draft }[] = [];
  for (let index = 0; index < storage.length; index++) {
    const key = storage.key(index);
    if (!key?.startsWith(`${DRAFT_PREFIX}${encodeURIComponent(scope)}:`)) continue;
    try {
      const value = JSON.parse(storage.getItem(key) ?? 'null');
      if (
        value?.schema === 1 &&
        typeof value.updatedAt === 'string' &&
        Number.isFinite(Date.parse(value.updatedAt)) &&
        typeof value.input?.name === 'string' &&
        Array.isArray(value.input?.environments) &&
        value.input.environments.every(
          (room: { id?: unknown; name?: unknown; loads?: unknown }) =>
            room &&
            typeof room.id === 'string' &&
            typeof room.name === 'string' &&
            Array.isArray(room.loads),
        ) &&
        (!value.saved ||
          (typeof value.saved.id === 'string' &&
            Number.isInteger(value.saved.version) &&
            value.saved.version > 0))
      )
        drafts.push({ key, draft: value });
    } catch {
      // Preserve unreadable slots; never destroy data during recovery.
    }
  }
  return drafts.sort((a, b) => b.draft.updatedAt.localeCompare(a.draft.updatedAt));
}

export function writeDraft(storage: Storage, key: string, input: ProjectInput, saved?: Project) {
  storage.setItem(
    key,
    JSON.stringify({ schema: 1, updatedAt: new Date().toISOString(), input, saved }),
  );
}
