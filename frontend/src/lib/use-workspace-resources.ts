'use client';

import { useCallback, useEffect, useState } from 'react';
import { request, type CatalogItem, type UtilityInfo } from './api';
import type { components } from './api.generated';

type Resources = {
  catalog: CatalogItem[];
  utilities: UtilityInfo[];
  states: string[];
  requirements: Record<string, components['schemas']['FieldRequirement']>;
  health?: components['schemas']['HealthInfo'];
};

/** Independent resources fail separately; retry never remounts the project. */
export function useWorkspaceResources() {
  const [attempt, setAttempt] = useState(0);
  const [issues, setIssues] = useState<string[]>([]);
  const [resources, setResources] = useState<Resources>({
    catalog: [],
    utilities: [],
    states: [],
    requirements: {},
  });
  useEffect(() => {
    const controller = new AbortController();
    async function load<K extends keyof Resources>(key: K, path: string, message: string) {
      try {
        const value = await request<Resources[K]>(path, { signal: controller.signal });
        if (!controller.signal.aborted) setResources((old) => ({ ...old, [key]: value }));
      } catch {
        if (controller.signal.aborted) return;
        if (key === 'health') setResources((old) => ({ ...old, health: undefined }));
        setIssues((old) => [...old, message]);
      }
    }
    void Promise.all([
      load('health', '/health', 'Não foi possível confirmar a conexão com a API.'),
      load('requirements', '/validation/requirements', 'Requisitos dos formulários indisponíveis.'),
      load('states', '/locations/states', 'Lista de estados indisponível.'),
      load('utilities', '/utilities', 'Consulta de distribuidoras indisponível.'),
      load('catalog', '/equipment', 'Catálogo de equipamentos indisponível.'),
    ]);
    return () => controller.abort();
  }, [attempt]);
  const retry = useCallback(() => {
    setIssues([]);
    setAttempt((value) => value + 1);
  }, []);
  return { ...resources, initializationIssues: issues, retry };
}
