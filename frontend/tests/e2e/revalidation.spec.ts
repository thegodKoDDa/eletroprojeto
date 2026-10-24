import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('reference review previews saved inputs and explicitly records a new history version', async ({
  page,
  request,
}) => {
  const api = 'http://127.0.0.1:8010/api/v1';
  const response = await request.post(`${api}/projects`, {
    data: {
      name: 'Revisão QA',
      municipality: 'Cidade QA',
      environments: [
        {
          name: 'Sala',
          loads: [
            {
              name: 'Carga manual',
              unit_power_w: '123.456789',
              quantity: 3,
              power_origin: 'nameplate',
              source: 'Valor manual QA',
            },
          ],
        },
      ],
    },
  });
  expect(response.ok()).toBe(true);
  const saved = await response.json();
  // Force only the review flag; preview/registration use the actual API and QA database.
  await page.route('**/projects/*/revalidation', async (route) => {
    const upstream = await route.fetch();
    await route.fulfill({
      response: upstream,
      json: {
        ...(await upstream.json()),
        requires_revalidation: true,
        previous_engine_version: 'histórico QA',
      },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
  await page.getByRole('button', { name: 'Revisão QA', exact: true }).click();
  await page.getByLabel('Mais ações do projeto').click();
  await page.getByRole('button', { name: 'Verificar referências', exact: true }).click();
  const review = page.getByRole('region', { name: 'Revisão das referências do projeto' });
  await expect(review).toBeVisible();
  expect((await (await request.get(`${api}/projects/${saved.id}`)).json()).version).toBe(1);
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  await review.getByRole('button', { name: 'Registrar revalidação com os dados salvos' }).click();
  await expect(page.getByTestId('project-message')).toContainText('Revalidação registrada');
  const updated = await (await request.get(`${api}/projects/${saved.id}`)).json();
  expect(updated.version).toBe(2);
  expect(updated.environments).toEqual(saved.environments);
  const history = await (await request.get(`${api}/projects/${saved.id}/history`)).json();
  expect(history.map((row: { version: number }) => row.version)).toEqual([2, 1]);
  expect(history[0].result.installed_power.value).toBe('370.370367');
  expect(history[1].result.installed_power.value).toBe('370.370367');
  await expect(review).toHaveCount(0);
});
