export interface User {
  id_usuario: number;
  correo: string;
  email_verificado: boolean;
  estado: string;
  roles: string[];
}
export interface CatalogItem {
  id_categoria?: number;
  id_habilidad?: number;
  nombre: string;
  descripcion: string;
  activo: boolean;
}
export interface Catalogs {
  categorias: CatalogItem[];
  habilidades: CatalogItem[];
}
export interface Skill {
  id_habilidad: number;
  nivel?: string;
  nivel_requerido?: string;
  obligatoria?: boolean;
  nombre?: string;
}
export interface Location {
  nombre_lugar: string;
  direccion: string;
}
export interface Activity {
  id_actividad: number;
  id_organizacion: number;
  id_categoria: number;
  titulo: string;
  descripcion: string;
  organizacion?: string;
  categoria?: string;
  modalidad: string;
  estado: string;
  fecha_inicio: string;
  fecha_fin: string;
  fecha_cierre_inscripcion: string;
  cupo_maximo: number;
  cupos_disponibles?: number;
  imagen_portada_url?: string;
  nombre_lugar?: string;
  direccion?: string;
  ubicacion?: Location;
  habilidades?: Skill[];
  impacto?: Impact;
}
export interface Organization {
  id_organizacion: number;
  nombre: string;
  descripcion: string;
  correo_contacto: string;
  telefono?: string;
  sitio_web?: string;
  logo_url?: string;
  estado_verificacion: string;
  cargo?: string;
  ubicacion?: Location;
  estadisticas?: Record<string, number>;
  revisiones?: { accion: string; detalle: string; fecha_evento: string }[];
}
export interface Application {
  id_inscripcion: number;
  id_actividad: number;
  id_voluntario: number;
  estado: string;
  titulo?: string;
  nombres?: string;
  apellidos?: string;
  motivacion: string;
  observacion?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  estado_actividad?: string;
  id_certificado?: number;
  codigo_verificacion?: string;
  horas_certificadas?: number;
  asistencia?: string;
  hora_entrada?: string;
  hora_salida?: string;
}
export interface Profile {
  nombres: string;
  apellidos: string;
  telefono?: string;
  biografia?: string;
  foto_url?: string;
  fecha_nacimiento?: string;
  habilidades: Skill[];
  horas: number;
  ubicacion?: Location;
}
export interface Document {
  id_documento: number;
  tipo_documento: string;
  numero_documento: string;
  estado_revision: string;
}
export interface Notice {
  id_notificacion: number;
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
}
export interface Impact {
  beneficiarios_estimados: number;
  horas_voluntariado: number;
  descripcion_impacto: string;
}
export interface Certificate {
  nombres: string;
  apellidos: string;
  actividad: string;
  organizacion: string;
  horas_certificadas: number;
  codigo_verificacion: string;
  fecha_emision: string;
}
export interface History {
  estado: string;
  fecha_cambio: string;
  comentario: string;
}
export interface Evidence {
  id_evidencia: number;
  tipo: string;
  descripcion: string;
}
export interface Member {
  id_usuario: number;
  correo: string;
  cargo: string;
  estado: string;
}
export interface Audit {
  id_evento: number;
  accion: string;
  entidad: string;
  detalle: string;
  fecha_evento: string;
}
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
