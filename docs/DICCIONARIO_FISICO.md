# Diccionario físico generado

Fuente: PostgreSQL local migrado mediante Alembic. 23 tablas, 29 FK.

| Tabla | Columna | Tipo | Nullable | Default |
|---|---|---|---|---|
|actividad|id_actividad|bigint|NO||
|actividad|id_organizacion|bigint|NO||
|actividad|id_categoria|bigint|NO||
|actividad|id_ubicacion|bigint|YES||
|actividad|titulo|character varying|NO||
|actividad|descripcion|character varying|NO||
|actividad|fecha_publicacion|timestamp with time zone|YES||
|actividad|fecha_inicio|timestamp with time zone|NO||
|actividad|fecha_fin|timestamp with time zone|NO||
|actividad|fecha_cierre_inscripcion|timestamp with time zone|NO||
|actividad|cupo_maximo|integer|NO||
|actividad|modalidad|character varying|NO||
|actividad|estado|character varying|NO|'borrador'::character varying|
|actividad|imagen_portada_url|text|YES||
|actividad|fecha_actualizacion|timestamp with time zone|NO|now()|
|actividad_habilidad|id_actividad|bigint|NO||
|actividad_habilidad|id_habilidad|bigint|NO||
|actividad_habilidad|nivel_requerido|character varying|NO||
|actividad_habilidad|obligatoria|boolean|NO|true|
|asistencia|id_asistencia|bigint|NO||
|asistencia|id_inscripcion|bigint|NO||
|asistencia|estado|character varying|NO||
|asistencia|hora_entrada|timestamp with time zone|YES||
|asistencia|hora_salida|timestamp with time zone|YES||
|asistencia|observacion|character varying|YES||
|bitacora_evento|id_evento|bigint|NO||
|bitacora_evento|id_usuario|bigint|YES||
|bitacora_evento|accion|character varying|NO||
|bitacora_evento|entidad|character varying|NO||
|bitacora_evento|id_registro|bigint|YES||
|bitacora_evento|fecha_evento|timestamp with time zone|NO|now()|
|bitacora_evento|direccion_ip_hash|character varying|YES||
|bitacora_evento|detalle|character varying|YES||
|categoria|id_categoria|bigint|NO||
|categoria|nombre|character varying|NO||
|categoria|descripcion|character varying|YES||
|categoria|icono|character varying|YES||
|categoria|activo|boolean|NO|true|
|certificado|id_certificado|bigint|NO||
|certificado|id_inscripcion|bigint|NO||
|certificado|codigo_verificacion|character varying|NO||
|certificado|horas_certificadas|numeric|NO||
|certificado|fecha_emision|timestamp with time zone|NO|now()|
|certificado|archivo_url|text|NO||
|documento_organizacion|id_documento|bigint|NO||
|documento_organizacion|id_organizacion|bigint|NO||
|documento_organizacion|tipo_documento|character varying|NO||
|documento_organizacion|numero_documento|character varying|NO||
|documento_organizacion|archivo_url|text|NO||
|documento_organizacion|estado_revision|character varying|NO|'pendiente'::character varying|
|documento_organizacion|fecha_subida|timestamp with time zone|NO|now()|
|documento_organizacion|fecha_revision|timestamp with time zone|YES||
|estado_inscripcion|id_estado|bigint|NO||
|estado_inscripcion|nombre|character varying|NO||
|estado_inscripcion|descripcion|character varying|YES||
|evidencia_actividad|id_evidencia|bigint|NO||
|evidencia_actividad|id_actividad|bigint|NO||
|evidencia_actividad|id_usuario|bigint|NO||
|evidencia_actividad|tipo|character varying|NO||
|evidencia_actividad|archivo_url|text|NO||
|evidencia_actividad|descripcion|character varying|NO||
|evidencia_actividad|fecha_subida|timestamp with time zone|NO|now()|
|habilidad|id_habilidad|bigint|NO||
|habilidad|nombre|character varying|NO||
|habilidad|descripcion|character varying|YES||
|habilidad|activo|boolean|NO|true|
|historial_inscripcion|id_historial|bigint|NO||
|historial_inscripcion|id_inscripcion|bigint|NO||
|historial_inscripcion|id_estado|bigint|NO||
|historial_inscripcion|id_usuario_responsable|bigint|NO||
|historial_inscripcion|fecha_cambio|timestamp with time zone|NO|now()|
|historial_inscripcion|comentario|character varying|YES||
|impacto_actividad|id_impacto|bigint|NO||
|impacto_actividad|id_actividad|bigint|NO||
|impacto_actividad|beneficiarios_estimados|integer|NO||
|impacto_actividad|horas_voluntariado|numeric|NO|0|
|impacto_actividad|descripcion_impacto|character varying|NO||
|impacto_actividad|fecha_registro|timestamp with time zone|NO|now()|
|inscripcion|id_inscripcion|bigint|NO||
|inscripcion|id_actividad|bigint|NO||
|inscripcion|id_voluntario|bigint|NO||
|inscripcion|id_estado|bigint|NO||
|inscripcion|fecha_inscripcion|timestamp with time zone|NO|now()|
|inscripcion|motivacion|character varying|NO||
|inscripcion|observacion|character varying|YES||
|inscripcion|fecha_actualizacion|timestamp with time zone|NO|now()|
|notificacion|id_notificacion|bigint|NO||
|notificacion|id_usuario|bigint|NO||
|notificacion|titulo|character varying|NO||
|notificacion|mensaje|character varying|NO||
|notificacion|tipo|character varying|NO||
|notificacion|url_destino|character varying|NO||
|notificacion|leida|boolean|NO|false|
|notificacion|fecha_creacion|timestamp with time zone|NO|now()|
|notificacion|fecha_lectura|timestamp with time zone|YES||
|organizacion|id_organizacion|bigint|NO||
|organizacion|nombre|character varying|NO||
|organizacion|descripcion|character varying|NO||
|organizacion|telefono|character varying|YES||
|organizacion|correo_contacto|character varying|NO||
|organizacion|sitio_web|text|YES||
|organizacion|logo_url|text|YES||
|organizacion|id_ubicacion|bigint|YES||
|organizacion|estado_verificacion|character varying|NO|'pendiente'::character varying|
|organizacion|fecha_registro|timestamp with time zone|NO|now()|
|organizacion_miembro|id_organizacion|bigint|NO||
|organizacion_miembro|id_usuario|bigint|NO||
|organizacion_miembro|cargo|character varying|NO||
|organizacion_miembro|estado|character varying|NO|'activo'::character varying|
|organizacion_miembro|fecha_ingreso|timestamp with time zone|NO|now()|
|rol|id_rol|bigint|NO||
|rol|nombre|character varying|NO||
|rol|descripcion|character varying|YES||
|token_cuenta|id_token|bigint|NO||
|token_cuenta|id_usuario|bigint|NO||
|token_cuenta|tipo|character varying|NO||
|token_cuenta|token_hash|character varying|NO||
|token_cuenta|fecha_creacion|timestamp with time zone|NO|now()|
|token_cuenta|fecha_expiracion|timestamp with time zone|NO||
|token_cuenta|fecha_uso|timestamp with time zone|YES||
|ubicacion|id_ubicacion|bigint|NO||
|ubicacion|nombre_lugar|character varying|NO||
|ubicacion|direccion|character varying|NO||
|ubicacion|latitud|numeric|YES||
|ubicacion|longitud|numeric|YES||
|usuario|id_usuario|bigint|NO||
|usuario|correo|character varying|NO||
|usuario|clave_hash|text|NO||
|usuario|email_verificado|boolean|NO|false|
|usuario|estado|character varying|NO|'activo'::character varying|
|usuario|fecha_registro|timestamp with time zone|NO|now()|
|usuario|ultimo_acceso|timestamp with time zone|YES||
|usuario|fecha_actualizacion|timestamp with time zone|NO|now()|
|usuario_rol|id_usuario|bigint|NO||
|usuario_rol|id_rol|bigint|NO||
|usuario_rol|fecha_asignacion|timestamp with time zone|NO|now()|
|usuario_rol|activo|boolean|NO|true|
|voluntario|id_voluntario|bigint|NO||
|voluntario|id_usuario|bigint|NO||
|voluntario|nombres|character varying|NO||
|voluntario|apellidos|character varying|NO||
|voluntario|telefono|character varying|YES||
|voluntario|fecha_nacimiento|date|YES||
|voluntario|biografia|character varying|YES||
|voluntario|foto_url|text|YES||
|voluntario|id_ubicacion|bigint|YES||
|voluntario|fecha_actualizacion|timestamp with time zone|NO|now()|
|voluntario_habilidad|id_voluntario|bigint|NO||
|voluntario_habilidad|id_habilidad|bigint|NO||
|voluntario_habilidad|nivel|character varying|NO||
|voluntario_habilidad|verificada|boolean|NO|false|

## Claves candidatas y dependencias funcionales

En cada tabla, cada clave candidata siguiente determina todos sus atributos. Las claves compuestas de tablas puente determinan únicamente atributos de esa relación; las FK determinan entidades externas sin copiar sus nombres. No existen listas ni grupos repetitivos (1FN), dependencias parciales (2FN) ni atributos descriptivos de otra entidad (3FN).

|Tabla|Tipo|Clave candidata|
|---|---|---|
|actividad|PRIMARY KEY|id_actividad|
|actividad_habilidad|PRIMARY KEY|id_actividad, id_habilidad|
|asistencia|UNIQUE|id_inscripcion|
|asistencia|PRIMARY KEY|id_asistencia|
|bitacora_evento|PRIMARY KEY|id_evento|
|categoria|UNIQUE|nombre|
|categoria|PRIMARY KEY|id_categoria|
|certificado|UNIQUE|codigo_verificacion|
|certificado|UNIQUE|id_inscripcion|
|certificado|PRIMARY KEY|id_certificado|
|documento_organizacion|PRIMARY KEY|id_documento|
|estado_inscripcion|UNIQUE|nombre|
|estado_inscripcion|PRIMARY KEY|id_estado|
|evidencia_actividad|PRIMARY KEY|id_evidencia|
|habilidad|UNIQUE|nombre|
|habilidad|PRIMARY KEY|id_habilidad|
|historial_inscripcion|PRIMARY KEY|id_historial|
|impacto_actividad|UNIQUE|id_actividad|
|impacto_actividad|PRIMARY KEY|id_impacto|
|inscripcion|UNIQUE|id_actividad, id_voluntario|
|inscripcion|PRIMARY KEY|id_inscripcion|
|notificacion|PRIMARY KEY|id_notificacion|
|organizacion|PRIMARY KEY|id_organizacion|
|organizacion_miembro|PRIMARY KEY|id_organizacion, id_usuario|
|rol|UNIQUE|nombre|
|rol|PRIMARY KEY|id_rol|
|token_cuenta|PRIMARY KEY|id_token|
|token_cuenta|UNIQUE|token_hash|
|ubicacion|PRIMARY KEY|id_ubicacion|
|usuario|UNIQUE|correo|
|usuario|PRIMARY KEY|id_usuario|
|usuario_rol|PRIMARY KEY|id_usuario, id_rol|
|voluntario|UNIQUE|id_usuario|
|voluntario|PRIMARY KEY|id_voluntario|
|voluntario_habilidad|PRIMARY KEY|id_voluntario, id_habilidad|

`impacto_actividad.horas_voluntariado` es un agregado mantenido por trigger y servicio, sin sumar certificados. Se conserva por su significado documental; no es una fuente independiente. Los certificados guardan la instantánea inmutable de horas emitidas.
