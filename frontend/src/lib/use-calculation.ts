'use client';
import { inputIdentity } from './input-identity';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { components } from './api.generated';
import { request, APIError, type CalculationResult, type ProjectInput } from './api';

export function useCalculation(input: ProjectInput, scope = 'default', enabled = true) {
  const key = useMemo(
    () =>
      inputIdentity(
        {
          analysis_scope: 'installed',
          energy_tariff_brl_per_kwh: input.energy_tariff_brl_per_kwh ?? null,
          name: input.name,
          property_stage: input.property_stage ?? null,
          residence_type: input.residence_type ?? null,
          utility_name: input.utility_name ?? null,
          built_area_m2: input.built_area_m2 === '' ? null : input.built_area_m2,
          state: input.state ?? 'SP',
          municipality: input.municipality ?? '',
          utility: input.utility ?? 'unconfirmed',
          environments: input.environments ?? [],
        },
        'CalculationInput',
      ),
    [
      input.energy_tariff_brl_per_kwh,
      input.name,
      input.property_stage,
      input.residence_type,
      input.utility_name,
      input.built_area_m2,
      input.state,
      input.municipality,
      input.utility,
      input.environments,
    ],
  );
  const sequence = useRef(0);
  const [state, setState] = useState<{
    key: string;
    scope: string;
    result?: CalculationResult;
    error?: string;
    notifications?: components['schemas']['Notification'][];
    httpStatus?: number;
  }>({ key: '', scope });
  const [lastSuccess, setLastSuccess] = useState<{ scope: string; result: CalculationResult }>();
  useEffect(() => {
    if (!enabled) return;
    const current = ++sequence.current;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      request<CalculationResult>('/calculations/full', {
        method: 'POST',
        body: key,
        signal: controller.signal,
      })
        .then((result) => {
          if (sequence.current === current && !controller.signal.aborted) {
            setState({ key, scope, result });
            setLastSuccess({ scope, result });
          }
        })
        .catch((error) => {
          if (!controller.signal.aborted && sequence.current === current)
            setState({
              key,
              scope,
              error: String(error.message),
              notifications: error instanceof APIError ? error.notifications : [],
              httpStatus: error instanceof APIError ? error.status : undefined,
            });
        });
    }, 400);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [key, scope, enabled]);
  const current = enabled && state.key === key && state.scope === scope;
  return {
    result: current ? state.result : undefined,
    // Retain DOM/layout during editing, but never expose this snapshot as current.
    displayResult:
      current && state.result
        ? state.result
        : lastSuccess?.scope === scope
          ? lastSuccess.result
          : undefined,
    httpStatus: current ? state.httpStatus : undefined,
    notifications: current ? (state.notifications ?? state.result?.notifications ?? []) : [],
    error: current ? state.error : undefined,
    loading: enabled && !current,
    stale: !(current && state.result),
  };
}
