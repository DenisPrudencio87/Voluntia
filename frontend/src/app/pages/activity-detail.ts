import { Component, inject, OnInit, signal, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { Session } from '../services/session';
import { Activity, Organization } from '../models/domain';
import { RecordForm, Field, FormValue } from '../components/record-form';
import { LabelPipe } from '../components/labels';

@Component({
  imports: [DatePipe, RouterLink, RecordForm, LabelPipe],
  template: `<section class="container section activity-detail">
    @if (activity(); as a) {
      <a routerLink="/actividades" class="small"
        ><i class="bi bi-arrow-left"></i> Todas las actividades</a
      >
      <div class="mt-4 mb-3 d-flex gap-2">
        <span class="pill">{{ a.categoria }}</span><span class="pill pill-neutral">{{
          a.estado | label
        }}</span>
      </div>
      <h1>{{ a.titulo }}</h1>
      <a [routerLink]="['/organizaciones', a.id_organizacion]"
        >{{ a.organizacion }} <i class="bi bi-patch-check"></i
      ></a>
      @if (a.imagen_portada_url) {
        <img
          class="w-100 rounded-4 my-4"
          style="max-height:360px;object-fit:cover"
          [src]="a.imagen_portada_url"
          alt="Imagen de la actividad"
        />
      }
      <div class="surface mt-4">
        <div class="row g-3">
          <div class="col-sm-6">
            <div class="small-label">Cuándo</div>
            {{ a.fecha_inicio | date: 'dd/MM/yyyy HH:mm' }}<br />Hasta
            {{ a.fecha_fin | date: 'dd/MM/yyyy HH:mm' }}
          </div>
          <div class="col-sm-6">
            <div class="small-label">Dónde</div>
            {{ a.modalidad | label }}<br />{{ a.nombre_lugar || 'Participación virtual' }}
            {{ a.direccion }}
          </div>
          <div class="col-sm-6">
            <div class="small-label">Inscripciones hasta</div>
            {{ a.fecha_cierre_inscripcion | date: 'dd/MM/yyyy HH:mm' }}
          </div>
          <div class="col-sm-6">
            <div class="small-label">Plazas disponibles</div>
            {{ a.cupos_disponibles }} de {{ a.cupo_maximo }}
          </div>
        </div>
      </div>
      <h2 class="h4">Sobre esta oportunidad</h2>
      <p class="prose">{{ a.descripcion }}</p>
      @if (a.habilidades?.length) {
        <h2 class="h5 mt-4">Habilidades solicitadas</h2>
        <ul>
          @for (h of a.habilidades; track h.id_habilidad) {
            <li>
              {{ h.nombre }} · {{ h.nivel_requerido | label }} ·
              {{ h.obligatoria ? 'Obligatoria' : 'Deseable' }}
            </li>
          }
        </ul>
      }
      @if (a.impacto) {
        <div class="surface mt-4">
          <h2 class="h4">El impacto de esta actividad</h2>
          <p>{{ a.impacto.descripcion_impacto }}</p>
          <strong
            >{{ a.impacto.beneficiarios_estimados }} beneficiarios estimados ·
            {{ a.impacto.horas_voluntariado }} horas</strong
          >
        </div>
      }
      <div class="surface mt-4">
        <h2 class="h4">Tu participación empieza aquí</h2>
        @if (canApply(a)) {
          @if (session.user()) {
            <p class="small text-secondary">
              Completa tu perfil y habilidades antes de postular. Podrás seguir el estado desde tu
              panel. Los certificados emitidos permiten verificar públicamente tu nombre, actividad,
              organización, horas y fecha.
            </p>
            <app-record-form
              [fields]="fields"
              label="Enviar postulación"
              [busy]="feedback.busy()"
              (saved)="apply($event)"
            />
          } @else {
            <p>Inicia sesión para postular a esta actividad.</p>
            <a class="btn btn-primary" routerLink="/acceso">Iniciar sesión</a>
          }
        } @else {
          <p class="mb-0">Las inscripciones para esta actividad están cerradas.</p>
        }
      </div>
    } @else if (!feedback.busy()) {
      <div class="empty">No se encontró la actividad.</div>
    }
  </section>`,
})
export class ActivityDetail implements OnInit {
  private destroyRef = inject(DestroyRef);
  route = inject(ActivatedRoute);
  api = inject(Api);
  feedback = inject(Feedback);
  session = inject(Session);
  activity = signal<Activity | null>(null);
  fields: Field[] = [
    {
      key: 'motivacion',
      label: 'Cuéntanos por qué quieres participar',
      type: 'textarea',
      required: true,
      min: 10,
      max: 2000,
    },
  ];
  async ngOnInit() {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const id = params.get('id');
      this.activity.set(null);
      void this.feedback.run(async () => {
        const activity = await this.api.get<Activity>('/activities/' + id);
        if (this.route.snapshot.paramMap.get('id') === id) this.activity.set(activity);
      });
    });
  }
  canApply(a: Activity) {
    return a.estado === 'publicada' && new Date(a.fecha_cierre_inscripcion) > new Date();
  }
  async apply(value: FormValue) {
    await this.feedback.run(
      () => this.api.post('/activities/' + this.activity()!.id_actividad + '/applications', value),
      'Postulación registrada. Consulta su estado en Mi panel.',
    );
  }
}

@Component({
  imports: [RouterLink],
  template: `<section class="container section activity-detail">
    @if (org(); as o) {
      <div class="eyebrow">Organización verificada</div>
      <h1 class="mt-2">{{ o.nombre }}</h1>
      <p class="prose mt-4">{{ o.descripcion }}</p>
      @if (o.sitio_web) {
        <a [href]="o.sitio_web" target="_blank" rel="noopener noreferrer"
          >Visitar sitio web <i class="bi bi-box-arrow-up-right"></i
        ></a>
      }
      <div class="mt-4">
        <a class="btn btn-primary" routerLink="/actividades">Explorar oportunidades</a>
      </div>
    }
  </section>`,
})
export class PublicOrganization implements OnInit {
  private destroyRef = inject(DestroyRef);
  api = inject(Api);
  feedback = inject(Feedback);
  route = inject(ActivatedRoute);
  org = signal<Organization | null>(null);
  async ngOnInit() {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const id = params.get('id');
      this.org.set(null);
      void this.feedback.run(async () => {
        const org = await this.api.get<Organization>('/organizations/' + id);
        if (this.route.snapshot.paramMap.get('id') === id) this.org.set(org);
      });
    });
  }
}
