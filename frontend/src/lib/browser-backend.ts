const PYODIDE_INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v0.27.4/full/';
const STORE_KEY = 'eletroprojeto.browser.store.v1';
const BACKUP_KEY = 'eletroprojeto.browser.backup.v1';

export type BrowserDispatchResponse = {
  status: number;
  headers: Record<string, string>;
  body: unknown;
  body_base64: string | null;
  store_json: string | null;
};

type BrowserDispatcher = (
  method: string,
  path: string,
  body: string | null,
  headers: Record<string, string>,
  storeJson: string | null,
) => Promise<BrowserDispatchResponse> | BrowserDispatchResponse;

type PyodideInstance = {
  loadPackage: (names: string[]) => Promise<void>;
  unpackArchive: (data: ArrayBuffer, format: string, options?: { extractDir?: string }) => void;
  runPythonAsync: (code: string) => Promise<unknown>;
  globals: {
    get: (name: string) => (...args: unknown[]) => {
      toJs: (options?: { dict_converter?: typeof Object.fromEntries }) => BrowserDispatchResponse;
      destroy?: () => void;
    };
  };
};

declare global {
  interface Window {
    loadPyodide?: (options: { indexURL: string }) => Promise<PyodideInstance>;
    __ELETROPROJETO_BROWSER_DISPATCH__?: BrowserDispatcher;
  }
}

export function isBrowserRuntime(): boolean {
  if (process.env.NEXT_PUBLIC_BROWSER_RUNTIME === '1') return true;
  if (typeof window === 'undefined') return false;
  const host = window.location?.hostname || '';
  return /\.github\.io$/i.test(host) || window.location?.protocol === 'file:';
}

function resolveBasePath(): string {
  if (process.env.NEXT_PUBLIC_BASE_PATH) return process.env.NEXT_PUBLIC_BASE_PATH;
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/eletroprojeto')) {
    return '/eletroprojeto';
  }
  return '';
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[data-pyodide-src="${src}"]`);
    if (existing) {
      if (typeof window.loadPyodide === 'function') {
        resolve();
        return;
      }
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener(
        'error',
        () => reject(new Error('Falha ao carregar motor Python.')),
        {
          once: true,
        },
      );
      return;
    }
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.dataset.pyodideSrc = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Falha ao carregar o motor Python no navegador.'));
    document.head.appendChild(script);
  });
}

let dispatcherPromise: Promise<BrowserDispatcher> | undefined;

async function getDispatcher(): Promise<BrowserDispatcher> {
  if (typeof window !== 'undefined' && window.__ELETROPROJETO_BROWSER_DISPATCH__) {
    return window.__ELETROPROJETO_BROWSER_DISPATCH__;
  }
  if (!dispatcherPromise) {
    dispatcherPromise = (async () => {
      if (typeof window.loadPyodide !== 'function') {
        await loadScript(`${PYODIDE_INDEX_URL}pyodide.js`);
      }
      if (typeof window.loadPyodide !== 'function') {
        throw new Error('Motor Python indisponível neste navegador.');
      }
      const pyodide = await window.loadPyodide({ indexURL: PYODIDE_INDEX_URL });
      await pyodide.loadPackage(['pydantic', 'tzdata']);
      const bundleResponse = await fetch(`${resolveBasePath()}/pyodide-app.zip`);
      if (!bundleResponse.ok) {
        throw new Error('Pacote do motor Python não encontrado.');
      }
      const bundleBuffer = await bundleResponse.arrayBuffer();
      pyodide.unpackArchive(bundleBuffer, 'zip', { extractDir: '/eletroprojeto' });
      await pyodide.runPythonAsync(`
import json, sys
if "/eletroprojeto" not in sys.path:
    sys.path.insert(0, "/eletroprojeto")
from app.browser_runtime import dispatch_request as _dispatch_request

def _eletroprojeto_dispatch(method, path, body, headers_json, store_json):
    headers = json.loads(headers_json) if headers_json else {}
    return json.dumps(_dispatch_request(method, path, body, headers, store_json), ensure_ascii=False)
`);
      const pyDispatch = pyodide.globals.get('_eletroprojeto_dispatch') as unknown as (
        method: string,
        path: string,
        body: string | null,
        headersJson: string,
        storeJson: string | null,
      ) => string;
      return (
        method: string,
        path: string,
        body: string | null,
        headers: Record<string, string>,
        storeJson: string | null,
      ) => {
        const raw = pyDispatch(method, path, body, JSON.stringify(headers), storeJson);
        return JSON.parse(String(raw)) as BrowserDispatchResponse;
      };
    })().catch((err) => {
      dispatcherPromise = undefined;
      throw err;
    });
  }
  return dispatcherPromise;
}

function readStore(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(STORE_KEY);
  } catch {
    return null;
  }
}

function writeStore(nextStoreJson: string): void {
  if (typeof window === 'undefined') return;
  const previous = window.localStorage.getItem(STORE_KEY);
  if (previous !== null) {
    window.localStorage.setItem(BACKUP_KEY, previous);
  }
  window.localStorage.setItem(STORE_KEY, nextStoreJson);
}

let queue: Promise<unknown> = Promise.resolve();

function serialize<T>(task: () => Promise<T>): Promise<T> {
  const run = async () => {
    if (typeof navigator !== 'undefined' && navigator.locks?.request) {
      return navigator.locks.request('eletroprojeto.browser.store', task);
    }
    return task();
  };
  const next = queue.then(run, run);
  queue = next.then(
    () => undefined,
    () => undefined,
  );
  return next;
}

function decodeBase64(b64: string): Uint8Array<ArrayBuffer> {
  const binary = atob(b64);
  const buffer = new ArrayBuffer(binary.length);
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function abortError(): Error {
  if (typeof DOMException !== 'undefined') {
    return new DOMException('The operation was aborted.', 'AbortError');
  }
  const err = new Error('The operation was aborted.');
  err.name = 'AbortError';
  return err;
}

export async function fetchBrowserApi(path: string, init?: RequestInit): Promise<Response> {
  if (init?.signal?.aborted) throw abortError();
  const method = (init?.method ?? 'GET').toUpperCase();
  const headers = Object.fromEntries(new Headers(init?.headers));
  const body = typeof init?.body === 'string' ? init.body : null;
  const isMutation = method !== 'GET' && method !== 'HEAD';

  const execute = async () => {
    if (init?.signal?.aborted) throw abortError();
    const dispatch = await getDispatcher();
    if (init?.signal?.aborted) throw abortError();
    const storeJson = readStore();
    const result = await dispatch(method, path, body, headers, storeJson);
    if (init?.signal?.aborted) throw abortError();
    if (result.store_json !== null && result.store_json !== undefined) {
      writeStore(result.store_json);
    }
    if (result.status === 204) {
      return new Response(null, { status: 204, headers: result.headers });
    }
    if (result.body_base64) {
      return new Response(decodeBase64(result.body_base64), {
        status: result.status,
        headers: result.headers,
      });
    }
    return new Response(JSON.stringify(result.body), {
      status: result.status,
      headers: result.headers,
    });
  };

  return isMutation ? serialize(execute) : execute();
}
