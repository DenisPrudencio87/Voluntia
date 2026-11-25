import { Field, FormValue } from './record-form';
export const organizationFields: Field[] = [
  { key: 'nombre', label: 'Nombre de la organización', required: true, min: 3, max: 160 },
  { key: 'correo_contacto', label: 'Correo de contacto', type: 'email', required: true },
  {
    key: 'descripcion',
    label: 'Qué hacemos',
    type: 'textarea',
    required: true,
    min: 10,
    max: 4000,
  },
  { key: 'telefono', label: 'Teléfono', max: 30 },
  { key: 'sitio_web', label: 'Sitio web (HTTPS)' },
  { key: 'logo_url', label: 'URL del logo (HTTPS)' },
  { key: 'lugar', label: 'Lugar o ciudad' },
  { key: 'direccion', label: 'Dirección' },
];
export function optional(values: FormValue, keys: string[]) {
  return { ...values, ...Object.fromEntries(keys.map((k) => [k, values[k] || null])) };
}
export function withLocation(values: FormValue) {
  const { lugar, direccion, ...rest } = values;
  return { ...rest, ubicacion: lugar && direccion ? { nombre_lugar: lugar, direccion } : null };
}
export function localDate(value: string | undefined) {
  if (!value) return '';
  const d = new Date(value);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
export function reason(message: string) {
  const value = window.prompt(message + '\nMotivo (al menos 5 caracteres):')?.trim();
  if (!value || value.length < 5) return null;
  return window.confirm('¿Confirmas esta acción?\n' + value) ? value : null;
}
