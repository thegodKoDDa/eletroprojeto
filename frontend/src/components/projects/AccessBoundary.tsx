'use client';
import { useEffect, useState, type ReactNode, type FormEvent } from 'react';
import { request, setSessionCsrf } from '@/lib/api';
import type { components } from '@/lib/api.generated';

type Access = components['schemas']['AccessSession'];

export function AccessBoundary({
  children,
}: {
  children: (scope: string, logout?: () => Promise<void>) => ReactNode;
}) {
  const [access, setAccess] = useState<Access>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const remote = process.env.NEXT_PUBLIC_AUTH_MODE === 'remote';
  useEffect(() => {
    if (!remote) return;
    const controller = new AbortController();
    request<Access>('/auth/session', { signal: controller.signal })
      .then((session) => {
        if (controller.signal.aborted) return;
        if (session.mode !== 'remote') throw new Error('Modo de acesso incompatível.');
        setSessionCsrf(session.csrf ?? undefined);
        setAccess(session);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError('Não foi possível consultar o acesso. Tente novamente.');
      });
    return () => controller.abort();
  }, [remote, attempt]);
  useEffect(() => {
    if (!remote) return;
    const expired = () => {
      setSessionCsrf(undefined);
      setAccess({ mode: 'remote', authenticated: false, username: null, csrf: null });
      setError('Sua sessão expirou. Entre novamente para recuperar a edição local.');
    };
    window.addEventListener('eletroprojeto:session-expired', expired);
    return () => window.removeEventListener('eletroprojeto:session-expired', expired);
  }, [remote]);
  if (!remote) return children('local');
  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true);
    setError('');
    try {
      const session = await request<Access>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: values.get('username'),
          password: values.get('password'),
        }),
      });
      form.reset();
      setSessionCsrf(session.csrf ?? undefined);
      setAccess(session);
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (access?.authenticated)
    return children(`user:${access.username}`, async () => {
      await request('/auth/logout', { method: 'POST' });
      setSessionCsrf(undefined);
      setAccess({ ...access, authenticated: false, csrf: null });
    });
  return (
    <main className="mx-auto max-w-lg p-8">
      <h1 className="text-2xl font-semibold">Entrar no EletroProjeto</h1>
      {error && (
        <p role="alert" className="my-4">
          {error}
        </p>
      )}
      {!access ? (
        error ? (
          <button
            className="btn"
            onClick={() => {
              setError('');
              setAttempt((value) => value + 1);
            }}
          >
            Tentar consultar acesso novamente
          </button>
        ) : (
          <p role="status">Consultando acesso…</p>
        )
      ) : (
        <form onSubmit={login} className="mt-6 grid gap-4">
          <label>
            Usuário
            <input name="username" autoComplete="username" required maxLength={200} />
          </label>
          <label>
            Senha
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={1024}
            />
          </label>
          <button className="btn" disabled={busy}>
            {busy ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      )}
    </main>
  );
}
