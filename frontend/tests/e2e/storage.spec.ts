import { test, expect } from '../support/workspace-test';

test('lost first-save response and immediate reload retain input without duplicate projects', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const name = `Retorno seguro ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Município informado');
  await page
    .getByLabel('Salvar automaticamente após o primeiro salvamento', { exact: true })
    .uncheck();
  let loseResponse = true;
  await page.route('**/api/v1/projects', async (route) => {
    if (route.request().method() === 'POST' && loseResponse) {
      loseResponse = false;
      const response = await route.fetch();
      expect(response.status()).toBe(201);
      await route.abort('failed');
    } else await route.continue();
  });
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Não foi possível conectar');
  const notes = 'Última edição antes de recarregar, sem aguardar o debounce.';
  await page.getByLabel('Observações', { exact: true }).fill(notes);
  await page.reload();
  await page.getByRole('button', { name: 'Continuar rascunho', exact: true }).click();
  await expect(page.getByLabel('Observações', { exact: true })).toHaveValue(notes);
  await page
    .getByLabel('Salvar automaticamente após o primeiro salvamento', { exact: true })
    .uncheck();
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Primeiro salvamento recuperado');
  await expect(page.getByLabel('Observações', { exact: true })).toHaveValue(notes);
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const all = await (await request.get('http://127.0.0.1:8010/api/v1/projects')).json();
  const matches = all.filter((row: { name: string }) => row.name === name);
  expect(matches).toHaveLength(1);
  expect(matches[0].notes).toBe(notes);
  const history = await (
    await request.get(`http://127.0.0.1:8010/api/v1/projects/${matches[0].id}/history`)
  ).json();
  expect(history).toHaveLength(2);
  const summaryResponse = page.waitForResponse((response) =>
    response.url().includes('/projects/summaries?'),
  );
  await page.locator('aside').getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  const summaries = await (await summaryResponse).json();
  expect(summaries.every((row: object) => !('environments' in row) && !('notes' in row))).toBe(
    true,
  );
  await page.getByRole('button', { name, exact: true }).click();
  await expect(page.getByLabel('Observações', { exact: true })).toHaveValue(notes);
  // A lost "save as new" also keeps its operation ID and the intended copy name.
  loseResponse = true;
  await page.getByLabel('Mais ações do projeto').click();
  await page.getByRole('button', { name: 'Salvar como novo', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Não foi possível conectar');
  const copyNotes = notes + ' Cópia com edição posterior.';
  await page.getByLabel('Observações', { exact: true }).fill(copyNotes);
  await page.getByLabel('Mais ações do projeto').click();
  await page.getByRole('button', { name: 'Salvar como novo', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Primeiro salvamento recuperado');
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(`${name} · cópia`);
  await expect(page.getByLabel('Observações', { exact: true })).toHaveValue(copyNotes);
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const afterCopy = await (await request.get('http://127.0.0.1:8010/api/v1/projects')).json();
  expect(afterCopy.filter((row: { name: string }) => row.name === `${name} · cópia`)).toHaveLength(
    1,
  );
  expect(afterCopy.find((row: { name: string }) => row.name === name).notes).toBe(notes);
});
