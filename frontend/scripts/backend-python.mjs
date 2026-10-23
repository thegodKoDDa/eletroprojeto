import { fileURLToPath, URL } from 'node:url';
import process from 'node:process';
import { join } from 'node:path';

export const backend = fileURLToPath(new URL('../../backend/', import.meta.url));
export const python =
  process.env.ELETROPROJETO_PYTHON ??
  join(backend, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
