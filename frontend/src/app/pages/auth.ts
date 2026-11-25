import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Api, Feedback } from '../services/api';
import { Session } from '../services/session';
import { RecordForm, Field, FormValue } from '../components/record-form';

@Component({
  imports: [RecordForm, RouterLink],
  template: `<section class="container">
    <div class="surface auth-card">
      <div class="eyebrow mb-2">Bienvenido a Voluntia</div>
      <h1 class="h2">{{ title }}</h1>
      <p class="text-secondary">{{ description }}</p>
      @if (closed) {
        <div class="alert alert-info">
          El registro público y la recuperación por correo están cerrados en esta demostración.
          Utiliza una cuenta ficticia entregada de forma privada por el responsable.
        </div>
      } @else {
        <app-record-form
          [fields]="fields"
          [label]="button"
          [busy]="feedback.busy()"
          (saved)="submit($event)"
        />
      }
      <div class="auth-links mt-4">
        <a routerLink="/acceso">Iniciar sesión</a>
        @if (session.config().public_signup_enabled) {
          <a routerLink="/registro">Crear cuenta</a><a routerLink="/olvido">Olvidé mi contraseña</a
          ><a routerLink="/reenviar">Reenviar verificación</a>
        }
      </div>
    </div>
  </section>`,
})
export class AuthPage implements OnInit {
  route = inject(ActivatedRoute);
  router = inject(Router);
  api = inject(Api);
  feedback = inject(Feedback);
  session = inject(Session);
  mode = 'login';
  title = '';
  description = '';
  button = 'Continuar';
  fields: Field[] = [];
  closed = false;
  ngOnInit() {
    this.mode = this.route.snapshot.data['mode'];
    this.closed =
      ['register', 'forgot', 'resend', 'reset'].includes(this.mode) &&
      !this.session.config().public_signup_enabled;
    const email: Field = {
      key: 'correo',
      label: 'Correo electrónico',
      type: 'email',
      required: true,
      max: 254,
    };
    const password: Field = {
      key: 'clave',
      label: 'Contraseña',
      type: 'password',
      required: true,
      min: this.mode === 'login' ? 1 : 12,
      max: 128,
    };
    const confirm: Field = {
      key: 'confirmacion',
      label: 'Confirmar contraseña',
      type: 'password',
      required: true,
      min: 12,
      max: 128,
    };
    const config: Record<
      string,
      { title: string; description: string; button: string; fields: Field[] }
    > = {
      login: {
        title: 'Qué bueno tenerte aquí',
        description: 'Inicia sesión y sigue construyendo un impacto positivo.',
        button: 'Iniciar sesión',
        fields: [email, password],
      },
      register: {
        title: 'Empieza a dejar huella',
        description:
          'Usa una contraseña de al menos 12 caracteres. Te enviaremos un enlace para verificar tu correo.',
        button: 'Crear mi cuenta',
        fields: [email, password, confirm],
      },
      forgot: {
        title: 'Recupera tu cuenta',
        description: 'Si el correo corresponde a una cuenta activa, recibirás un enlace privado.',
        button: 'Enviar enlace',
        fields: [email],
      },
      resend: {
        title: 'Verifica tu correo',
        description: 'Solicita un nuevo enlace. El anterior dejará de ser válido.',
        button: 'Reenviar enlace',
        fields: [email],
      },
      verify: {
        title: 'Confirma tu correo',
        description:
          'Confirma para activar tu participación. El enlace es privado y de un solo uso.',
        button: 'Verificar correo',
        fields: [],
      },
      reset: {
        title: 'Elige una nueva contraseña',
        description: 'Las sesiones anteriores se cerrarán al guardar.',
        button: 'Actualizar contraseña',
        fields: [password, confirm],
      },
    };
    Object.assign(this, config[this.mode]);
  }
  async submit(value: FormValue) {
    await this.feedback.run(async () => {
      let body: unknown = value;
      if (['verify', 'reset'].includes(this.mode))
        body = { ...value, token: this.route.snapshot.queryParamMap.get('token') ?? '' };
      const result = await this.api.post<{ mensaje: string }>('/auth/' + this.mode, body);
      if (this.mode === 'login') {
        await this.session.refresh();
        await this.router.navigateByUrl('/panel');
      } else this.feedback.success.set(result.mensaje);
    });
  }
}
