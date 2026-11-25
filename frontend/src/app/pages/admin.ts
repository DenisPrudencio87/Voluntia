import { Component, inject, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { User, Organization, Document, Activity, Audit, CatalogItem } from '../models/domain';
import { RecordForm, Field, FormValue } from '../components/record-form';
import { LabelPipe } from '../components/labels';
import { reason } from '../components/domain-fields';

@Component({
  imports: [DatePipe, RecordForm, LabelPipe],
  template: `
    <div class="section-title">
      <div>
        <div class="eyebrow">Administración general</div>
        <h2 class="mt-2">Cuidemos esta comunidad</h2>
      </div>
      <button class="btn btn-outline-primary" (click)="load(view)">Actualizar</button>
    </div>
    <div class="row g-3 mb-4">
      @for (s of statsCards(); track s.label) {
        <div class="col-6 col-md-3">
          <div class="surface mb-0">
            <div class="stat-value">{{ s.value }}</div>
            <div class="small-label">{{ s.label }}</div>
          </div>
        </div>
      }
    </div>
    <div class="action-row mb-4" role="group" aria-label="Secciones de administración">
      @for (t of tabs; track t.key) {
        <button
          [class]="view === t.key ? 'btn btn-primary' : 'btn btn-outline-primary'"
          (click)="load(t.key)"
        >
          {{ t.label }}
        </button>
      }
    </div>
    @if (view === 'organizations') {
      <div class="surface">
        <h3 class="h4">Organizaciones</h3>
        @for (o of organizations(); track o.id_organizacion) {
          <div class="border-top py-3">
            <div class="section-title mb-2">
              <div>
                <h4 class="h6 mb-1">{{ o.nombre }}</h4>
                <span class="pill">{{ o.estado_verificacion | label }}</span>
              </div>
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" (click)="selectOrg(o)">
                  Revisar documentos
                </button>
                @if (o.estado_verificacion !== 'verificada') {
                  <button class="btn btn-sm btn-primary" (click)="orgState(o, 'verificada')">
                    Aprobar
                  </button>
                }
                @if (o.estado_verificacion !== 'rechazada') {
                  <button class="btn btn-sm btn-outline-danger" (click)="orgState(o, 'rechazada')">
                    Rechazar
                  </button>
                }
                @if (o.estado_verificacion !== 'suspendida') {
                  <button class="btn btn-sm btn-outline-danger" (click)="orgState(o, 'suspendida')">
                    Suspender
                  </button>
                } @else {
                  <button class="btn btn-sm btn-outline-primary" (click)="orgState(o, 'pendiente')">
                    Reabrir revisión
                  </button>
                }
              </div>
            </div>
            <p class="small text-secondary mb-0">{{ o.descripcion }}</p>
            @if (selectedOrg() === o.id_organizacion) {
              <div class="border rounded p-3 mt-3">
                <h4 class="h6">Documentos de verificación</h4>
                @for (d of documents(); track d.id_documento) {
                  <div class="border-top py-2">
                    <span class="small"
                      >{{ d.tipo_documento }} · {{ d.numero_documento }} ·
                      {{ d.estado_revision | label }}</span
                    >
                    @if (d.estado_revision === 'pendiente') {
                      <div class="action-row mt-2">
                        <a
                          class="btn btn-sm btn-outline-primary"
                          [href]="'/api/v1/admin/documents/' + d.id_documento + '/file'"
                          >Descargar para revisar</a
                        ><button class="btn btn-sm btn-primary" (click)="review(d, 'aprobado')">
                          Aprobar documento</button
                        ><button
                          class="btn btn-sm btn-outline-danger"
                          (click)="review(d, 'rechazado')"
                        >
                          Rechazar documento
                        </button>
                      </div>
                    }
                  </div>
                } @empty {
                  <p class="small">La organización aún no sube documentos.</p>
                }
              </div>
            }
          </div>
        } @empty {
          <p class="text-secondary">No hay organizaciones en esta página.</p>
        }
      </div>
    }
    @if (view === 'users') {
      <div class="surface">
        <h3 class="h4">Usuarios y permisos</h3>
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>Cuenta</th>
                <th>Roles</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (u of users(); track u.id_usuario) {
                <tr>
                  <td class="text-break">
                    {{ u.correo }}<br /><span class="small text-secondary">{{
                      u.email_verificado ? 'Correo verificado' : 'Correo pendiente'
                    }}</span>
                  </td>
                  <td>
                    @for (r of u.roles; track r) {
                      <span class="pill me-1 mb-1">{{ r | label }}</span>
                    }
                  </td>
                  <td>{{ u.estado | label }}</td>
                  <td>
                    <div class="action-row">
                      <button class="btn btn-sm btn-outline-primary" (click)="editRoles(u)">
                        Editar roles</button
                      ><button class="btn btn-sm btn-outline-danger" (click)="userState(u)">
                        {{ u.estado === 'activo' ? 'Suspender' : 'Activar' }}
                      </button>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        @if (roleTarget(); as u) {
          <div class="border rounded p-3 mt-3">
            <h4 class="h6">Roles de {{ u.correo }}</h4>
            <div class="action-row mb-3">
              @for (r of roleOptions; track r) {
                <label class="form-check"
                  ><input
                    type="checkbox"
                    class="form-check-input"
                    [checked]="selectedRoles.includes(r)"
                    (change)="toggleRole(r, $event)"
                  />{{ r | label }}</label
                >
              }
            </div>
            <app-record-form
              [fields]="reasonFields"
              label="Actualizar roles y revocar sesiones"
              [busy]="feedback.busy()"
              (saved)="saveRoles($event)"
            />
          </div>
        }
      </div>
    }
    @if (view === 'activities') {
      <div class="surface">
        <h3 class="h4">Supervisión de actividades</h3>
        @for (a of activities(); track a.id_actividad) {
          <div class="border-top py-3 d-flex gap-3 justify-content-between flex-wrap">
            <div>
              <h4 class="h6">{{ a.titulo }}</h4>
              <span class="pill">{{ a.estado | label }}</span><span class="small ms-2">{{
                a.fecha_inicio | date: 'dd/MM/yyyy HH:mm'
              }}</span>
            </div>
            @if (!['finalizada', 'cancelada'].includes(a.estado)) {
              <button class="btn btn-sm btn-outline-danger" (click)="cancel(a)">
                Cancelar con motivo
              </button>
            }
          </div>
        } @empty {
          <p>No hay actividades.</p>
        }
      </div>
    }
    @if (view === 'categoria' || view === 'habilidad') {
      <div class="surface">
        <h3 class="h4">{{ view === 'categoria' ? 'Categorías' : 'Habilidades' }}</h3>
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Estado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              @for (i of catalog(); track $index) {
                <tr>
                  <td>{{ i.nombre }}</td>
                  <td>{{ i.activo ? 'Activo' : 'Inactivo' }}</td>
                  <td>
                    <button class="btn btn-sm btn-outline-primary" (click)="catalogTarget.set(i)">
                      Editar
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        <h4 class="h5 mt-4">{{ catalogTarget() ? 'Editar registro' : 'Crear registro' }}</h4>
        <app-record-form
          [fields]="catalogFields"
          [initial]="catalogTarget()"
          label="Guardar catálogo"
          [busy]="feedback.busy()"
          (saved)="saveCatalog($event)"
        />
        @if (catalogTarget()) {
          <button class="btn btn-link mt-2" (click)="catalogTarget.set(null)">
            Crear otro registro
          </button>
        }
      </div>
    }
    @if (view === 'audit') {
      <div class="surface">
        <h3 class="h4">Bitácora de eventos</h3>
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Acción</th>
                <th>Entidad</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              @for (e of events(); track e.id_evento) {
                <tr>
                  <td>{{ e.fecha_evento | date: 'dd/MM/yyyy HH:mm' }}</td>
                  <td>{{ e.accion }}</td>
                  <td>{{ e.entidad }}</td>
                  <td>{{ e.detalle }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }
    @if (!['categoria', 'habilidad'].includes(view)) {
      <nav class="pagination-bar" aria-label="Páginas de administración">
        <button
          class="btn btn-outline-primary"
          [disabled]="page === 1"
          (click)="load(view, page - 1)"
        >
          Anterior</button
        ><span>Página {{ page }}</span
        ><button
          class="btn btn-outline-primary"
          [disabled]="currentSize() < (view === 'audit' ? 30 : 20)"
          (click)="load(view, page + 1)"
        >
          Siguiente
        </button>
      </nav>
    }
  `,
})
export class AdminPage implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  view = 'organizations';
  page = 1;
  selectedOrg = signal(0);
  stats = signal<Record<string, number>>({});
  organizations = signal<Organization[]>([]);
  documents = signal<Document[]>([]);
  users = signal<User[]>([]);
  activities = signal<Activity[]>([]);
  events = signal<Audit[]>([]);
  catalog = signal<CatalogItem[]>([]);
  catalogTarget = signal<CatalogItem | null>(null);
  roleTarget = signal<User | null>(null);
  selectedRoles: string[] = [];
  private selection = 0;
  roleOptions = ['administrador', 'voluntario', 'organizacion'];
  tabs = [
    { key: 'organizations', label: 'Organizaciones' },
    { key: 'users', label: 'Usuarios' },
    { key: 'activities', label: 'Actividades' },
    { key: 'categoria', label: 'Categorías' },
    { key: 'habilidad', label: 'Habilidades' },
    { key: 'audit', label: 'Bitácora' },
  ];
  reasonFields: Field[] = [
    { key: 'motivo', label: 'Motivo del cambio', required: true, min: 5, max: 1000 },
  ];
  catalogFields: Field[] = [
    { key: 'nombre', label: 'Nombre', required: true, min: 2, max: 100 },
    { key: 'descripcion', label: 'Descripción', type: 'textarea', max: 500 },
    { key: 'activo', label: 'Activo', type: 'checkbox' },
  ];
  async ngOnInit() {
    await this.load('organizations');
  }
  statsCards() {
    const s = this.stats();
    return [
      { label: 'Usuarios', value: s['usuarios'] ?? 0 },
      { label: 'Organizaciones pendientes', value: s['organizaciones_pendientes'] ?? 0 },
      { label: 'Actividades', value: s['actividades'] ?? 0 },
      { label: 'Inscripciones', value: s['inscripciones'] ?? 0 },
    ];
  }
  async load(view: string, page = 1) {
    const ticket = ++this.selection;
    await this.feedback.run(async () => {
      const stats = await this.api.get<Record<string, number>>('/admin/statistics');
      if (ticket !== this.selection) return;
      this.stats.set(stats);
      this.view = view;
      this.page = page;
      this.selectedOrg.set(0);
      this.catalogTarget.set(null);
      this.roleTarget.set(null);
      if (view === 'organizations')
        this.organizations.set(
          await this.api.get<Organization[]>('/admin/organizations?page=' + page),
        );
      else if (view === 'users')
        this.users.set(await this.api.get<User[]>('/admin/users?page=' + page));
      else if (view === 'activities')
        this.activities.set(await this.api.get<Activity[]>('/admin/activities?page=' + page));
      else if (view === 'audit')
        this.events.set(await this.api.get<Audit[]>('/admin/audit?page=' + page));
      else this.catalog.set(await this.api.get<CatalogItem[]>('/admin/catalogs/' + view));
    });
  }
  currentSize() {
    return this.view === 'users'
      ? this.users().length
      : this.view === 'organizations'
        ? this.organizations().length
        : this.view === 'activities'
          ? this.activities().length
          : this.events().length;
  }
  async selectOrg(o: Organization) {
    const ticket = ++this.selection;
    this.selectedOrg.set(0);
    this.documents.set([]);
    await this.feedback.run(async () => {
      const docs = await this.api.get<Document[]>(
        '/admin/organizations/' + o.id_organizacion + '/documents',
      );
      if (ticket !== this.selection) return;
      this.documents.set(docs);
      this.selectedOrg.set(o.id_organizacion);
    });
  }
  async review(d: Document, state: string) {
    const motivo = reason('Confirma la revisión del documento.');
    if (!motivo) return;
    const id = this.selectedOrg();
    const r = await this.feedback.run(() =>
      this.api.post('/admin/documents/' + d.id_documento + '/review', { estado: state, motivo }),
    );
    if (r) {
      await this.feedback.run(async () => {
        const docs = await this.api.get<Document[]>('/admin/organizations/' + id + '/documents');
        if (this.selectedOrg() === id) this.documents.set(docs);
      });
    }
  }
  async orgState(o: Organization, state: string) {
    const motivo = reason(
      'Actualizar estado de ' + o.nombre + '. La suspensión oculta sus actividades públicas.',
    );
    if (!motivo) return;
    const r = await this.feedback.run(() =>
      this.api.post('/admin/organizations/' + o.id_organizacion + '/state', {
        estado: state,
        motivo,
      }),
    );
    if (r) await this.load(this.view, this.page);
  }
  async userState(u: User) {
    const motivo = reason('Cambiar el estado de ' + u.correo + ' y revocar sus sesiones.');
    if (!motivo) return;
    const r = await this.feedback.run(() =>
      this.api.post('/admin/users/' + u.id_usuario + '/state', {
        estado: u.estado === 'activo' ? 'suspendido' : 'activo',
        motivo,
      }),
    );
    if (r) await this.load(this.view, this.page);
  }
  editRoles(u: User) {
    this.roleTarget.set(u);
    this.selectedRoles = [...u.roles];
  }
  toggleRole(r: string, e: Event) {
    this.selectedRoles = (e.target as HTMLInputElement).checked
      ? [...this.selectedRoles, r]
      : this.selectedRoles.filter((x) => x !== r);
  }
  async saveRoles(v: FormValue) {
    if (!window.confirm('¿Confirmas estos roles? Las sesiones de esta cuenta se revocarán.'))
      return;
    const r = await this.feedback.run(() =>
      this.api.post('/admin/users/' + this.roleTarget()!.id_usuario + '/roles', {
        roles: this.selectedRoles,
        motivo: v['motivo'],
      }),
    );
    if (r) await this.load(this.view, this.page);
  }
  async cancel(a: Activity) {
    const motivo = reason('Cancelar ' + a.titulo + ' y todas sus inscripciones activas.');
    if (!motivo) return;
    const r = await this.feedback.run(() =>
      this.api.post('/admin/activities/' + a.id_actividad + '/cancel', { motivo }),
    );
    if (r) await this.load(this.view, this.page);
  }
  async saveCatalog(v: FormValue) {
    const target = this.catalogTarget();
    const id = target?.id_categoria ?? target?.id_habilidad;
    const r = await this.feedback.run(() =>
      id
        ? this.api.put('/admin/catalogs/' + this.view + '/' + id, v)
        : this.api.post('/admin/catalogs/' + this.view, v),
    );
    if (r) await this.load(this.view);
  }
}
