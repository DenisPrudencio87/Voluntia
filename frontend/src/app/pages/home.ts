import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe, DecimalPipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { Activity, Catalogs, Page } from '../models/domain';
import { LabelPipe } from '../components/labels';
@Component({
  imports: [RouterLink, DatePipe, DecimalPipe, LabelPipe],
  template: ` <section class="hero">
      <div class="container">
        <div class="row align-items-center">
          <div class="col-lg-7 hero-copy">
            <div class="eyebrow mb-3">Tu tiempo puede transformar vidas</div>
            <h1>Pequeñas acciones.<br /><em>Un gran impacto.</em></h1>
            <p class="mt-4 mb-4">
              Encuentra una causa que te mueva. Conecta con organizaciones y convierte tus ganas de
              ayudar en acciones que cuentan.
            </p>
            <a class="btn btn-primary btn-lg" routerLink="/actividades"
              >Encuentra tu próxima causa <i class="bi bi-arrow-right ms-2"></i
            ></a>
            <div class="small text-secondary mt-3">Participa. Conecta. Deja huella.</div>
          </div>
          <div class="col-lg-5 hero-art" aria-hidden="true">
            <i class="bi bi-flower1 hero-mark"></i>
            <div class="hero-note one"><i class="bi bi-heart-fill"></i> Tu tiempo tiene valor</div>
            <div class="hero-note two">
              <i class="bi bi-people-fill"></i> Juntos llegamos más lejos
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="stat-row" aria-label="Impacto registrado">
      <div class="container py-4">
        <div class="row text-center g-3">
          @for (stat of statCards(); track stat.label) {
            <div class="col-6 col-md-3">
              <div class="stat-value">{{ stat.value | number: '1.0-1' }}</div>
              <div class="small text-secondary">{{ stat.label }}</div>
            </div>
          }
        </div>
      </div>
    </section>
    <section class="container section">
      <div class="section-title">
        <div>
          <div class="eyebrow mb-2">Encuentra tu lugar</div>
          <h2>Hay una causa para ti</h2>
        </div>
      </div>
      <div class="row g-3">
        @for (c of catalogs()?.categorias; track c.id_categoria) {
          <div class="col-sm-6 col-lg-3">
            <a
              class="category-link"
              routerLink="/actividades"
              [queryParams]="{ categoria: c.id_categoria }"
              ><i class="bi bi-heart" aria-hidden="true"></i>{{ c.nombre
              }}<i class="bi bi-arrow-up-right ms-auto"></i
            ></a>
          </div>
        }
      </div>
    </section>
    <section class="container pb-4">
      <div class="section-title">
        <div>
          <div class="eyebrow mb-2">El siguiente paso es tuyo</div>
          <h2>Oportunidades para sumar</h2>
        </div>
        <a routerLink="/actividades">Ver todas las actividades <i class="bi bi-arrow-right"></i></a>
      </div>
      <div class="row g-4">
        @for (a of activities(); track a.id_actividad) {
          <div class="col-md-6 col-lg-4">
            <article class="card activity-card">
              <div class="card-art">
                @if (a.imagen_portada_url) {
                  <img [src]="a.imagen_portada_url" alt="" loading="lazy" />
                } @else {
                  <i class="bi bi-tree" aria-hidden="true"></i>
                }
              </div>
              <div class="card-body">
                <span class="pill mb-3">{{ a.categoria }}</span>
                <h3>
                  <a [routerLink]="['/actividades', a.id_actividad]">{{ a.titulo }}</a>
                </h3>
                <p class="small text-secondary">{{ a.organizacion }}</p>
                <div class="activity-meta">
                  <i class="bi bi-calendar3 me-2"></i>{{ a.fecha_inicio | date: 'dd/MM/yyyy HH:mm'
                  }}<br /><i class="bi bi-geo-alt me-2"></i>{{ a.modalidad | label }} ·
                  {{ a.nombre_lugar || 'Desde donde estés' }}
                </div>
                <div class="d-flex justify-content-between align-items-center mt-3">
                  <span class="small">{{ a.cupos_disponibles }} cupos disponibles</span
                  ><a
                    [routerLink]="['/actividades', a.id_actividad]"
                    aria-label="Ver detalles de actividad"
                    ><i class="bi bi-arrow-right"></i
                  ></a>
                </div>
              </div>
            </article>
          </div>
        } @empty {
          <div class="col-12">
            <div class="empty">
              Aún no hay actividades publicadas. Pronto encontrarás nuevas formas de ayudar.
            </div>
          </div>
        }
      </div>
    </section>
    <section class="container section">
      <div class="surface row align-items-center g-3">
        <div class="col-md-8">
          <div class="eyebrow">Multiplica tu impacto</div>
          <h2 class="mt-2">¿Representas una organización?</h2>
          <p class="mb-0 text-secondary">
            Publica oportunidades y acompaña a tu comunidad en cada paso.
          </p>
        </div>
        <div class="col-md-4 text-md-end">
          <a class="btn btn-outline-primary" routerLink="/panel/organizacion"
            >Registrar mi organización <i class="bi bi-arrow-right"></i
          ></a>
        </div>
      </div>
    </section>`,
})
export class Home implements OnInit {
  private api = inject(Api);
  feedback = inject(Feedback);
  catalogs = signal<Catalogs | null>(null);
  activities = signal<Activity[]>([]);
  stats = signal<Record<string, number>>({});
  statCards() {
    const s = this.stats();
    return [
      { label: 'Organizaciones verificadas', value: s['organizaciones'] ?? 0 },
      { label: 'Oportunidades abiertas', value: s['actividades'] ?? 0 },
      { label: 'Perfiles voluntarios', value: s['voluntarios'] ?? 0 },
      { label: 'Horas de participación', value: s['horas'] ?? 0 },
    ];
  }
  async ngOnInit() {
    await this.feedback.run(async () => {
      const [c, a, s] = await Promise.all([
        this.api.get<Catalogs>('/catalogs'),
        this.api.get<Page<Activity>>('/activities?disponible=true&size=3'),
        this.api.get<Record<string, number>>('/statistics'),
      ]);
      this.catalogs.set(c);
      this.activities.set(a.items);
      this.stats.set(s);
    });
  }
}
