import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import { defineConfig } from 'eslint/config';

export default defineConfig([
  {
    ignores: [
      '.next/**',
      'out/**',
      'build/**',
      'next-env.d.ts',
      'src/lib/api.generated.ts',
      'playwright-report/**',
      'test-results/**',
    ],
  },
  { files: ['**/*.mjs'], ...js.configs.recommended },
  ...tseslint.configs.recommended,
  { files: ['src/**/*.{ts,tsx}'], ...reactHooks.configs.flat.recommended },
]);
