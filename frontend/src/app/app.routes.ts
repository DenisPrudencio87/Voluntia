import { Routes } from '@angular/router';

import { authGuard } from './guards/auth';
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home').then((m) => m.Home),
    title: 'Voluntia · Cada acción cuenta',
  },
  {
    path: 'actividades',
    loadComponent: () => import('./pages/catalog').then((m) => m.Catalog),
    title: 'Explorar actividades · Voluntia',
  },
  {
    path: 'actividades/:id',
    loadComponent: () => import('./pages/activity-detail').then((m) => m.ActivityDetail),
    title: 'Actividad · Voluntia',
  },
  {
    path: 'organizaciones/:id',
    loadComponent: () => import('./pages/activity-detail').then((m) => m.PublicOrganization),
    title: 'Organización · Voluntia',
  },
  ...[
    { path: 'acceso', mode: 'login' },
    { path: 'registro', mode: 'register' },
    { path: 'olvido', mode: 'forgot' },
    { path: 'reenviar', mode: 'resend' },
    { path: 'verificar', mode: 'verify' },
    { path: 'recuperar', mode: 'reset' },
  ].map((r) => ({
    path: r.path,
    loadComponent: () => import('./pages/auth').then((m) => m.AuthPage),
    data: { mode: r.mode },
    title: 'Cuenta · Voluntia',
  })),
  {
    path: 'certificados',
    loadComponent: () => import('./pages/certificate').then((m) => m.CertificatePage),
    title: 'Verificar certificado · Voluntia',
  },
  {
    path: 'panel',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/panel').then((m) => m.Panel),
    children: [
      { path: '', loadComponent: () => import('./pages/panel').then((m) => m.PanelHome) },
      {
        path: 'voluntario',
        canActivate: [authGuard],
        data: { role: 'voluntario' },
        loadComponent: () => import('./pages/volunteer').then((m) => m.VolunteerPage),
      },
      {
        path: 'perfil',
        canActivate: [authGuard],
        data: { role: 'voluntario' },
        loadComponent: () => import('./pages/volunteer').then((m) => m.ProfilePage),
      },
      {
        path: 'notificaciones',
        loadComponent: () => import('./pages/volunteer').then((m) => m.NotificationsPage),
      },
      {
        path: 'organizacion',
        loadComponent: () => import('./pages/organization').then((m) => m.OrganizationPage),
      },
      {
        path: 'actividad/nueva/:org',
        canActivate: [authGuard],
        data: { role: 'organizacion' },
        loadComponent: () => import('./pages/manage-activity').then((m) => m.ManageActivity),
      },
      {
        path: 'actividad/:id',
        canActivate: [authGuard],
        data: { role: 'organizacion' },
        loadComponent: () => import('./pages/manage-activity').then((m) => m.ManageActivity),
      },
      {
        path: 'admin',
        canActivate: [authGuard],
        data: { role: 'administrador' },
        loadComponent: () => import('./pages/admin').then((m) => m.AdminPage),
      },
      {
        path: 'seguridad',
        loadComponent: () => import('./pages/panel').then((m) => m.SecurityPage),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
