import { test, expect, Page } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = path.resolve('..');
const creds = JSON.parse(
  fs.readFileSync(path.join(root, '.local/e2e-credentials.json'), 'utf8'),
) as Record<string, { email: string; password: string; id: number }>;
const python = process.env['E2E_PYTHON'] ?? path.join(root, '.venv', 'Scripts', 'python.exe');
async function login(page: Page, role: string) {
  await page.goto('/acceso');
  await page.getByLabel('Correo electrónico', { exact: true }).fill(creds[role].email);
  await page.getByLabel('Contraseña', { exact: true }).fill(creds[role].password);
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Mi panel', exact: true })).toBeVisible();
}

test('catálogo responsive, navegación y validaciones', async ({ page }, info) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Pequeñas acciones/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.screenshot({
    path: path.join(root, '.local', 'home-' + info.project.name + '.png'),
    fullPage: true,
  });
  await page
    .getByRole('link', { name: /Encuentra tu próxima causa/ })
    .first()
    .click();
  await expect(page.getByRole('heading', { name: 'Encuentra tu próxima causa' })).toBeVisible();
  await page.getByLabel('¿Qué te gustaría hacer?').fill('Sin coincidencias ficticias');
  await page.getByRole('button', { name: /Buscar actividades/ }).click();
  await expect(page.getByText('No encontramos actividades con estos filtros.')).toBeVisible();
  await page.goto('/registro');
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click();
  await expect(page.getByText('Revisa correo electrónico.')).toBeVisible();
  await page.getByLabel('Correo electrónico', { exact: true }).fill('invalido');
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click();
  await expect(page.getByText('Revisa correo electrónico.')).toBeVisible();
});

test('recorrido de roles hasta certificado con PostgreSQL real', async ({ browser }, info) => {
  const orgContext = await browser.newContext({ viewport: info.project.use.viewport });
  const adminContext = await browser.newContext({ viewport: info.project.use.viewport });
  const volContext = await browser.newContext({ viewport: info.project.use.viewport });
  const org = await orgContext.newPage(),
    admin = await adminContext.newPage(),
    vol = await volContext.newPage();
  for (const p of [org, admin, vol])
    p.on('dialog', (d) =>
      d.type() === 'prompt' ? d.accept('Revisión académica ficticia') : d.accept(),
    );
  await login(org, 'org');
  await org.goto('/panel/organizacion');
  await org.getByRole('button', { name: 'Registrar organización', exact: true }).click();
  const orgName = 'Organización E2E ' + info.project.name + ' ' + Date.now();
  await org.getByLabel('Nombre de la organización').fill(orgName);
  await org.getByLabel('Correo de contacto').fill('organizacion@example.org');
  await org
    .getByLabel('Qué hacemos')
    .fill('Organización ficticia para demostrar participación social.');
  await org.getByRole('button', { name: 'Registrar organización', exact: true }).last().click();
  await expect(org.getByRole('heading', { name: orgName, exact: true }).last()).toBeVisible();
  await org.getByText('Documentos de verificación', { exact: true }).click();
  const pdf = execFileSync(
    python,
    [
      '-c',
      "from backend.app.services.certificates import certificate_pdf; from datetime import datetime,timezone; import sys; sys.stdout.buffer.write(certificate_pdf('Ficticio','Documento','Prueba',1,'demostracion',datetime.now(timezone.utc)))",
    ],
    { cwd: root },
  );
  await org
    .getByLabel('Documento PDF')
    .setInputFiles({ name: 'ficticio.pdf', mimeType: 'application/pdf', buffer: pdf });
  await org.getByLabel('Tipo de documento').fill('Constancia ficticia');
  await org.getByLabel('Número o referencia').fill('DEMO-E2E');
  await org.getByRole('button', { name: 'Subir documento privado' }).click();
  await expect(org.getByText('Constancia ficticia · DEMO-E2E')).toBeVisible();
  await login(admin, 'admin');
  await admin.goto('/panel/admin');
  const orgRow = admin
    .locator('.border-top')
    .filter({ has: admin.getByRole('heading', { name: orgName, exact: true }) })
    .first();
  await orgRow.getByRole('button', { name: 'Revisar documentos' }).click();
  await expect(admin.getByRole('heading', {name:'Documentos de verificación',exact:true})).toBeVisible();
  await orgRow.getByRole('button', { name: 'Aprobar documento', exact: true }).click();
  await expect(orgRow.getByText(/Constancia ficticia.*Aprobado/)).toBeVisible();
  await orgRow.getByRole('button', { name: 'Aprobar', exact: true }).click();
  await expect(orgRow.getByText('Verificada', { exact: true })).toBeVisible();
  await org.reload();
  await org.getByRole('button', { name: new RegExp(orgName) }).click();
  await org.getByRole('link', { name: 'Crear actividad' }).click();
  const title = 'Jornada E2E ' + info.project.name + ' ' + Date.now();
  await org.getByLabel('Título de la actividad').fill(title);
  await org.getByLabel('Categoría', { exact: true }).selectOption('1');
  await org
    .getByLabel('Descripción y propósito')
    .fill('Actividad ficticia completa para demostrar el ciclo real de voluntariado.');
  const now = Date.now();
  const local = (n: number) =>
    new Date(n - new Date(n).getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  await org.getByLabel('Inicio', { exact: true }).fill(local(now + 172800000));
  await org.getByLabel('Fin', { exact: true }).fill(local(now + 180000000));
  await org.getByLabel('Cierre de inscripción').fill(local(now + 86400000));
  await org.getByLabel('Cupo máximo').fill('2');
  await org.getByLabel('Modalidad', { exact: true }).selectOption('virtual');
  await org.getByRole('button', { name: 'Crear borrador' }).click();
  await expect(org.getByRole('heading', { name: title, exact: true })).toBeVisible();
  const activity = org.url().split('/').pop()!;
  await org.getByRole('button', { name: 'Publicar', exact: true }).click();
  await expect(org.getByText('Publicada', { exact: true })).toBeVisible();
  await login(vol, 'vol');
  await vol.goto('/panel/perfil');
  await vol.getByLabel('Nombres', { exact: true }).fill('Persona E2E');
  await vol.getByLabel('Apellidos', { exact: true }).fill('Ficticia');
  await vol.getByRole('button', { name: 'Guardar mi perfil' }).click();
  await expect(vol.getByText('Perfil actualizado')).toBeVisible();
  await vol.goto('/actividades/' + activity);
  await vol
    .getByLabel('Cuéntanos por qué quieres participar')
    .fill('Me interesa colaborar en esta actividad ficticia.');
  await vol.getByRole('button', { name: 'Enviar postulación' }).click();
  await expect(vol.getByText(/Postulación registrada/)).toBeVisible();
  await org.reload();
  await org.getByRole('button', { name: 'Aceptar', exact: true }).click();
  await expect(org.getByText('Aceptada', { exact: true })).toBeVisible();
  // Fixture de reloj: comando restringido a *_test, sin endpoint ni bypass en aplicación.
  execFileSync(python, ['-m', 'scripts.e2e_clock', activity], { cwd: root, env: process.env });
  await org.reload();
  await org.getByRole('button', { name: 'Iniciar actividad', exact: true }).click();
  await expect(org.getByText('En curso', { exact: true })).toBeVisible();
  await org.getByRole('button', { name: 'Registrar asistencia' }).click();
  const times = JSON.parse(
    execFileSync(python, ['-m', 'scripts.e2e_clock', activity, '--read'], {
      cwd: root,
      encoding: 'utf8',
      env: process.env,
    }),
  );
  await org.getByLabel('Hora de entrada').fill(local(new Date(times.start).getTime()));
  await org.getByLabel('Hora de salida').fill(local(new Date(times.end).getTime()));
  await org.getByRole('button', { name: 'Guardar asistencia' }).click();
  await expect(org.getByText('Asistió', { exact: true })).toBeVisible();
  await org.getByRole('button', { name: 'Finalizar actividad', exact: true }).click();
  await expect(org.getByRole('heading', { name: 'Impacto registrado' })).toBeVisible();
  await org.getByLabel('Beneficiarios estimados').fill('15');
  await org
    .getByLabel('Resultados alcanzados')
    .fill('Impacto ficticio comprobado durante el recorrido de evaluación.');
  await org.getByRole('button', { name: 'Guardar impacto' }).click();
  await expect(org.getByText(/2(?:\.0+)? horas de voluntariado/)).toBeVisible();
  await org.getByRole('button', { name: 'Emitir certificado' }).click();
  await expect(org.getByText('Certificado emitido', { exact: true })).toBeVisible();
  await vol.goto('/panel/voluntario');
  const participation = vol.locator('article').filter({has:vol.getByRole('link',{name:title,exact:true})});
  await expect(participation.getByRole('link', { name: 'Descargar certificado' })).toBeVisible();
  const link = participation.getByRole('link', { name: 'Verificar certificado', exact: true });
  await link.click();
  await vol.getByRole('button', { name: 'Verificar certificado' }).click();
  await expect(vol.getByText('Certificado válido')).toBeVisible();
  await expect(vol.getByRole('heading', { name: 'Persona E2E Ficticia' })).toBeVisible();
  for (const p of [org, admin, vol])
    expect(await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
      true,
    );
  await orgContext.close();
  await adminContext.close();
  await volContext.close();
});
