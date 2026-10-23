import type { components } from './api.generated';
export type ProjectInput = components['schemas']['ProjectInput'];
export type Project = components['schemas']['Project'];
export type Environment = components['schemas']['Environment'];
export type Load = components['schemas']['Load'];
export type CalculationResult = components['schemas']['CalculationResult'];
export const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
let csrfToken: string | undefined;
export function setSessionCsrf(value?: string) {
  csrfToken = value;
}
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public notifications: components['schemas']['Notification'][] = [],
  ) {
    super(message);
  }
}
async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  try {
    const response = await fetch(`${API}${path}`, {
      ...init,
      credentials: 'include',
      headers: { ...init?.headers, ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}) },
    });
    if (response.status === 401 && !path.startsWith('/auth/') && typeof window !== 'undefined')
      window.dispatchEvent(new Event('eletroprojeto:session-expired'));
    return response;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error;
    throw new Error('Não foi possível conectar ao serviço. Tente novamente.');
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetchApi(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new APIError(
      Array.isArray(detail)
        ? detail
            .map(
              (item: { loc: string[]; msg: string }) =>
                `${item.loc.slice(1).join('.')}: ${item.msg}`,
            )
            .join('\n')
        : typeof detail === 'string'
          ? detail
          : `Falha na API (${response.status})`,
      response.status,
      body?.notifications ?? [],
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export function projectInputs(project: Project): ProjectInput {
  const { id, version, created_at, updated_at, standards_version, deleted_at, ...inputs } = project;
  void id;
  void version;
  void created_at;
  void updated_at;
  void standards_version;
  void deleted_at;
  return inputs;
}
export type CatalogItem = components['schemas']['CatalogItem'];
export type TechnicalParameters = components['schemas']['TechnicalParameters'];

export type CalculationMemory = components['schemas']['Memory'];

export type UtilityInfo = components['schemas']['UtilityInfo'];

export async function requestReport(
  format: 'pdf' | 'json',
  body: components['schemas']['PDFExportInput'],
): Promise<Blob> {
  const response = await fetchApi(`/reports/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `Não foi possível exportar ${format.toUpperCase()} (${response.status}). Confira os campos.`,
    );
  }
  if (!response.headers.get('Content-Type')?.startsWith(`application/${format}`))
    throw new Error(`A API não retornou um ${format.toUpperCase()} válido.`);
  return response.blob();
}
