import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { Api, Feedback } from '../services/api';
import { Activity, Application, Catalogs, Skill, Impact, Evidence } from '../models/domain';
import { RecordForm, Field, FormValue } from '../components/record-form';
import { SkillsEditor } from '../components/skills-editor';
import { LabelPipe, LABELS } from '../components/labels';
import { optional, withLocation, localDate, reason } from '../components/domain-fields';

@Component({
  imports: [RouterLink, DatePipe, RecordForm, SkillsEditor, LabelPipe],
  template: ` <a routerLink="/panel/organizacion" class="small"
      ><i class="bi bi-arrow-left"></i> Mis organizaciones</a
    >
    <div class="section-title mt-3">
      <div>
        <div class="eyebrow">Gestión de actividad</div>
        <h2 class="mt-2">{{ activity()?.titulo || 'Crea una nueva oportunidad' }}</h2>
      </div>
      @if (activity(); as a) {
        <span class="pill">{{ a.estado | label }}</span>
      }
    </div>
    @if (activity(); as a) {
      <div class="surface">
        <div class="row g-3">
          <div class="col-sm-6">
            <div class="small-label">Inicio y fin</div>
            {{ a.fecha_inicio | date: 'dd/MM/yyyy HH:mm' }}<br />{{
              a.fecha_fin | date: 'dd/MM/yyyy HH:mm'
            }}
          </div>
          <div class="col-sm-6">
            <div class="small-label">Cupo máximo</div>
            {{ a.cupo_maximo }} personas
          </div>
        </div>
        <div class="action-row mt-3">
          @for (s of stateActions(a); track s) {
            <button
              [class]="s === 'cancelada' ? 'btn btn-outline-danger' : 'btn btn-outline-primary'"
              [disabled]="feedback.busy()"
              (click)="state(s)"
            >
              {{ actionLabel(s) }}
            </button>
          }
        </div>
      </div>
    }
    @if (!activity() || canEdit()) {
      <details class="surface" [open]="!activity() || activity()?.estado === 'borrador'">
        <summary class="fw-semibold">
          {{ activity() ? 'Editar actividad' : 'Datos de la actividad' }}
        </summary>
        <p class="small text-secondary mt-3">
          Las horas usan la zona horaria de tu dispositivo. Las modalidades presencial e híbrida
          requieren lugar y dirección.
        </p>
        <app-skills
          [catalog]="catalogs()?.habilidades ?? []"
          [(skills)]="skills"
          [requiredMode]="true"
        /><app-record-form
          [fields]="fields"
          [initial]="initial()"
          [label]="activity() ? 'Guardar cambios' : 'Crear borrador'"
          [busy]="feedback.busy()"
          (saved)="save($event)"
        />
      </details>
    }
    @if (activity(); as a) {
      <div class="surface">
        <h3 class="h4">Postulantes y participación</h3>
        @for (i of applicants(); track i.id_inscripcion) {
          <article class="border-top py-3">
            <div class="section-title mb-2">
              <div>
                <h4 class="h6 mb-1">{{ i.nombres }} {{ i.apellidos }}</h4>
                <span class="pill">{{ i.estado | label }}</span>
                @if (i.asistencia) {
                  <span class="small ms-2">{{ i.asistencia | label }}</span>
                }
              </div>
              <div class="action-row">
                @if (beforeStart() && ['pendiente', 'espera'].includes(i.estado)) {
                  <button
                    class="btn btn-primary btn-sm"
                    (click)="applicationState(i, 'aceptada')"
                    [disabled]="feedback.busy()"
                  >
                    Aceptar
                  </button>
                  @if (i.estado === 'pendiente') {
                    <button
                      class="btn btn-outline-primary btn-sm"
                      (click)="applicationState(i, 'espera')"
                      [disabled]="feedback.busy()"
                    >
                      Lista de espera
                    </button>
                  }
                  <button
                    class="btn btn-outline-danger btn-sm"
                    (click)="applicationState(i, 'rechazada')"
                    [disabled]="feedback.busy()"
                  >
                    Rechazar
                  </button>
                }
                @if (canAttendance(i)) {
                  <button class="btn btn-outline-primary btn-sm" (click)="editAttendance(i)">
                    Registrar asistencia
                  </button>
                }
                @if (a.estado === 'finalizada' && i.asistencia === 'asistio' && !i.id_certificado) {
                  <button
                    class="btn btn-primary btn-sm"
                    (click)="certificate(i)"
                    [disabled]="feedback.busy()"
                  >
                    Emitir certificado
                  </button>
                }
                @if (i.id_certificado) {
                  <span class="pill">Certificado emitido</span>
                }
              </div>
            </div>
            <p class="small mb-0">{{ i.motivacion }}</p>
            @if (i.hora_entrada) {
              <div class="small text-secondary">
                Asistencia: {{ i.hora_entrada | date: 'dd/MM/yyyy HH:mm' }} a
                {{ i.hora_salida | date: 'HH:mm' }}
              </div>
            }
            @if (attendanceTarget === i.id_inscripcion) {
              <div class="border rounded p-3 mt-3">
                <h4 class="h6">Asistencia de {{ i.nombres }}</h4>
                <p class="small text-secondary">
                  Indica entrada y salida juntas, dentro del horario de la actividad. No se puede
                  editar una asistencia certificada.
                </p>
                <app-record-form
                  [fields]="attendanceFields"
                  [initial]="attendanceInitial()"
                  label="Guardar asistencia"
                  [busy]="feedback.busy()"
                  (saved)="saveAttendance($event)"
                />
              </div>
            }
          </article>
        } @empty {
          <p class="text-secondary mt-3">Todavía no hay postulaciones.</p>
        }
        <nav class="pagination-bar" aria-label="Páginas de postulantes">
          <button
            class="btn btn-sm btn-outline-primary"
            [disabled]="page === 1"
            (click)="loadApplicants(page - 1)"
          >
            Anterior</button
          ><span>{{ page }}</span
          ><button
            class="btn btn-sm btn-outline-primary"
            [disabled]="applicants().length < 20"
            (click)="loadApplicants(page + 1)"
          >
            Siguiente
          </button>
        </nav>
      </div>
      @if (a.estado === 'finalizada') {
        <div class="surface">
          <h3 class="h4">Impacto registrado</h3>
          <p class="small text-secondary">
            Las horas se calculan a partir de asistencias efectivas y se mantienen sincronizadas.
          </p>
          @if (impact()) {
            <p class="pill">{{ impact()?.horas_voluntariado }} horas de voluntariado</p>
          }
          <app-record-form
            [fields]="impactFields"
            [initial]="impact()"
            label="Guardar impacto"
            [busy]="feedback.busy()"
            (saved)="saveImpact($event)"
          />
        </div>
      }
      <details class="surface">
        <summary class="fw-semibold">Evidencias privadas</summary>
        <p class="small text-secondary mt-3">
          Imágenes hasta 5 MB o PDF hasta 10 MB. No subas información personal de terceros.
        </p>
        @for (e of evidence(); track e.id_evidencia) {
          <p>
            <a
              [href]="
                '/api/v1/manage/activities/' +
                a.id_actividad +
                '/evidence/' +
                e.id_evidencia +
                '/file'
              "
              >{{ e.descripcion }} <i class="bi bi-download"></i
            ></a>
          </p>
        }
        <label for="evidence-file" class="form-label">Seleccionar archivo</label
        ><input
          id="evidence-file"
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf"
          class="form-control mb-3"
          (change)="chooseFile($event)"
        /><app-record-form
          [fields]="evidenceFields"
          label="Subir evidencia privada"
          [busy]="feedback.busy()"
          (saved)="uploadEvidence($event)"
        />
      </details>
    }`,
})
export class ManageActivity implements OnInit {
  api = inject(Api);
  feedback = inject(Feedback);
  route = inject(ActivatedRoute);
  router = inject(Router);
  activity = signal<Activity | null>(null);
  catalogs = signal<Catalogs | null>(null);
  applicants = signal<Application[]>([]);
  impact = signal<Impact | null>(null);
  evidence = signal<Evidence[]>([]);
  initial = signal<object | null>(null);
  skills: Skill[] = [];
  fields: Field[] = [];
  page = 1;
  attendanceTarget = 0;
  attendanceInitial = signal<object | null>(null);
  file: File | null = null;
  attendanceFields: Field[] = [
    {
      key: 'estado',
      label: 'Asistencia',
      type: 'select',
      required: true,
      options: [
        { value: 'asistio', label: 'Asistió' },
        { value: 'no_asistio', label: 'No asistió' },
        { value: 'justificado', label: 'Justificado' },
      ],
    },
    { key: 'hora_entrada', label: 'Hora de entrada', type: 'datetime-local' },
    { key: 'hora_salida', label: 'Hora de salida', type: 'datetime-local' },
    { key: 'observacion', label: 'Observación', type: 'textarea', max: 2000 },
  ];
  impactFields: Field[] = [
    {
      key: 'beneficiarios_estimados',
      label: 'Beneficiarios estimados',
      type: 'number',
      required: true,
      min: 0,
      max: 10000000,
    },
    {
      key: 'descripcion_impacto',
      label: 'Resultados alcanzados',
      type: 'textarea',
      required: true,
      min: 10,
      max: 4000,
    },
  ];
  evidenceFields: Field[] = [
    {
      key: 'descripcion',
      label: 'Descripción de la evidencia',
      type: 'textarea',
      required: true,
      min: 5,
      max: 1000,
    },
  ];
  async ngOnInit() {
    await this.feedback.run(async () => {
      const c = await this.api.get<Catalogs>('/catalogs');
      this.catalogs.set(c);
      this.fields = [
        { key: 'titulo', label: 'Título de la actividad', required: true, min: 5, max: 160 },
        {
          key: 'id_categoria',
          label: 'Categoría',
          type: 'select',
          required: true,
          options: c.categorias.map((v) => ({ value: v.id_categoria!, label: v.nombre })),
        },
        {
          key: 'descripcion',
          label: 'Descripción y propósito',
          type: 'textarea',
          required: true,
          min: 20,
          max: 6000,
        },
        { key: 'fecha_inicio', label: 'Inicio', type: 'datetime-local', required: true },
        { key: 'fecha_fin', label: 'Fin', type: 'datetime-local', required: true },
        {
          key: 'fecha_cierre_inscripcion',
          label: 'Cierre de inscripción',
          type: 'datetime-local',
          required: true,
        },
        {
          key: 'cupo_maximo',
          label: 'Cupo máximo',
          type: 'number',
          required: true,
          min: 1,
          max: 100000,
        },
        {
          key: 'modalidad',
          label: 'Modalidad',
          type: 'select',
          required: true,
          options: [
            { value: 'presencial', label: 'Presencial' },
            { value: 'virtual', label: 'Virtual' },
            { value: 'hibrida', label: 'Híbrida' },
          ],
        },
        { key: 'imagen_portada_url', label: 'Imagen de portada (URL HTTPS)' },
        { key: 'lugar', label: 'Lugar o ciudad' },
        { key: 'direccion', label: 'Dirección' },
      ];
    });
    if (this.route.snapshot.paramMap.has('id')) await this.load();
  }
  async load() {
    await this.feedback.run(async () => {
      const id = this.route.snapshot.paramMap.get('id');
      const [a, p, i, e] = await Promise.all([
        this.api.get<Activity>('/manage/activities/' + id),
        this.api.get<Application[]>('/manage/activities/' + id + '/applications'),
        this.api.get<Impact | null>('/manage/activities/' + id + '/impact'),
        this.api.get<Evidence[]>('/manage/activities/' + id + '/evidence'),
      ]);
      this.activity.set(a);
      this.skills = a.habilidades ?? [];
      this.initial.set({
        ...a,
        fecha_inicio: localDate(a.fecha_inicio),
        fecha_fin: localDate(a.fecha_fin),
        fecha_cierre_inscripcion: localDate(a.fecha_cierre_inscripcion),
        lugar: a.ubicacion?.nombre_lugar,
        direccion: a.ubicacion?.direccion,
      });
      this.applicants.set(p);
      this.impact.set(i);
      this.evidence.set(e);
      this.attendanceTarget = 0;
      this.page = 1;
    });
  }
  canEdit() {
    const a = this.activity();
    return (
      !!a &&
      ['borrador', 'publicada', 'cerrada'].includes(a.estado) &&
      (a.estado === 'borrador' || new Date(a.fecha_inicio) > new Date())
    );
  }
  beforeStart() {
    const a = this.activity();
    return (
      !!a && ['publicada', 'cerrada'].includes(a.estado) && new Date(a.fecha_inicio) > new Date()
    );
  }
  stateActions(a: Activity) {
    const states: Record<string, string[]> = {
      borrador: ['publicada', 'cancelada'],
      publicada: ['cerrada', 'en_curso', 'cancelada'],
      cerrada: ['en_curso', 'cancelada'],
      en_curso: ['finalizada', 'cancelada'],
    };
    return (states[a.estado] ?? [])
      .filter((s) => s !== 'en_curso' || new Date(a.fecha_inicio) <= new Date())
      .filter((s) => s !== 'finalizada' || new Date(a.fecha_fin) <= new Date());
  }
  actionLabel(s: string) {
    return (
      (
        {
          publicada: 'Publicar',
          cerrada: 'Cerrar inscripciones',
          en_curso: 'Iniciar actividad',
          finalizada: 'Finalizar actividad',
          cancelada: 'Cancelar actividad',
        } as Record<string, string>
      )[s] ?? LABELS[s]
    );
  }
  async save(v: FormValue) {
    const body = {
      ...withLocation(optional(v, ['imagen_portada_url'])),
      id_categoria: Number(v['id_categoria']),
      cupo_maximo: Number(v['cupo_maximo']),
      fecha_inicio: new Date(String(v['fecha_inicio'])).toISOString(),
      fecha_fin: new Date(String(v['fecha_fin'])).toISOString(),
      fecha_cierre_inscripcion: new Date(String(v['fecha_cierre_inscripcion'])).toISOString(),
      habilidades: this.skills.map((s) => ({
        id_habilidad: s.id_habilidad,
        nivel_requerido: s.nivel_requerido,
        obligatoria: s.obligatoria,
      })),
    };
    const result = await this.feedback.run(async () => {
      if (this.activity())
        return this.api.put<Activity>('/manage/activities/' + this.activity()!.id_actividad, body);
      return this.api.post<Activity>(
        '/organization/' + this.route.snapshot.paramMap.get('org') + '/activities',
        body,
      );
    });
    if (result) {
      if (!this.activity()) {
        await this.router.navigate(['/panel/actividad', result.id_actividad]);
      } else await this.load();
    }
  }
  async state(s: string) {
    let motivo = '';
    if (s === 'cancelada') {
      const r = reason('Cancelar la actividad cancelará todas las inscripciones activas.');
      if (!r) return;
      motivo = r;
    } else if (!window.confirm('¿' + this.actionLabel(s) + '?')) return;
    const r = await this.feedback.run(() =>
      this.api.post('/manage/activities/' + this.activity()!.id_actividad + '/state', {
        estado: s,
        motivo,
      }),
    );
    if (r) await this.load();
  }
  async applicationState(i: Application, s: string) {
    const note = s === 'rechazada' ? reason('Rechazar esta postulación') : '';
    if (s === 'rechazada' && !note) return;
    const r = await this.feedback.run(() =>
      this.api.post('/applications/' + i.id_inscripcion + '/state', {
        estado: s,
        observacion: note ?? '',
      }),
    );
    if (r) await this.loadApplicants(this.page);
  }
  async loadApplicants(page: number) {
    await this.feedback.run(async () => {
      this.applicants.set(
        await this.api.get<Application[]>(
          '/manage/activities/' + this.activity()!.id_actividad + '/applications?page=' + page,
        ),
      );
      this.page = page;
    });
  }
  canAttendance(i: Application) {
    const a = this.activity();
    return (
      !!a &&
      a.estado !== 'cancelada' &&
      new Date(a.fecha_inicio) <= new Date() &&
      ['aceptada', 'finalizada'].includes(i.estado) &&
      !i.id_certificado
    );
  }
  editAttendance(i: Application) {
    this.attendanceTarget = i.id_inscripcion;
    this.attendanceInitial.set({
      estado: i.asistencia ?? 'asistio',
      hora_entrada: localDate(i.hora_entrada),
      hora_salida: localDate(i.hora_salida),
      observacion: '',
    });
  }
  async saveAttendance(v: FormValue) {
    const body = {
      ...v,
      hora_entrada: v['hora_entrada'] ? new Date(String(v['hora_entrada'])).toISOString() : null,
      hora_salida: v['hora_salida'] ? new Date(String(v['hora_salida'])).toISOString() : null,
    };
    const r = await this.feedback.run(() =>
      this.api.put('/manage/applications/' + this.attendanceTarget + '/attendance', body),
    );
    if (r) await this.load();
  }
  async saveImpact(v: FormValue) {
    const r = await this.feedback.run(() =>
      this.api.put('/manage/activities/' + this.activity()!.id_actividad + '/impact', {
        ...v,
        beneficiarios_estimados: Number(v['beneficiarios_estimados']),
      }),
    );
    if (r) await this.load();
  }
  async certificate(i: Application) {
    if (
      !window.confirm(
        'El código permitirá consultar públicamente nombre, actividad, organización, horas y fecha. La asistencia quedará protegida contra edición. ¿Emitir certificado?',
      )
    )
      return;
    const r = await this.feedback.run(() =>
      this.api.post('/manage/applications/' + i.id_inscripcion + '/certificate', {
        acepta_visibilidad_publica: true,
      }),
    );
    if (r) await this.load();
  }
  chooseFile(e: Event) {
    this.file = (e.target as HTMLInputElement).files?.[0] ?? null;
  }
  async uploadEvidence(v: FormValue) {
    if (!this.file) {
      this.feedback.error.set('Selecciona una imagen o PDF para continuar.');
      return;
    }
    const data = new FormData();
    data.set('file', this.file);
    data.set('descripcion', String(v['descripcion']));
    const r = await this.feedback.run(() =>
      this.api.post('/manage/activities/' + this.activity()!.id_actividad + '/evidence', data),
    );
    if (r) {
      this.file = null;
      await this.load();
    }
  }
}
