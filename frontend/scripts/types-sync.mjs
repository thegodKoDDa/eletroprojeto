import { spawnSync } from 'node:child_process';
import { fileURLToPath, URL } from 'node:url';
import process from 'node:process';
import { backend, python } from './backend-python.mjs';

const frontend = fileURLToPath(new URL('../', import.meta.url));
for (const [command, args, cwd] of [
  [python, ['export_openapi.py'], backend],
  [
    process.execPath,
    [
      'node_modules/openapi-typescript/bin/cli.js',
      '../backend/openapi.json',
      '-o',
      'src/lib/api.generated.ts',
    ],
    frontend,
  ],
]) {
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', env: process.env });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
