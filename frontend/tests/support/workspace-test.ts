import { test as base, expect } from '@playwright/test';

/** Existing journey regressions exercise the unchanged exploration presentation.
 * Fresh-session/profile selection has its own browser tests without this fixture.
 */
export const test = base.extend({
  page: async ({ page }, run) => {
    await page.addInitScript(() => {
      for (const owner of ['local', 'user:alice', 'user:bob']) {
        const key = `eletroprojeto:experience:v1:${encodeURIComponent(owner)}`;
        if (!sessionStorage.getItem(key)) sessionStorage.setItem(key, 'explore');
      }
    });
    await run(page);
  },
});
export { expect };
