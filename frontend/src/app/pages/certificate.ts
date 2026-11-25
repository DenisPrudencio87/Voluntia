import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { RecordForm, Field, FormValue } from '../components/record-form';
import { Api, Feedback } from '../services/api';
import { Certificate } from '../models/domain';
@Component({
  imports: [RecordForm, DatePipe],
  template: `<section class="container section activity-detail">
    <div class="eyebrow">Participación que deja huella</div>
    <h1 class="mt-2">Verificar un certificado</h1>
    <p class="text-secondary">Introduce el código del documento para comprobar su autenticidad.</p>
    <div class="surface">
      <app-record-form
        [fields]="fields"
        [initial]="initial"
        label="Verificar certificado"
        [busy]="feedback.busy()"
        (saved)="verify($event)"
      />
    </div>
    @if (certificate(); as c) {
      <div class="surface">
        <span class="pill mb-3"><i class="bi bi-check-circle"></i> Certificado válido</span>
        <h2>{{ c.nombres }} {{ c.apellidos }}</h2>
        <p>{{ c.actividad }} · {{ c.organizacion }}</p>
        <p>
          {{ c.horas_certificadas }} horas · Emitido el {{ c.fecha_emision | date: 'dd/MM/yyyy' }}
        </p>
        <div class="small text-secondary text-break">Código: {{ c.codigo_verificacion }}</div>
      </div>
    }
  </section>`,
})
export class CertificatePage {
  api = inject(Api);
  feedback = inject(Feedback);
  route = inject(ActivatedRoute);
  certificate = signal<Certificate | null>(null);
  initial = { code: this.route.snapshot.queryParamMap.get('code') ?? '' };
  fields: Field[] = [
    { key: 'code', label: 'Código de verificación', required: true, min: 20, max: 64 },
  ];
  async verify(value: FormValue) {
    this.certificate.set(null);
    await this.feedback.run(async () =>
      this.certificate.set(
        await this.api.get<Certificate>(
          '/certificates/' + encodeURIComponent(String(value['code'])),
        ),
      ),
    );
  }
}
