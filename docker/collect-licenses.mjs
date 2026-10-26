import { readdir, mkdir, copyFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';

const source = '/web/node_modules';
const target = '/licenses/npm';
async function collect(directory, relative = '') {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const next = join(relative, entry.name);
    if (entry.isDirectory()) await collect(join(directory, entry.name), next);
    else if (entry.isFile() && /licen[cs]e|notice|copying|copyright/i.test(entry.name)) {
      const destination = join(target, next);
      await mkdir(dirname(destination), { recursive: true });
      await copyFile(join(directory, entry.name), destination);
    }
  }
}
await collect(source);
