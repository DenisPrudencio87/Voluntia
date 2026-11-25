import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Session } from '../services/session';
import { Api, Feedback } from '../services/api';
import { RecordForm, Field, FormValue } from '../components/record-form';
@Component({
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  template: `<div class="container section">
    <div class="eyebrow">Tu espacio para transformar</div>
    <div class="section-title mt-2">
      <h1 class="h2 mb-0">Mi panel</h1>
      <span class="text-secondary small text-break">{{ session.user()?.correo }}</span>
    </div>
    @if (!session.user()?.email_verificado) {
      <div class="alert alert-warning">
        Verifica tu correo para completar tu perfil y participar.
        <a routerLink="/reenviar">Solicitar enlace</a>
      </div>
    }
    <nav class="panel-nav" aria-label="Paneles por rol">
      @if (session.has('voluntario')) {
        <a routerLink="/panel/voluntario" routerLinkActive="active">Mi voluntariado</a
        ><a routerLink="/panel/perfil" routerLinkActive="active">Mi perfil</a>
      }
      <a routerLink="/panel/organizacion" routerLinkActive="active">Mis organizaciones</a>
      @if (session.has('administrador')) {
        <a routerLink="/panel/admin" routerLinkActive="active">Administración</a>
      }
      <a routerLink="/panel/notificaciones" routerLinkActive="active">Notificaciones</a
      ><a routerLink="/panel/seguridad" routerLinkActive="active">Seguridad</a>
    </nav>
    <router-outlet />
  </div>`,
})
export class Panel {
  session = inject(Session);
}

@Component({
  imports: [RouterLink],
  template: `<div class="surface">
    <h2>Elige cómo quieres participar</h2>
    <p class="text-secondary">
      Desde aquí puedes gestionar tu perfil, tus actividades y tus organizaciones.
    </p>
    <div class="action-row">
      @if (session.has('voluntario')) {
        <a class="btn btn-primary" routerLink="/panel/voluntario">Mi voluntariado</a>
      }
      <a class="btn btn-outline-primary" routerLink="/panel/organizacion">Mis organizaciones</a>
      @if (session.has('administrador')) {
        <a class="btn btn-outline-primary" routerLink="/panel/admin">Administración</a>
      }
    </div>
  </div>`,
})
export class PanelHome {
  session = inject(Session);
}

@Component({
  imports: [RecordForm],
  template: `<div class="surface">
    <h2 class="h4">Cambiar contraseña</h2>
    <p class="text-secondary">
      Al guardar se cerrarán todas tus sesiones. Usa al menos 12 caracteres.
    </p>
    <app-record-form
      [fields]="fields"
      label="Cambiar contraseña"
      [busy]="feedback.busy()"
      (saved)="save($event)"
    />
  </div>`,
})
export class SecurityPage {
  router = inject(Router);
  api = inject(Api);
  feedback = inject(Feedback);
  session = inject(Session);
  fields: Field[] = [
    { key: 'clave_actual', label: 'Contraseña actual', type: 'password', required: true, max: 128 },
    {
      key: 'clave',
      label: 'Nueva contraseña',
      type: 'password',
      required: true,
      min: 12,
      max: 128,
    },
    {
      key: 'confirmacion',
      label: 'Confirmar contraseña',
      type: 'password',
      required: true,
      min: 12,
      max: 128,
    },
  ];
  async save(value: FormValue) {
    const result = await this.feedback.run(() =>
      this.api.post<{ mensaje: string }>('/auth/password', value),
    );
    if (result) {
      this.session.user.set(null);
      await this.router.navigateByUrl('/acceso');
      this.feedback.success.set(result.mensaje);
    }
  }
}
