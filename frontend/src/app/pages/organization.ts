import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { Session } from '../services/session';
import { Organization, Activity, Document, Member } from '../models/domain';
import { RecordForm, Field, FormValue } from '../components/record-form';
import { organizationFields, optional, withLocation } from '../components/domain-fields';
import { LabelPipe } from '../components/labels';

@Component({
  imports: [RouterLink, DatePipe, RecordForm, LabelPipe],
  template: ` <div class="section-title">
      <div>
        <h2>Mis organizaciones</h2>
        <p class="text-secondary mb-0">Gestiona tus causas y acompaña a tu comunidad.</p>
      </div>
      <button class="btn btn-primary" (click)="showCreate = !showCreate">
        {{ showCreate ? 'Cerrar formulario' : 'Registrar organización' }}
      </button>
    </div>
    @if (showCreate) {
      <div class="surface">
        <h3 class="h4">Una nueva causa empieza aquí</h3>
        <app-record-form
          [fields]="organizationFields"
          label="Registrar organización"
          [busy]="feedback.busy()"
          (saved)="create($event)"
        />
      </div>
    }
    <div class="row g-3 mb-4">
      @for (o of organizations(); track o.id_organizacion) {
        <div class="col-md-6">
          <button
            class="surface text-start w-100 mb-0"
            type="button"
            (click)="select(o.id_organizacion)"
          >
            <span class="pill">{{ o.estado_verificacion | label }}</span>
            <h3 class="h5 mt-2">{{ o.nombre }}</h3>
            <span class="small text-secondary"
              >{{ o.cargo | label }} · Abrir gestión <i class="bi bi-arrow-right"></i
            ></span>
          </button>
        </div>
      } @empty {
        <div class="col-12">
          <div class="empty">Aún no administras organizaciones. Registra una para empezar.</div>
        </div>
      }
    </div>
    @if (selected(); as o) {
      <div class="section-title">
        <h2 class="h3">{{ o.nombre }}</h2>
        <span class="pill">{{ o.estado_verificacion | label }}</span>
      </div>
      @if (o.estado_verificacion === 'suspendida') {
        <div class="alert alert-warning">
          Esta organización está suspendida. Contacta con el administrador responsable.
        </div>
      }
      <div class="row g-3 mb-4">
        @for (s of stats(o); track s.label) {
          <div class="col-6 col-lg">
            <div class="surface mb-0">
              <div class="stat-value">{{ s.value }}</div>
              <div class="small-label">{{ s.label }}</div>
            </div>
          </div>
        }
      </div>
      @if (o.revisiones?.length) {
        <details class="surface">
          <summary>Observaciones de revisión</summary>
          @for (r of o.revisiones; track $index) {
            <p class="mt-2 mb-0">{{ r.detalle }} · {{ r.fecha_evento | date: 'dd/MM/yyyy' }}</p>
          }
        </details>
      }
      @if (o.estado_verificacion !== 'suspendida') {
        <div class="surface">
          <div class="section-title">
            <h3 class="h4 mb-0">Actividades</h3>
            <a class="btn btn-primary" [routerLink]="['/panel/actividad/nueva', o.id_organizacion]"
              >Crear actividad</a
            >
          </div>
          @for (a of activities(); track a.id_actividad) {
            <div
              class="border-top py-3 d-flex gap-3 justify-content-between align-items-center flex-wrap"
            >
              <div>
                <span class="pill mb-2">{{ a.estado | label }}</span>
                <h4 class="h6 mb-1">{{ a.titulo }}</h4>
                <span class="small text-secondary"
                  >{{ a.fecha_inicio | date: 'dd/MM/yyyy HH:mm' }} ·
                  {{ a.cupos_disponibles }} cupos</span
                >
              </div>
              <a
                class="btn btn-outline-primary btn-sm"
                [routerLink]="['/panel/actividad', a.id_actividad]"
                >Gestionar</a
              >
            </div>
          } @empty {
            <p class="text-secondary">
              Todavía no hay actividades. Crea un borrador para comenzar.
            </p>
          }
          <nav class="pagination-bar" aria-label="Páginas de actividades">
            <button
              class="btn btn-sm btn-outline-primary"
              [disabled]="page === 1"
              (click)="loadActivities(page - 1)"
            >
              Anterior</button
            ><span>{{ page }}</span
            ><button
              class="btn btn-sm btn-outline-primary"
              [disabled]="activities().length < 20"
              (click)="loadActivities(page + 1)"
            >
              Siguiente
            </button>
          </nav>
        </div>
        <details class="surface">
          <summary class="fw-semibold">Documentos de verificación</summary>
          <p class="small text-secondary mt-3">
            Solo PDF hasta 10 MB. Los documentos son privados. Usa exclusivamente datos ficticios
            durante la demostración.
          </p>
          @for (d of documents(); track d.id_documento) {
            <div class="border-top py-2 d-flex gap-2 flex-wrap align-items-center">
              <span>{{ d.tipo_documento }} · {{ d.numero_documento }}</span
              ><span class="pill">{{ d.estado_revision | label }}</span
              ><a
                [href]="
                  '/api/v1/organization/' +
                  o.id_organizacion +
                  '/documents/' +
                  d.id_documento +
                  '/file'
                "
                >Descargar</a
              >
            </div>
          }
          @if (o.cargo === 'administrador') {
            <div class="mt-3 mb-3">
              <label class="form-label" for="org-document">Documento PDF</label
              ><input
                id="org-document"
                type="file"
                accept="application/pdf"
                class="form-control"
                (change)="chooseFile($event)"
              />
            </div>
            <app-record-form
              [fields]="documentFields"
              label="Subir documento privado"
              [busy]="feedback.busy()"
              (saved)="upload($event)"
            />
          }
        </details>
        @if (o.cargo === 'administrador') {
          <details class="surface">
            <summary class="fw-semibold">Perfil de la organización</summary>
            <div class="mt-3">
              <app-record-form
                [fields]="organizationFields"
                [initial]="editValues()"
                label="Guardar organización"
                [busy]="feedback.busy()"
                (saved)="update($event)"
              />
            </div>
          </details>
          <details class="surface">
            <summary class="fw-semibold">Miembros y permisos</summary>
            <div class="table-responsive mt-3">
              <table class="table">
                <thead>
                  <tr>
                    <th>Cuenta</th>
                    <th>Cargo</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  @for (m of members(); track m.id_usuario) {
                    <tr>
                      <td>{{ m.correo }}</td>
                      <td>{{ m.cargo | label }}</td>
                      <td>{{ m.estado | label }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
            <p class="small text-secondary">
              La cuenta debe existir y estar verificada. No se puede retirar al último administrador
              activo.
            </p>
            <app-record-form
              [fields]="memberFields"
              label="Agregar o actualizar miembro"
              [busy]="feedback.busy()"
              (saved)="saveMember($event)"
            />
          </details>
        }
      }
    }`,
})
export class OrganizationPage implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  session = inject(Session);
  organizations = signal<Organization[]>([]);
  selected = signal<Organization | null>(null);
  activities = signal<Activity[]>([]);
  documents = signal<Document[]>([]);
  members = signal<Member[]>([]);
  editValues = signal<object | null>(null);
  showCreate = false;
  file: File | null = null;
  private fileInput: HTMLInputElement | null = null;
  page = 1;
  private selection = 0;
  organizationFields = organizationFields;
  documentFields: Field[] = [
    { key: 'tipo_documento', label: 'Tipo de documento', required: true, min: 2, max: 80 },
    { key: 'numero_documento', label: 'Número o referencia', required: true, min: 2, max: 80 },
  ];
  memberFields: Field[] = [
    { key: 'correo', label: 'Correo de la cuenta', type: 'email', required: true },
    {
      key: 'cargo',
      label: 'Cargo',
      type: 'select',
      required: true,
      options: [
        { value: 'administrador', label: 'Administrador' },
        { value: 'coordinador', label: 'Coordinador' },
      ],
    },
    {
      key: 'estado',
      label: 'Estado',
      type: 'select',
      required: true,
      options: [
        { value: 'activo', label: 'Activo' },
        { value: 'inactivo', label: 'Inactivo' },
      ],
    },
  ];
  async ngOnInit() {
    await this.load();
  }
  async load() {
    await this.feedback.run(async () =>
      this.organizations.set(await this.api.get<Organization[]>('/organization')),
    );
  }
  body(v: FormValue) {
    return withLocation(optional(v, ['telefono', 'sitio_web', 'logo_url']));
  }
  async create(v: FormValue) {
    const o = await this.feedback.run(() =>
      this.api.post<Organization>('/organization', this.body(v)),
    );
    if (o) {
      this.showCreate = false;
      await this.feedback.run(() => this.session.refresh());
      await this.load();
      await this.select(o.id_organizacion);
    }
  }
  async select(id: number) {
    const ticket = ++this.selection;
    if (this.selected()?.id_organizacion !== id) {
      this.selected.set(null);
      this.activities.set([]);
      this.documents.set([]);
      this.members.set([]);
    }
    this.file = null;
    if (this.fileInput) this.fileInput.value = '';
    await this.feedback.run(async () => {
      const o = await this.api.get<Organization>('/organization/' + id);
      if (ticket !== this.selection) return;
      if (o.estado_verificacion === 'suspendida') {
        this.selected.set(o);
        return;
      }
      const [a, d, m] = await Promise.all([
        this.api.get<Activity[]>('/organization/' + id + '/activities'),
        this.api.get<Document[]>('/organization/' + id + '/documents'),
        o.cargo === 'administrador'
          ? this.api.get<Member[]>('/organization/' + id + '/members')
          : Promise.resolve([]),
      ]);
      if (ticket !== this.selection) return;
      this.selected.set(o);
      this.editValues.set({
        ...o,
        lugar: o.ubicacion?.nombre_lugar,
        direccion: o.ubicacion?.direccion,
      });
      this.activities.set(a);
      this.documents.set(d);
      this.page = 1;
      this.members.set(m);
    });
  }
  stats(o: Organization) {
    const s = o.estadisticas ?? {};
    return [
      { label: 'Actividades', value: s['actividades'] ?? 0 },
      { label: 'Inscripciones', value: s['inscritos'] ?? 0 },
      { label: 'Asistencias', value: s['asistencias'] ?? 0 },
      { label: 'Horas', value: s['horas'] ?? 0 },
      { label: 'Beneficiarios', value: s['beneficiarios'] ?? 0 },
    ];
  }
  async loadActivities(page: number) {
    await this.feedback.run(async () => {
      this.activities.set(
        await this.api.get<Activity[]>(
          '/organization/' + this.selected()!.id_organizacion + '/activities?page=' + page,
        ),
      );
      this.page = page;
    });
  }
  async update(v: FormValue) {
    const r = await this.feedback.run(() =>
      this.api.put('/organization/' + this.selected()!.id_organizacion, this.body(v)),
    );
    if (r) {
      await this.load();
      await this.select(this.selected()!.id_organizacion);
    }
  }
  chooseFile(e: Event) {
    this.fileInput = e.target as HTMLInputElement;
    this.file = this.fileInput.files?.[0] ?? null;
  }
  async upload(v: FormValue) {
    if (!this.file) {
      this.feedback.error.set('Selecciona un PDF antes de subir el documento.');
      return;
    }
    const body = new FormData();
    body.set('file', this.file);
    body.set('tipo_documento', String(v['tipo_documento']));
    body.set('numero_documento', String(v['numero_documento']));
    const r = await this.feedback.run(() =>
      this.api.post('/organization/' + this.selected()!.id_organizacion + '/documents', body),
    );
    if (r) {
      this.file = null;
      await this.select(this.selected()!.id_organizacion);
    }
  }
  async saveMember(v: FormValue) {
    if (!window.confirm('¿Confirmas el cargo y estado de esta membresía?')) return;
    const r = await this.feedback.run(() =>
      this.api.put('/organization/' + this.selected()!.id_organizacion + '/members', v),
    );
    if (r) await this.select(this.selected()!.id_organizacion);
  }
}
