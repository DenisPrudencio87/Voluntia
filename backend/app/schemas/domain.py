from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import EmailStr, Field, field_validator, model_validator
from backend.app.schemas.auth import Input


class Skill(Input):
    id_habilidad: int = Field(gt=0)
    nivel: Literal['basico','intermedio','avanzado']='basico'


class RequiredSkill(Input):
    id_habilidad: int = Field(gt=0)
    nivel_requerido: Literal['basico','intermedio','avanzado']='basico'
    obligatoria: bool=True


def https_optional(value):
    if value is not None and (not value.startswith('https://') or len(value)>2048):
        raise ValueError('Usa una URL HTTPS válida')
    return value


class Location(Input):
    nombre_lugar: str = Field(min_length=2,max_length=160)
    direccion: str = Field(min_length=3,max_length=300)
    latitud: Decimal|None = Field(default=None,ge=-90,le=90)
    longitud: Decimal|None = Field(default=None,ge=-180,le=180)


class Profile(Input):
    nombres: str = Field(min_length=2,max_length=100)
    apellidos: str = Field(min_length=2,max_length=100)
    telefono: str|None = Field(default=None,max_length=30)
    fecha_nacimiento: date|None=None
    biografia: str|None = Field(default=None,max_length=2000)
    foto_url: str|None=None
    ubicacion: Location|None=None
    habilidades: list[Skill] = Field(default_factory=list,max_length=30)
    _https=field_validator('foto_url')(https_optional)

    @field_validator('fecha_nacimiento')
    @classmethod
    def past_birth(cls,v):
        if v and v>=date.today():
            raise ValueError('La fecha de nacimiento debe ser anterior a hoy')
        return v


class Organization(Input):
    nombre: str = Field(min_length=3,max_length=160)
    descripcion: str = Field(min_length=10,max_length=4000)
    correo_contacto: EmailStr
    telefono: str|None = Field(default=None,max_length=30)
    sitio_web: str|None=None
    logo_url: str|None=None
    ubicacion: Location|None=None
    _https=field_validator('sitio_web','logo_url')(https_optional)


class Membership(Input):
    correo: EmailStr
    cargo: Literal['administrador','coordinador']
    estado: Literal['activo','inactivo']='activo'


class Activity(Input):
    id_categoria: int = Field(gt=0)
    titulo: str = Field(min_length=5,max_length=160)
    descripcion: str = Field(min_length=20,max_length=6000)
    fecha_inicio: datetime
    fecha_fin: datetime
    fecha_cierre_inscripcion: datetime
    cupo_maximo: int = Field(gt=0,le=100000)
    modalidad: Literal['presencial','virtual','hibrida']
    imagen_portada_url: str|None=None
    ubicacion: Location|None=None
    habilidades: list[RequiredSkill] = Field(default_factory=list,max_length=30)
    _https=field_validator('imagen_portada_url')(https_optional)

    @model_validator(mode='after')
    def valid_dates(self):
        dates=(self.fecha_inicio,self.fecha_fin,self.fecha_cierre_inscripcion)
        if any(v.tzinfo is None for v in dates):
            raise ValueError('Las fechas requieren zona horaria')
        if not self.fecha_cierre_inscripcion<=self.fecha_inicio<self.fecha_fin:
            raise ValueError('Debe cumplirse cierre ≤ inicio < fin')
        if self.modalidad!='virtual' and not self.ubicacion:
            raise ValueError('Esta modalidad requiere ubicación')
        return self


class Reason(Input):
    motivo: str = Field(min_length=5,max_length=1000)


class ActivityState(Input):
    estado: Literal['publicada','cerrada','en_curso','finalizada','cancelada']
    motivo: str = Field(default='',max_length=1000)


class Application(Input):
    motivacion: str = Field(min_length=10,max_length=2000)


class ApplicationState(Input):
    estado: Literal['aceptada','rechazada','espera','cancelada']
    observacion: str = Field(default='',max_length=2000)


class Attendance(Input):
    estado: Literal['asistio','no_asistio','justificado']
    hora_entrada: datetime|None=None
    hora_salida: datetime|None=None
    observacion: str = Field(default='',max_length=2000)

    @model_validator(mode='after')
    def valid_times(self):
        if (self.hora_entrada is None)!=(self.hora_salida is None):
            raise ValueError('Indica entrada y salida juntas')
        if self.hora_entrada and (not self.hora_entrada.tzinfo or not self.hora_salida.tzinfo or self.hora_salida<self.hora_entrada):
            raise ValueError('Intervalo de asistencia inválido')
        if self.estado!='asistio' and self.hora_entrada:
            raise ValueError('Solo una asistencia efectiva tiene horas')
        return self


class Impact(Input):
    beneficiarios_estimados: int = Field(ge=0,le=10000000)
    descripcion_impacto: str = Field(min_length=10,max_length=4000)


class Review(Reason):
    estado: Literal['aprobado','rechazado']


class OrganizationState(Reason):
    estado: Literal['verificada','rechazada','suspendida','pendiente']


class UserState(Reason):
    estado: Literal['activo','suspendido']


class Roles(Reason):
    roles: list[Literal['administrador','voluntario','organizacion']] = Field(min_length=1,max_length=3)


class Catalog(Input):
    nombre: str = Field(min_length=2,max_length=100)
    descripcion: str = Field(default='',max_length=500)
    activo: bool=True


class CertificateConsent(Input):
    acepta_visibilidad_publica: Literal[True]
