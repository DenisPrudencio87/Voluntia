import { Pipe, PipeTransform } from '@angular/core';
export const LABELS: Record<string, string> = {
  borrador: 'Borrador',
  publicada: 'Publicada',
  cerrada: 'Inscripciones cerradas',
  en_curso: 'En curso',
  finalizada: 'Finalizada',
  cancelada: 'Cancelada',
  pendiente: 'Pendiente',
  aceptada: 'Aceptada',
  rechazada: 'Rechazada',
  espera: 'Lista de espera',
  verificada: 'Verificada',
  suspendida: 'Suspendida',
  activo: 'Activo',
  suspendido: 'Suspendido',
  inactivo: 'Inactivo',
  administrador: 'Administrador',
  coordinador: 'Coordinador',
  voluntario: 'Voluntario',
  organizacion: 'Organización',
  presencial: 'Presencial',
  virtual: 'Virtual',
  hibrida: 'Híbrida',
  basico: 'Básico',
  intermedio: 'Intermedio',
  avanzado: 'Avanzado',
  asistio: 'Asistió',
  no_asistio: 'No asistió',
  justificado: 'Justificado',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
};
@Pipe({ name: 'label' })
export class LabelPipe implements PipeTransform {
  transform(value: string | null | undefined) {
    return value ? (LABELS[value] ?? value) : '—';
  }
}
