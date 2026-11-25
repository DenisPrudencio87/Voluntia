import { test, expect, Page } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('..');
const credentials = JSON.parse(
  fs.readFileSync(path.join(root, '.local/e2e-credentials.json'), 'utf8'),
);
async function login(page: Page, email: string, password: string) {
  await page.goto('/acceso');
  await page.getByLabel('Correo electrónico', { exact: true }).fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Mi panel', exact: true })).toBeVisible();
}
async function screenshot(page: Page, name: string) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({
    path: path.join(root, '.local', 'audit-' + name + '.png'),
    fullPage: true,
  });
}

test('correo real en Mailpit, confirmaciones y cambio de contraseña', async ({
  page,
  request,
}, info) => {
  const email = `audit-${info.project.name}-${Date.now()}@example.org`;
  const password = 'Ficticia-Auditoria-2026!';
  await page.goto('/registro');
  await page.getByLabel('Correo electrónico', { exact: true }).fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByLabel('Confirmar contraseña').fill(password);
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click();
  await expect(page.getByText(/Si el correo puede registrarse/)).toBeVisible();
  await page.goto('/reenviar');
  await page.getByLabel('Correo electrónico', { exact: true }).fill(email);
  await page.getByRole('button', { name: 'Reenviar enlace' }).click();
  await expect(page.getByText('Si corresponde, recibirás un nuevo enlace.')).toBeVisible();
  async function token(subject: string) {
    const messages = await (await request.get('http://127.0.0.1:8025/api/v1/messages')).json();
    const mail = messages.messages.find(
      (m: any) => m.To.some((t: any) => t.Address === email) && m.Subject.includes(subject),
    );
    expect(mail).toBeTruthy();
    const content = await (
      await request.get('http://127.0.0.1:8025/api/v1/message/' + mail.ID)
    ).json();
    return content.Text.match(/token=([A-Za-z0-9_-]+)/)[1];
  }
  await page.goto('/verificar?token=' + (await token('verifica')));
  await page.getByRole('button', { name: 'Verificar correo', exact: true }).click();
  await expect(page.getByText('Correo verificado. Ya puedes iniciar sesión.')).toBeVisible();
  await page.goto('/olvido');
  await page.getByLabel('Correo electrónico', { exact: true }).fill(email);
  await page.getByRole('button', { name: 'Enviar enlace', exact: true }).click();
  await expect(
    page.getByText('Si corresponde, recibirás un enlace de recuperación.'),
  ).toBeVisible();
  await page.goto('/recuperar?token=' + (await token('recupera')));
  await page.getByLabel('Contraseña', { exact: true }).fill(password + '2');
  await page.getByLabel('Confirmar contraseña').fill(password + '2');
  await page.getByRole('button', { name: 'Actualizar contraseña', exact: true }).click();
  await expect(
    page.getByText('Contraseña actualizada. Las sesiones anteriores caducaron.'),
  ).toBeVisible();
  await login(page, email, password + '2');
  await page.goto('/panel/seguridad');
  await page.getByLabel('Contraseña actual').fill(password + '2');
  await page.getByLabel('Nueva contraseña').fill(password + '3');
  await page.getByLabel('Confirmar contraseña').fill(password + '3');
  await page.getByRole('button', { name: 'Cambiar contraseña', exact: true }).click();
  await expect(page).toHaveURL(/\/acceso$/);
  await expect(
    page.getByRole('status').filter({ hasText: 'Contraseña actualizada' }),
  ).toBeVisible();
  await screenshot(page, 'cuenta-' + info.project.name);
  await login(page, email, password + '3');
  if (info.project.name === 'mobile')
    await page.getByRole('button', { name: 'Abrir navegación' }).click();
  await page.getByRole('button', { name: 'Salir', exact: true }).click();
  await expect(page.getByText('Sesión cerrada', { exact: true })).toBeVisible();
});

test('administración secundaria, permisos, estados vacíos y sesiones vencidas', async ({
  page,
}, info) => {
  page.on('dialog', (d) =>
    d.type() === 'prompt' ? d.accept('Revisión ficticia de auditoría') : d.accept(),
  );
  await login(page, credentials.admin.email, credentials.admin.password);
  await page.goto('/panel/admin');
  await page.getByRole('button', { name: 'Categorías', exact: true }).click();
  const category = 'Auditoría ' + info.project.name + ' ' + Date.now();
  await page.getByLabel('Nombre', { exact: true }).fill(category);
  await page.getByLabel('Descripción', { exact: true }).fill('Catálogo ficticio de auditoría');
  await page.getByLabel('Activo', { exact: true }).check();
  await page.getByRole('button', { name: 'Guardar catálogo' }).click();
  const row = page
    .getByRole('row')
    .filter({ has: page.getByRole('cell', { name: category, exact: true }) });
  await expect(row.getByRole('cell', { name: 'Activo', exact: true })).toBeVisible();
  await row.getByRole('button', { name: 'Editar', exact: true }).click();
  await page.getByLabel('Activo', { exact: true }).uncheck();
  await page.getByRole('button', { name: 'Guardar catálogo' }).click();
  await expect(row.getByRole('cell', { name: 'Inactivo', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Habilidades', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Habilidades', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Usuarios', exact: true }).click();
  const admin = page.getByRole('row').filter({ hasText: credentials.admin.email });
  await admin.getByRole('button', { name: 'Suspender', exact: true }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'último administrador' })).toBeVisible();
  await page.getByRole('button', { name: 'Actividades', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Supervisión de actividades' })).toBeVisible();
  await page.getByRole('button', { name: 'Bitácora', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bitácora de eventos' })).toBeVisible();
  await screenshot(page, 'admin-' + info.project.name);
  await login(page, credentials.org.email, credentials.org.password);
  await page.goto('/panel/organizacion');
  await page.getByRole('button', { name: 'Registrar organización', exact: true }).click();
  const organization = 'Equipo auditoría ' + info.project.name + ' ' + Date.now();
  await page.getByLabel('Nombre de la organización').fill(organization);
  await page.getByLabel('Correo de contacto').fill('equipo@example.org');
  await page
    .getByLabel('Qué hacemos')
    .fill('Equipo ficticio para verificar permisos de coordinación.');
  await page.getByRole('button', { name: 'Registrar organización', exact: true }).last().click();
  await expect(
    page.getByRole('heading', { name: organization, exact: true, level: 2 }),
  ).toBeVisible();
  await page.getByText('Miembros y permisos', { exact: true }).click();
  await page.getByLabel('Correo de la cuenta').fill(credentials.vol.email);
  await page.getByLabel('Cargo', { exact: true }).selectOption('coordinador');
  await page.getByLabel('Estado', { exact: true }).selectOption('activo');
  await page.getByRole('button', { name: 'Agregar o actualizar miembro' }).click();
  await expect(page.getByText('Procesando…', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('row').filter({ hasText: credentials.vol.email })).toBeVisible();
  await page.goto('/panel/actividad/999999999');
  await expect(page.getByRole('alert').filter({ hasText: 'Registro no encontrado' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Crear borrador' })).toHaveCount(0);
  await login(page, credentials.vol.email, credentials.vol.password);
  await page.goto('/panel/organizacion');
  await page.getByRole('button', { name: new RegExp(organization) }).click();
  await expect(
    page.getByRole('heading', { name: organization, exact: true, level: 2 }),
  ).toBeVisible();
  await expect(page.getByText('Miembros y permisos', { exact: true })).toHaveCount(0);
  await page.getByText('Documentos de verificación', { exact: true }).click();
  await expect(page.getByLabel('Documento PDF', { exact: true })).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Subir documento privado', exact: true }),
  ).toHaveCount(0);
  await expect(page.getByText('Perfil de la organización', { exact: true })).toHaveCount(0);
  await page.goto('/panel/admin');
  await expect(page).toHaveURL(/\/panel$/);
  await page.goto('/panel/notificaciones');
  await expect(page.getByRole('heading', { name: 'Notificaciones', exact: true })).toBeVisible();
  await screenshot(page, 'notificaciones-' + info.project.name);
  await page
    .context()
    .addCookies([{ name: 'voluntia_session', value: 'expired', url: new URL(page.url()).origin }]);
  await page.getByRole('button', { name: 'Actualizar', exact: true }).click();
  await expect(page).toHaveURL(/\/acceso$/);
  await expect(page.getByRole('button', { name: 'Iniciar sesión', exact: true })).toBeVisible();
});
