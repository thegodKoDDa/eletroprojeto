import { spawnSync, spawn } from 'node:child_process';
import process from 'node:process';
import { basename, dirname, join } from 'node:path';
import { backend, python } from './backend-python.mjs';

const migration = spawnSync(python, ['-m', 'alembic', 'upgrade', 'head'], {
  cwd: backend,
  stdio: 'inherit',
  env: process.env,
});
if (migration.error) throw migration.error;
if (migration.status !== 0) process.exit(migration.status ?? 1);
if (process.env.ELETROPROJETO_QA_ACCOUNTS === '1') {
  if (
    !basename(dirname((process.env.DATABASE_URL ?? '').replace('sqlite:///', ''))).startsWith(
      'eletroprojeto-auth-e2e-',
    )
  )
    throw new Error('Contas QA exigem banco temporário dedicado.');
  const seed = spawnSync(
    python,
    [
      '-c',
      "from app.auth import passwords; from app.database import SessionLocal, UserRow; s=SessionLocal(); s.add_all([UserRow(id=n,username=n,active=True,password_hash=passwords.hash('qa-password-only-123')) for n in ('alice','bob')]); s.commit(); s.close()",
    ],
    { cwd: backend, stdio: 'inherit', env: process.env },
  );
  if (seed.status !== 0) process.exit(seed.status ?? 1);
}
if (process.env.ELETROPROJETO_QA_LIBRARY === '1') {
  if (
    !basename((process.env.DATABASE_URL ?? '').replace('sqlite:///', '')).startsWith(
      'eletroprojeto-e2e-',
    )
  )
    throw new Error('Biblioteca QA exige banco temporário dedicado.');
  const fixture = join(process.cwd(), 'tests', 'fixtures', 'knowledge-seed.py');
  const seed = spawnSync(
    python,
    [
      '-c',
      'import sys; from pathlib import Path; exec(compile(Path(sys.argv[1]).read_text(), sys.argv[1], "exec"))',
      fixture,
    ],
    { cwd: backend, stdio: 'inherit', env: process.env },
  );
  if (seed.status !== 0) process.exit(seed.status ?? 1);
}
const tls =
  process.env.QA_TLS_CERT && process.env.QA_TLS_KEY
    ? ['--ssl-certfile', process.env.QA_TLS_CERT, '--ssl-keyfile', process.env.QA_TLS_KEY]
    : [];
const child = spawn(
  python,
  ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8010', ...tls],
  { cwd: backend, stdio: 'inherit', env: process.env },
);
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
child.on('error', (error) => {
  throw error;
});
child.on('exit', (code) => process.exit(code ?? 1));
