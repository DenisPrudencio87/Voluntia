import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { Activity, Catalogs, Page } from '../models/domain';
import { LabelPipe } from '../components/labels';

@Component({
  imports: [RouterLink, ReactiveFormsModule, DatePipe, LabelPipe],
  template: ` <section class="container section">
    <div class="eyebrow mb-2">Actúa por lo que te importa</div>
    <h1>Encuentra tu próxima causa</h1>
    <p class="text-secondary">Explora oportunidades reales y elige dónde dejar tu huella.</p>
    <form class="surface row g-3 mt-4" [formGroup]="form" (ngSubmit)="search()">
      <div class="col-md-6 col-lg-4">
        <label for="search-q" class="form-label">¿Qué te gustaría hacer?</label
        ><input
          id="search-q"
          class="form-control"
          formControlName="q"
          placeholder="Buscar actividad o causa"
          maxlength="100"
        />
      </div>
      <div class="col-md-6 col-lg-4">
        <label for="search-category" class="form-label">Categoría</label
        ><select id="search-category" class="form-select" formControlName="categoria">
          <option value="">Todas las causas</option>
          @for (c of catalogs()?.categorias; track c.id_categoria) {
            <option [value]="c.id_categoria">{{ c.nombre }}</option>
          }
        </select>
      </div>
      <div class="col-md-6 col-lg-4">
        <label for="search-mode" class="form-label">Modalidad</label
        ><select id="search-mode" class="form-select" formControlName="modalidad">
          <option value="">Todas</option>
          <option value="presencial">Presencial</option>
          <option value="virtual">Virtual</option>
          <option value="hibrida">Híbrida</option>
        </select>
      </div>
      <div class="col-md-6 col-lg-4">
        <label for="search-location" class="form-label">Ubicación</label
        ><input
          id="search-location"
          class="form-control"
          formControlName="ubicacion"
          placeholder="Lugar o ciudad"
          maxlength="100"
        />
      </div>
      <div class="col-md-6 col-lg-4">
        <label for="search-date" class="form-label">Desde</label
        ><input id="search-date" type="date" class="form-control" formControlName="desde" />
      </div>
      <div class="col-md-6 col-lg-4 d-flex flex-column justify-content-end">
        <label class="form-check mb-2"
          ><input type="checkbox" class="form-check-input" formControlName="disponible" />Solo con
          cupos e inscripción abierta</label
        ><button class="btn btn-primary" [disabled]="feedback.busy()">
          Buscar actividades <i class="bi bi-search ms-2"></i>
        </button>
      </div>
    </form>
    <div class="section-title">
      <h2 class="h5 mb-0">{{ result()?.total ?? 0 }} oportunidades</h2>
      <button type="button" class="btn btn-link" (click)="clear()">Limpiar filtros</button>
    </div>
    <div class="row g-4">
      @for (a of result()?.items; track a.id_actividad) {
        <div class="col-md-6 col-lg-4">
          <article class="card activity-card">
            <div class="card-art">
              @if (a.imagen_portada_url) {
                <img [src]="a.imagen_portada_url" alt="" loading="lazy" />
              } @else {
                <i class="bi bi-flower1" aria-hidden="true"></i>
              }
            </div>
            <div class="card-body">
              <div class="d-flex gap-2 mb-3">
                <span class="pill">{{ a.categoria }}</span><span class="pill pill-neutral">{{
                  a.estado | label
                }}</span>
              </div>
              <h3>
                <a [routerLink]="['/actividades', a.id_actividad]">{{ a.titulo }}</a>
              </h3>
              <p class="text-secondary small">{{ a.organizacion }}</p>
              <p class="activity-meta">
                <i class="bi bi-calendar3 me-2"></i>{{ a.fecha_inicio | date: 'dd/MM/yyyy HH:mm'
                }}<br /><i class="bi bi-geo-alt me-2"></i
                >{{ a.nombre_lugar || (a.modalidad | label) }}
              </p>
              <div class="d-flex justify-content-between">
                <span class="small">{{ a.cupos_disponibles }} cupos</span
                ><a [routerLink]="['/actividades', a.id_actividad]"
                  >Conocer actividad <i class="bi bi-arrow-right"></i
                ></a>
              </div>
            </div>
          </article>
        </div>
      } @empty {
        <div class="col-12">
          <div class="empty">
            No encontramos actividades con estos filtros. Prueba otra búsqueda.
          </div>
        </div>
      }
    </div>
    <nav class="pagination-bar" aria-label="Páginas del catálogo">
      <button
        class="btn btn-outline-primary"
        [disabled]="page === 1 || feedback.busy()"
        (click)="load(page - 1)"
      >
        Anterior</button
      ><span>Página {{ page }}</span
      ><button
        class="btn btn-outline-primary"
        [disabled]="page * 9 >= (result()?.total ?? 0) || feedback.busy()"
        (click)="load(page + 1)"
      >
        Siguiente
      </button>
    </nav>
  </section>`,
})
export class Catalog implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  route = inject(ActivatedRoute);
  fb = inject(FormBuilder);
  page = 1;
  result = signal<Page<Activity> | null>(null);
  catalogs = signal<Catalogs | null>(null);
  form = this.fb.group({
    q: [''],
    categoria: [''],
    modalidad: [''],
    ubicacion: [''],
    desde: [''],
    disponible: [false],
  });
  async ngOnInit() {
    this.form.patchValue({ categoria: this.route.snapshot.queryParamMap.get('categoria') ?? '' });
    await this.feedback.run(async () => {
      this.catalogs.set(await this.api.get<Catalogs>('/catalogs'));
    });
    await this.load(1);
  }
  async search() {
    await this.load(1);
  }
  async clear() {
    this.form.reset({
      q: '',
      categoria: '',
      modalidad: '',
      ubicacion: '',
      desde: '',
      disponible: false,
    });
    await this.load(1);
  }
  async load(page: number) {
    await this.feedback.run(async () => {
      const v = this.form.getRawValue(),
        params = new URLSearchParams({ page: String(page) });
      for (const [k, value] of Object.entries(v)) {
        if (value !== null && value !== '' && value !== false)
          params.set(
            k,
            k === 'desde' ? new Date((value as string) + 'T00:00:00').toISOString() : String(value),
          );
      }
      this.result.set(await this.api.get<Page<Activity>>('/activities?' + params));
      this.page = page;
    });
  }
}
