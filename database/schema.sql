-- Consumido exclusivamente por Alembic. 23 tablas de producto.
CREATE SCHEMA voluntia;
REVOKE ALL ON SCHEMA voluntia FROM PUBLIC;
SET search_path TO voluntia, public;
CREATE TABLE usuario (
 id_usuario bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 correo varchar(254) NOT NULL UNIQUE CHECK (correo = lower(trim(correo))),
 clave_hash text NOT NULL, email_verificado boolean NOT NULL DEFAULT false,
 estado varchar(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','suspendido')),
 fecha_registro timestamptz NOT NULL DEFAULT now(), ultimo_acceso timestamptz,
 fecha_actualizacion timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE rol (
 id_rol bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 nombre varchar(30) NOT NULL UNIQUE CHECK(nombre IN ('administrador','voluntario','organizacion')), descripcion varchar(300)
);
CREATE TABLE usuario_rol (
 id_usuario bigint REFERENCES usuario NOT NULL, id_rol bigint REFERENCES rol NOT NULL,
 fecha_asignacion timestamptz NOT NULL DEFAULT now(), activo boolean NOT NULL DEFAULT true,
 PRIMARY KEY(id_usuario,id_rol)
);
CREATE TABLE token_cuenta (
 id_token bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_usuario bigint REFERENCES usuario NOT NULL,
 tipo varchar(30) NOT NULL CHECK(tipo IN ('verificar_email','recuperar_password')),
 token_hash varchar(64) NOT NULL UNIQUE, fecha_creacion timestamptz NOT NULL DEFAULT now(),
 fecha_expiracion timestamptz NOT NULL, fecha_uso timestamptz,
 CHECK(fecha_expiracion > fecha_creacion)
);
CREATE TABLE ubicacion (
 id_ubicacion bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 nombre_lugar varchar(160) NOT NULL, direccion varchar(300) NOT NULL,
 latitud numeric(9,6) CHECK(latitud BETWEEN -90 AND 90),
 longitud numeric(9,6) CHECK(longitud BETWEEN -180 AND 180)
);
CREATE TABLE voluntario (
 id_voluntario bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_usuario bigint NOT NULL UNIQUE REFERENCES usuario,
 nombres varchar(100) NOT NULL, apellidos varchar(100) NOT NULL, telefono varchar(30), fecha_nacimiento date,
 biografia varchar(2000), foto_url text, id_ubicacion bigint REFERENCES ubicacion,
 fecha_actualizacion timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organizacion (
 id_organizacion bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, nombre varchar(160) NOT NULL,
 descripcion varchar(4000) NOT NULL, telefono varchar(30), correo_contacto varchar(254) NOT NULL,
 sitio_web text, logo_url text, id_ubicacion bigint REFERENCES ubicacion,
 estado_verificacion varchar(20) NOT NULL DEFAULT 'pendiente' CHECK(estado_verificacion IN ('pendiente','verificada','rechazada','suspendida')),
 fecha_registro timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organizacion_miembro (
 id_organizacion bigint REFERENCES organizacion NOT NULL, id_usuario bigint REFERENCES usuario NOT NULL,
 cargo varchar(20) NOT NULL CHECK(cargo IN ('administrador','coordinador')),
 estado varchar(20) NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo','inactivo')),
 fecha_ingreso timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id_organizacion,id_usuario)
);
CREATE TABLE documento_organizacion (
 id_documento bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_organizacion bigint REFERENCES organizacion NOT NULL,
 tipo_documento varchar(80) NOT NULL, numero_documento varchar(80) NOT NULL, archivo_url text NOT NULL,
 estado_revision varchar(20) NOT NULL DEFAULT 'pendiente' CHECK(estado_revision IN ('pendiente','aprobado','rechazado')),
 fecha_subida timestamptz NOT NULL DEFAULT now(), fecha_revision timestamptz
);
CREATE TABLE categoria (
 id_categoria bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, nombre varchar(100) UNIQUE NOT NULL,
 descripcion varchar(500), icono varchar(60), activo boolean NOT NULL DEFAULT true
);
CREATE TABLE habilidad (
 id_habilidad bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, nombre varchar(100) UNIQUE NOT NULL,
 descripcion varchar(500), activo boolean NOT NULL DEFAULT true
);
CREATE TABLE voluntario_habilidad (
 id_voluntario bigint REFERENCES voluntario NOT NULL, id_habilidad bigint REFERENCES habilidad NOT NULL,
 nivel varchar(20) NOT NULL CHECK(nivel IN ('basico','intermedio','avanzado')), verificada boolean NOT NULL DEFAULT false,
 PRIMARY KEY(id_voluntario,id_habilidad)
);
CREATE TABLE actividad (
 id_actividad bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_organizacion bigint REFERENCES organizacion NOT NULL,
 id_categoria bigint REFERENCES categoria NOT NULL, id_ubicacion bigint REFERENCES ubicacion,
 titulo varchar(160) NOT NULL, descripcion varchar(6000) NOT NULL, fecha_publicacion timestamptz,
 fecha_inicio timestamptz NOT NULL, fecha_fin timestamptz NOT NULL, fecha_cierre_inscripcion timestamptz NOT NULL,
 cupo_maximo integer NOT NULL CHECK(cupo_maximo > 0),
 modalidad varchar(20) NOT NULL CHECK(modalidad IN ('presencial','virtual','hibrida')),
 estado varchar(20) NOT NULL DEFAULT 'borrador' CHECK(estado IN ('borrador','publicada','cerrada','en_curso','finalizada','cancelada')),
 imagen_portada_url text, fecha_actualizacion timestamptz NOT NULL DEFAULT now(),
 CHECK(fecha_cierre_inscripcion <= fecha_inicio AND fecha_inicio < fecha_fin),
 CHECK(modalidad = 'virtual' OR id_ubicacion IS NOT NULL)
);
CREATE TABLE actividad_habilidad (
 id_actividad bigint REFERENCES actividad NOT NULL, id_habilidad bigint REFERENCES habilidad NOT NULL,
 nivel_requerido varchar(20) NOT NULL CHECK(nivel_requerido IN ('basico','intermedio','avanzado')),
 obligatoria boolean NOT NULL DEFAULT true, PRIMARY KEY(id_actividad,id_habilidad)
);
CREATE TABLE estado_inscripcion (
 id_estado bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, nombre varchar(20) NOT NULL UNIQUE
 CHECK(nombre IN ('pendiente','aceptada','rechazada','cancelada','espera','finalizada')), descripcion varchar(300)
);
CREATE TABLE inscripcion (
 id_inscripcion bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_actividad bigint REFERENCES actividad NOT NULL,
 id_voluntario bigint REFERENCES voluntario NOT NULL, id_estado bigint REFERENCES estado_inscripcion NOT NULL,
 fecha_inscripcion timestamptz NOT NULL DEFAULT now(), motivacion varchar(2000) NOT NULL, observacion varchar(2000),
 fecha_actualizacion timestamptz NOT NULL DEFAULT now(), UNIQUE(id_actividad,id_voluntario)
);
CREATE TABLE historial_inscripcion (
 id_historial bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_inscripcion bigint REFERENCES inscripcion NOT NULL,
 id_estado bigint REFERENCES estado_inscripcion NOT NULL, id_usuario_responsable bigint REFERENCES usuario NOT NULL,
 fecha_cambio timestamptz NOT NULL DEFAULT now(), comentario varchar(2000)
);
CREATE TABLE asistencia (
 id_asistencia bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_inscripcion bigint REFERENCES inscripcion NOT NULL UNIQUE,
 estado varchar(20) NOT NULL CHECK(estado IN ('asistio','no_asistio','justificado')),
 hora_entrada timestamptz, hora_salida timestamptz, observacion varchar(2000),
 CHECK((hora_entrada IS NULL AND hora_salida IS NULL) OR (hora_entrada IS NOT NULL AND hora_salida IS NOT NULL AND hora_salida >= hora_entrada)),
 CHECK(estado = 'asistio' OR hora_entrada IS NULL)
);
CREATE TABLE impacto_actividad (
 id_impacto bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_actividad bigint REFERENCES actividad NOT NULL UNIQUE,
 beneficiarios_estimados integer NOT NULL CHECK(beneficiarios_estimados >= 0),
 horas_voluntariado numeric(12,2) NOT NULL DEFAULT 0 CHECK(horas_voluntariado >= 0),
 descripcion_impacto varchar(4000) NOT NULL, fecha_registro timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE evidencia_actividad (
 id_evidencia bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_actividad bigint REFERENCES actividad NOT NULL,
 id_usuario bigint REFERENCES usuario NOT NULL, tipo varchar(20) NOT NULL CHECK(tipo IN ('imagen','pdf','video')),
 archivo_url text NOT NULL, descripcion varchar(1000) NOT NULL, fecha_subida timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE certificado (
 id_certificado bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_inscripcion bigint REFERENCES inscripcion NOT NULL UNIQUE,
 codigo_verificacion varchar(64) NOT NULL UNIQUE, horas_certificadas numeric(10,2) NOT NULL CHECK(horas_certificadas > 0),
 fecha_emision timestamptz NOT NULL DEFAULT now(), archivo_url text NOT NULL
);
CREATE TABLE notificacion (
 id_notificacion bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_usuario bigint REFERENCES usuario NOT NULL,
 titulo varchar(160) NOT NULL, mensaje varchar(2000) NOT NULL, tipo varchar(40) NOT NULL,
 url_destino varchar(300) NOT NULL CHECK(url_destino ~ '^/[^/]' AND url_destino !~ '[\\:]'),
 leida boolean NOT NULL DEFAULT false, fecha_creacion timestamptz NOT NULL DEFAULT now(), fecha_lectura timestamptz,
 CHECK(leida = (fecha_lectura IS NOT NULL))
);
CREATE TABLE bitacora_evento (
 id_evento bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, id_usuario bigint REFERENCES usuario,
 accion varchar(80) NOT NULL, entidad varchar(80) NOT NULL, id_registro bigint,
 fecha_evento timestamptz NOT NULL DEFAULT now(), direccion_ip_hash varchar(64), detalle varchar(2000)
);
-- Un índice por FK (también útil para joins y eliminación referencial).
DO $$ DECLARE r record; BEGIN
 FOR r IN SELECT tc.table_name,kcu.column_name FROM information_schema.table_constraints tc
 JOIN information_schema.key_column_usage kcu USING(constraint_catalog,constraint_schema,constraint_name)
 WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='voluntia'
 LOOP EXECUTE format('CREATE INDEX ON voluntia.%I (%I)',r.table_name,r.column_name); END LOOP;
END $$;
CREATE INDEX actividad_catalogo ON actividad(estado,fecha_inicio,id_categoria);
CREATE INDEX notificacion_usuario ON notificacion(id_usuario,leida,fecha_creacion);
