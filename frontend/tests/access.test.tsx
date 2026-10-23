import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AccessBoundary } from '@/components/projects/AccessBoundary';
import { request, setSessionCsrf } from '@/lib/api';

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  setSessionCsrf();
});

test('remote login gates the editor, sends cookies/CSRF and logout unmounts account data', async () => {
  vi.stubEnv('NEXT_PUBLIC_AUTH_MODE', 'remote');
  let headers: HeadersInit | undefined;
  let credentials: RequestCredentials | undefined;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      headers = init?.headers;
      credentials = init?.credentials;
      return {
        ok: true,
        status: url.endsWith('/logout') ? 204 : 200,
        json: async () =>
          url.endsWith('/session')
            ? { mode: 'remote', authenticated: false, username: null, csrf: null }
            : { mode: 'remote', authenticated: true, username: 'alice', csrf: 'csrf-test' },
      };
    }),
  );
  render(
    <AccessBoundary>
      {(scope, logout) => (
        <div>
          <p>Editor {scope}</p>
          <button onClick={logout}>Sair</button>
        </div>
      )}
    </AccessBoundary>,
  );
  expect(screen.queryByText(/Editor/)).toBeNull();
  await screen.findByRole('button', { name: 'Entrar' });
  fireEvent.change(screen.getByLabelText('Usuário'), { target: { value: 'alice' } });
  fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'long-password' } });
  fireEvent.submit(screen.getByRole('button', { name: 'Entrar' }).closest('form')!);
  await screen.findByText('Editor user:alice');
  await request('/projects', { method: 'POST', body: '{}' });
  expect(credentials).toBe('include');
  expect(headers).toMatchObject({ 'X-CSRF-Token': 'csrf-test' });
  fireEvent.click(screen.getByRole('button', { name: 'Sair' }));
  await waitFor(() => expect(screen.queryByText(/Editor/)).toBeNull());
  await screen.findByRole('button', { name: 'Entrar' });
  expect(localStorage.length).toBe(0);
});
