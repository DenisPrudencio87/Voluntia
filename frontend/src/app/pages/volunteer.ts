import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { Application, Profile, History, Notice, Catalogs, Skill } from '../models/domain';
import { LabelPipe } from '../components/labels';
import { RecordForm, Field, FormValue } from '../components/record-form';
import { SkillsEditor } from '../components/skills-editor';
import { optional, withLocation } from '../components/domain-fields';

@Component({
  imports: [RouterLink, DatePipe, LabelPipe],
  template: `<div class="section-title">
      <div>
        <h2>Mi voluntariado</h2>
        <p class="text-secondary mb-0">Cada hora cuenta. Aquí puedes seguir tu participación.</p>
      </div>
      <a class="btn btn-primary" routerLink="/actividades">Encontrar actividades</a>
    </div>
    <div class="row g-3 mb-4">
      <div class="col-md-6">
        <div class="surface mb-0">
          <div class="small-label">Horas de participación efectiva</div>
          <div class="stat-value">{{ profile()?.horas ?? 0 }}</div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="surface mb-0">
          <div class="small-label">Tu perfil</div>
          <p class="mb-0 mt-2">
            {{
              profile()
                ? 'Listo para conectar con nuevas causas'
                : 'Completa tu perfil para postular'
            }}
          </p>
          <a routerLink="/panel/perfil">Editar mi perfil <i class="bi bi-arrow-right"></i></a>
        </div>
      </div>
    </div>
    @for (i of applications(); track i.id_inscripcion) {
      <article class="surface">
        <div class="section-title">
          <div>
            <span class="pill mb-2">{{ i.estado | label }}</span>
            <h3 class="h5">
              <a [routerLink]="['/actividades', i.id_actividad]">{{ i.titulo }}</a>
            </h3>
            <div class="small text-secondary">{{ i.fecha_inicio | date: 'dd/MM/yyyy HH:mm' }}</div>
          </div>
          <div class="action-row">
            <button class="btn btn-sm btn-outline-primary" (click)="history(i)">
              Ver historial
            </button>
            @if (canCancel(i)) {
              <button
                class="btn btn-sm btn-outline-danger"
                [disabled]="feedback.busy()"
                (click)="cancel(i)"
              >
                Cancelar postulación
              </button>
            }
          </div>
        </div>
        @if (i.observacion) {
          <p>{{ i.observacion }}</p>
        }
        @if (i.id_certificado) {
          <div class="action-row">
            <a
              class="btn btn-primary btn-sm"
              [href]="'/api/v1/certificates/private/' + i.id_certificado + '/file'"
              >Descargar certificado</a
            ><a
              class="btn btn-outline-primary btn-sm"
              routerLink="/certificados"
              [queryParams]="{ code: i.codigo_verificacion }"
              >Verificar certificado</a
            ><span class="small align-self-center"
              >{{ i.horas_certificadas }} horas certificadas</span
            >
          </div>
        }
        @if (selected === i.id_inscripcion) {
          <ol class="mt-3 mb-0">
            @for (h of histories(); track $index) {
              <li>
                {{ h.estado | label }} · {{ h.fecha_cambio | date: 'dd/MM/yyyy HH:mm' }}
                @if (h.comentario) {
                  — {{ h.comentario }}
                }
              </li>
            }
          </ol>
        }
      </article>
    } @empty {
      <div class="empty">Todavía no tienes postulaciones. Descubre una causa que te inspire.</div>
    }
    <nav class="pagination-bar" aria-label="Páginas de postulaciones">
      <button class="btn btn-outline-primary" [disabled]="page === 1" (click)="load(page - 1)">
        Anterior</button
      ><span>Página {{ page }}</span
      ><button
        class="btn btn-outline-primary"
        [disabled]="applications().length < 20"
        (click)="load(page + 1)"
      >
        Siguiente
      </button>
    </nav>`,
})
export class VolunteerPage implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  applications = signal<Application[]>([]);
  profile = signal<Profile | null>(null);
  histories = signal<History[]>([]);
  selected = 0;
  page = 1;
  async ngOnInit() {
    await this.load(1);
  }
  async load(page: number) {
    await this.feedback.run(async () => {
      const [a, p] = await Promise.all([
        this.api.get<Application[]>('/volunteer/applications?page=' + page),
        this.api.get<Profile | null>('/volunteer/profile'),
      ]);
      this.applications.set(a);
      this.profile.set(p);
      this.page = page;
    });
  }
  canCancel(i: Application) {
    return (
      ['pendiente', 'espera', 'aceptada'].includes(i.estado) &&
      !!i.fecha_inicio &&
      new Date(i.fecha_inicio) > new Date()
    );
  }
  async cancel(i: Application) {
    if (
      !window.confirm('¿Cancelar tu postulación? No podrás volver a inscribirte en esta actividad.')
    )
      return;
    const r = await this.feedback.run(() =>
      this.api.post('/applications/' + i.id_inscripcion + '/state', {
        estado: 'cancelada',
        observacion: 'Cancelación voluntaria',
      }),
    );
    if (r) await this.load(this.page);
  }
  async history(i: Application) {
    await this.feedback.run(async () => {
      this.histories.set(
        await this.api.get<History[]>('/volunteer/applications/' + i.id_inscripcion + '/history'),
      );
      this.selected = i.id_inscripcion;
    });
  }
}

@Component({
  imports: [RecordForm, SkillsEditor],
  template: `<div class="surface">
    <h2>Mi perfil voluntario</h2>
    <p class="text-secondary">
      Comparte tus habilidades para encontrar oportunidades donde puedas aportar.
    </p>
    <app-skills [catalog]="catalogs()?.habilidades ?? []" [(skills)]="skills" /><app-record-form
      [fields]="fields"
      [initial]="initial()"
      label="Guardar mi perfil"
      [busy]="feedback.busy()"
      (saved)="save($event)"
    />
  </div>`,
})
export class ProfilePage implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  catalogs = signal<Catalogs | null>(null);
  initial = signal<object | null>(null);
  skills: Skill[] = [];
  fields: Field[] = [
    { key: 'nombres', label: 'Nombres', required: true, min: 2, max: 100 },
    { key: 'apellidos', label: 'Apellidos', required: true, min: 2, max: 100 },
    { key: 'telefono', label: 'Teléfono', max: 30 },
    { key: 'fecha_nacimiento', label: 'Fecha de nacimiento', type: 'date' },
    { key: 'biografia', label: 'Sobre mí', type: 'textarea', max: 2000 },
    { key: 'foto_url', label: 'Foto (URL HTTPS)' },
    { key: 'lugar', label: 'Lugar o ciudad' },
    { key: 'direccion', label: 'Dirección' },
  ];
  async ngOnInit() {
    await this.feedback.run(async () => {
      const [c, p] = await Promise.all([
        this.api.get<Catalogs>('/catalogs'),
        this.api.get<Profile | null>('/volunteer/profile'),
      ]);
      this.catalogs.set(c);
      if (p) {
        this.skills = p.habilidades;
        this.initial.set({
          ...p,
          lugar: p.ubicacion?.nombre_lugar,
          direccion: p.ubicacion?.direccion,
        });
      }
    });
  }
  async save(v: FormValue) {
    const body = {
      ...withLocation(optional(v, ['telefono', 'fecha_nacimiento', 'biografia', 'foto_url'])),
      habilidades: this.skills.map((s) => ({ id_habilidad: s.id_habilidad, nivel: s.nivel })),
    };
    await this.feedback.run(() => this.api.put('/volunteer/profile', body), 'Perfil actualizado');
  }
}

@Component({
  imports: [DatePipe],
  template: `<div class="section-title">
      <h2>Notificaciones</h2>
      <button class="btn btn-outline-primary" (click)="load(page)">Actualizar</button>
    </div>
    @for (n of notices(); track n.id_notificacion) {
      <article class="surface" [class.notice-unread]="!n.leida">
        <h3 class="h6">{{ n.titulo }}</h3>
        <p>{{ n.mensaje }}</p>
        <div class="d-flex justify-content-between gap-2">
          <span class="small text-secondary">{{
            n.fecha_creacion | date: 'dd/MM/yyyy HH:mm'
          }}</span>
          @if (!n.leida) {
            <button class="btn btn-sm btn-outline-primary" (click)="read(n)">
              Marcar como leída
            </button>
          } @else {
            <span class="small text-secondary">Leída</span>
          }
        </div>
      </article>
    } @empty {
      <div class="empty">No tienes notificaciones en esta página.</div>
    }
    <nav class="pagination-bar" aria-label="Páginas de notificaciones">
      <button class="btn btn-outline-primary" [disabled]="page === 1" (click)="load(page - 1)">
        Anterior</button
      ><span>{{ page }}</span
      ><button
        class="btn btn-outline-primary"
        [disabled]="notices().length < 20"
        (click)="load(page + 1)"
      >
        Siguiente
      </button>
    </nav>`,
})
export class NotificationsPage implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  notices = signal<Notice[]>([]);
  page = 1;
  async ngOnInit() {
    await this.load(1);
  }
  async load(page: number) {
    await this.feedback.run(async () => {
      this.notices.set(await this.api.get<Notice[]>('/volunteer/notifications?page=' + page));
      this.page = page;
    });
  }
  async read(n: Notice) {
    await this.feedback.run(() =>
      this.api.post('/volunteer/notifications/' + n.id_notificacion + '/read'),
    );
    await this.load(this.page);
  }
}
