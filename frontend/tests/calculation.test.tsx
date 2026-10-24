import { StrictMode, createElement } from 'react';
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { useCalculation } from '../src/lib/use-calculation';
import type { ProjectInput } from '../src/lib/api';
const input: ProjectInput = {
  analysis_scope: 'installed',
  name: 'Casa',
  municipality: 'Cidade',
  built_area_m2: '60',
  state: 'SP',
  utility: 'unconfirmed',
  residence_type: 'Casa',
  floors: 1,
  reference_voltage_v: '220',
  notes: '',
};
beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

test('hides stale results immediately when input changes', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ installed_power: { value: '7500' } }),
    }),
  );
  const { result, rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(result.current.result?.installed_power.value).toBe('7500');
  rerender({ data: { ...input, utility: 'energisa_sul_sudeste' as const } });
  expect(result.current.result).toBeUndefined();
  expect(result.current.loading).toBe(true);
});

test('debounces edits and ignores obsolete responses', async () => {
  let resolveOld!: (value: unknown) => void;
  const fetch = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveOld = resolve;
        }),
    )
    .mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ installed_power: { value: '5500' } }),
    });
  vi.stubGlobal('fetch', fetch);
  const { result, rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  rerender({ data: { ...input, utility: 'energisa_sul_sudeste' as const } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  await act(async () => {
    resolveOld({
      ok: true,
      status: 200,
      json: async () => ({ installed_power: { value: '7500' } }),
    });
  });
  expect(result.current.result?.installed_power.value).toBe('5500');
  expect(fetch).toHaveBeenCalledTimes(2);
});

test('shows API validation errors for the current input', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: [{ loc: ['body', 'name'], msg: 'Campo inválido' }] }),
    }),
  );
  const { result } = renderHook(() => useCalculation(input));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(result.current.error).toContain('name: Campo inválido');
  expect(result.current.result).toBeUndefined();
});

test('retains a labelled display snapshot without exposing it as a current result', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ installed_power: { value: '7500' } }),
    }),
  );
  const { result, rerender } = renderHook(({ data, scope }) => useCalculation(data, scope), {
    initialProps: { data: input, scope: 'project-a' },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  const display = result.current.displayResult;
  rerender({ data: { ...input, utility: 'energisa_sul_sudeste' as const }, scope: 'project-a' });
  expect(result.current.result).toBeUndefined();
  expect(result.current.displayResult).toBe(display);
  expect(result.current.stale).toBe(true);
  rerender({ data: input, scope: 'project-b' });
  expect(result.current.displayResult).toBeUndefined();
});

test('identical inputs do not loop or refetch while idle', async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ installed_power: { value: '0' } }),
  });
  vi.stubGlobal('fetch', fetch);
  const { rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  rerender({ data: { ...input, notes: 'Anotação' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000);
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('rapid edits send only the final payload', async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ installed_power: { value: '0' } }),
  });
  vi.stubGlobal('fetch', fetch);
  const { rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  for (const area of ['1', '12', '120']) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    rerender({
      data: {
        ...input,
        environments: [
          {
            name: 'Sala',
            type: 'living',
            area_m2: area,
            perimeter_m: '14',
            lighting_points: 1,
            outlets: 2,
          },
        ],
      },
    });
  }
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(JSON.parse(fetch.mock.calls[0][1].body).environments[0].area_m2).toBe('120');
});

test('Strict Mode cleans up the first effect and sends one settled request', async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ installed_power: { value: '0' } }),
  });
  vi.stubGlobal('fetch', fetch);
  renderHook(() => useCalculation(input), {
    wrapper: ({ children }) => createElement(StrictMode, null, children),
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('changing requested operation invalidates diagnostics and recalculates the same loads', async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ installed_power: { value: '7500' }, notifications: [] }),
  });
  vi.stubGlobal('fetch', fetch);
  const { result, rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  rerender({ data: { ...input, analysis_scope: 'current' } });
  expect(result.current.result).toBeUndefined();
  expect(result.current.notifications).toEqual([]);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(JSON.parse(fetch.mock.calls[1][1].body).analysis_scope).toBe('current');
  expect(result.current.result?.installed_power.value).toBe('7500');
});

test('demand settings invalidate the current result and are included in recalculation', async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ installed_power: { value: '0' } }),
  });
  vi.stubGlobal('fetch', fetch);
  const { result, rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  rerender({
    data: {
      ...input,
      energisa_demand: {
        enabled: true,
        unit_type: 'individual_residential',
        confirmed_absent_groups: [],
      },
    },
  });
  expect(result.current.result).toBeUndefined();
  expect(result.current.stale).toBe(true);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(JSON.parse(fetch.mock.calls[1][1].body).energisa_demand.enabled).toBe(true);
});

test.each([
  {
    circuits: [
      {
        id: 'circuit',
        name: 'Circuito',
        purpose: 'sockets' as const,
        method: 'unknown' as const,
        scope_confirmed: false,
        voltage_drop_model_confirmed: false,
        overload_duration_confirmed: false,
        supply_origin: 'unknown' as const,
        length_m: '30',
        protections: {
          cable_k: '115',
          earthing_system: 'unknown' as const,
          rcd_type_compatible_confirmed: false,
        },
      },
    ],
  },
  {
    service_entry: {
      network: '220_127' as const,
      route: 'underground' as const,
      insulation: 'unknown' as const,
      scope_confirmed: false,
      special_loads_reviewed: false,
    },
  },
])('circuit and entry edits invalidate current results immediately', async (patch) => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ installed_power: { value: '0' } }),
  });
  vi.stubGlobal('fetch', fetch);
  const { result, rerender } = renderHook(({ data }) => useCalculation(data), {
    initialProps: { data: input },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  rerender({ data: { ...input, ...patch } });
  expect(result.current.result).toBeUndefined();
  expect(result.current.stale).toBe(true);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(JSON.parse(fetch.mock.calls[1][1].body)).toMatchObject(patch);
});
