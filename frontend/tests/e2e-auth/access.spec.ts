import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('HTTPS sessions isolate projects and local drafts across two accounts', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Entrar', exact: true })).toBeVisible();
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  async function login(username: string) {
    await page.getByLabel('Usuário', { exact: true }).fill(username);
    await page.getByLabel('Senha', { exact: true }).fill('qa-password-only-123');
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Sair da conta' })).toBeVisible();
  }
  await login('alice');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill('Casa privada de Alice');
  await page.getByLabel('Município', { exact: true }).fill('São Paulo');
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const cookies = await page.context().cookies();
  expect(cookies.find((cookie) => cookie.name === 'eletroprojeto_session')).toMatchObject({
    secure: true,
    httpOnly: true,
    sameSite: 'Strict',
  });
  // Name edits pause autosave, so this stays a private unsent draft.
  await page.getByLabel('Nome do projeto', { exact: true }).fill('Rascunho privado de Alice');
  await page.getByRole('button', { name: 'Sair da conta' }).click();
  await login('bob');
  await expect(page.getByRole('region', { name: 'Rascunhos recuperados' })).toHaveCount(0);
  await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
  await expect(page.getByText('Casa privada de Alice', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Sair da conta' }).click();
  await login('alice');
  await expect(page.getByRole('region', { name: 'Rascunhos recuperados' })).toContainText(
    'Rascunho privado de Alice',
  );
});
