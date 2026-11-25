# Voluntia — modelo relacional definitivo (23 tablas)
Fuente de verdad para la implementación. PostgreSQL, nombres físicos snake_case en minúsculas; nombres lógicos originales abajo. Se posponen FAVORITO, VALORACION, CONVERSACION, CONVERSACION_PARTICIPANTE, MENSAJE y ORGANIZACION_CATEGORIA. Las áreas de la organización se deducen de sus actividades; no se muestran áreas independientes. No crear tablas de producto adicionales sin justificarlo. Alembic puede crear su tabla técnica de versiones, que no cuenta en las 23.

## Diccionario lógico conservado del original
### USUARIO
Representa una cuenta del sistema.

Campos:

- id_usuario — PK
- correo — UNIQUE, NOT NULL
- clave_hash — NOT NULL
- email_verificado
- estado
- fecha_registro
- ultimo_acceso
- fecha_actualizacion

La contraseña nunca debe almacenarse directamente. Se debe almacenar únicamente su hash.

### ROL
Define los diferentes roles disponibles.

Campos:

- id_rol — PK
- nombre — UNIQUE, NOT NULL
- descripcion

Posibles roles:

- Administrador
- Voluntario
- Organización

### USUARIO_ROL
Resuelve la relación muchos a muchos entre USUARIO y ROL.

Campos:

- id_usuario — PK, FK → USUARIO
- id_rol — PK, FK → ROL
- fecha_asignacion
- activo

Clave primaria compuesta:

(id_usuario, id_rol)

Un usuario puede poseer uno o varios roles.

### TOKEN_CUENTA
Gestiona tokens relacionados con funciones de seguridad.

Campos:

- id_token — PK
- id_usuario — FK → USUARIO
- tipo
- token_hash
- fecha_creacion
- fecha_expiracion
- fecha_uso

Posibles tipos:

- VERIFICAR_EMAIL
- RECUPERAR_PASSWORD

### UBICACION
Almacena ubicaciones reutilizables.

Campos:

- id_ubicacion — PK
- nombre_lugar
- direccion
- latitud
- longitud

Puede ser utilizada por voluntarios, organizaciones y actividades.

### VOLUNTARIO
Representa el perfil de una persona voluntaria.

Campos:

- id_voluntario — PK
- id_usuario — FK → USUARIO, UNIQUE
- nombres
- apellidos
- telefono
- fecha_nacimiento
- biografia
- foto_url
- id_ubicacion — FK → UBICACION
- fecha_actualizacion

Cada voluntario está asociado a una cuenta de usuario.

### ORGANIZACION
Representa una organización que publica actividades sociales.

Campos:

- id_organizacion — PK
- nombre
- descripcion
- telefono
- correo_contacto
- sitio_web
- logo_url
- id_ubicacion — FK → UBICACION
- estado_verificacion
- fecha_registro

Una organización puede tener varios miembros administradores.

### ORGANIZACION_MIEMBRO
Relaciona usuarios con organizaciones.

Campos:

- id_organizacion — PK, FK → ORGANIZACION
- id_usuario — PK, FK → USUARIO
- cargo
- estado
- fecha_ingreso

Clave primaria compuesta:

(id_organizacion, id_usuario)

Permite que una organización sea administrada por varias personas.

### DOCUMENTO_ORGANIZACION
Almacena información relacionada con documentos utilizados para verificar una organización.

Campos:

- id_documento — PK
- id_organizacion — FK → ORGANIZACION
- tipo_documento
- numero_documento
- archivo_url
- estado_revision
- fecha_subida
- fecha_revision

Posibles estados:

- Pendiente
- Aprobado
- Rechazado

### CATEGORIA
Clasifica actividades y áreas sociales.

Campos:

- id_categoria — PK
- nombre — UNIQUE
- descripcion
- icono
- activo

Ejemplos:

- Medio ambiente
- Educación
- Salud
- Bienestar animal
- Ayuda humanitaria
- Adultos mayores
- Inclusión social

### HABILIDAD
Catálogo de habilidades relevantes para voluntariado.

Campos:

- id_habilidad — PK
- nombre — UNIQUE
- descripcion
- activo

Ejemplos:

- Primeros auxilios
- Enseñanza
- Logística
- Fotografía
- Programación
- Cocina
- Idiomas

### VOLUNTARIO_HABILIDAD
Relaciona voluntarios con sus habilidades.

Campos:

- id_voluntario — PK, FK → VOLUNTARIO
- id_habilidad — PK, FK → HABILIDAD
- nivel
- verificada

Clave primaria compuesta:

(id_voluntario, id_habilidad)

Un voluntario puede tener varias habilidades y una habilidad puede pertenecer a muchos voluntarios.

### ACTIVIDAD
Representa una actividad o campaña de voluntariado.

Campos:

- id_actividad — PK
- id_organizacion — FK → ORGANIZACION
- id_categoria — FK → CATEGORIA
- id_ubicacion — FK → UBICACION
- titulo
- descripcion
- fecha_publicacion
- fecha_inicio
- fecha_fin
- fecha_cierre_inscripcion
- cupo_maximo
- modalidad
- estado
- imagen_portada_url
- fecha_actualizacion

Posibles modalidades:

- Presencial
- Virtual
- Híbrida

Posibles estados:

- Borrador
- Publicada
- Inscripciones cerradas
- En curso
- Finalizada
- Cancelada

Una organización puede crear muchas actividades.

Una categoría puede contener muchas actividades.

### ACTIVIDAD_HABILIDAD
Define las habilidades solicitadas para una actividad.

Campos:

- id_actividad — PK, FK → ACTIVIDAD
- id_habilidad — PK, FK → HABILIDAD
- nivel_requerido
- obligatoria

Clave primaria compuesta:

(id_actividad, id_habilidad)

Permite posteriormente implementar sistemas de recomendación entre voluntarios y actividades.

### ESTADO_INSCRIPCION
Catálogo de estados posibles de una inscripción.

Campos:

- id_estado — PK
- nombre — UNIQUE
- descripcion

Ejemplos:

- Pendiente
- Aceptada
- Rechazada
- Cancelada
- Lista de espera
- Finalizada

### INSCRIPCION
Representa la inscripción de un voluntario en una actividad.

Campos:

- id_inscripcion — PK
- id_actividad — FK → ACTIVIDAD
- id_voluntario — FK → VOLUNTARIO
- id_estado — FK → ESTADO_INSCRIPCION
- fecha_inscripcion
- motivacion
- observacion
- fecha_actualizacion

Debe existir:

UNIQUE(id_actividad, id_voluntario)

Esto impide que un voluntario se inscriba varias veces en la misma actividad.

### HISTORIAL_INSCRIPCION
Conserva el historial de cambios realizados sobre una inscripción.

Campos:

- id_historial — PK
- id_inscripcion — FK → INSCRIPCION
- id_estado — FK → ESTADO_INSCRIPCION
- id_usuario_responsable — FK → USUARIO
- fecha_cambio
- comentario

Ejemplo:

Pendiente → Aceptada → Cancelada

El historial no debe sobrescribirse.

### ASISTENCIA
Registra la participación efectiva de un voluntario.

Campos:

- id_asistencia — PK
- id_inscripcion — FK → INSCRIPCION, UNIQUE
- estado
- hora_entrada
- hora_salida
- observacion

Posibles estados:

- Asistió
- No asistió
- Justificado

Solo debe existir una asistencia por inscripción.

### IMPACTO_ACTIVIDAD
Almacena los resultados sociales de una actividad.

Campos:

- id_impacto — PK
- id_actividad — FK → ACTIVIDAD, UNIQUE
- beneficiarios_estimados
- horas_voluntariado
- descripcion_impacto
- fecha_registro

Ejemplos de datos:

- personas beneficiadas;
- horas de voluntariado;
- resultados obtenidos;
- impacto generado.

### EVIDENCIA_ACTIVIDAD
Almacena evidencias asociadas a las actividades.

Campos:

- id_evidencia — PK
- id_actividad — FK → ACTIVIDAD
- id_usuario — FK → USUARIO
- tipo
- archivo_url
- descripcion
- fecha_subida

Los archivos físicos no deben guardarse directamente en la BD; se debe almacenar principalmente su URL o referencia.

Puede almacenar referencias a:

- fotografías;
- vídeos;
- PDFs;
- documentos;
- otros archivos.

### CERTIFICADO
Representa un certificado obtenido por participar en una actividad.

Campos:

- id_certificado — PK
- id_inscripcion — FK → INSCRIPCION, UNIQUE
- codigo_verificacion — UNIQUE
- horas_certificadas
- fecha_emision
- archivo_url

Cada certificado debe poder verificarse mediante un código único.

### NOTIFICACION
Gestiona notificaciones internas.

Campos:

- id_notificacion — PK
- id_usuario — FK → USUARIO
- titulo
- mensaje
- tipo
- url_destino
- leida
- fecha_creacion
- fecha_lectura

Ejemplos:

- inscripción aceptada;
- actividad próxima;
- cambio de ubicación;
- certificado disponible;
- actividad cancelada.

### BITACORA_EVENTO
Registra acciones importantes realizadas en el sistema.

Campos:

- id_evento — PK
- id_usuario — FK → USUARIO
- accion
- entidad
- id_registro
- fecha_evento
- direccion_ip_hash
- detalle

Ejemplos:

- creación de actividad;
- modificación de inscripción;
- aprobación de organización;
- cambio de estado;
- operaciones administrativas.

## Especificación física y ajustes explícitos
- PK simples bigint identity; FK bigint; PK compuestas según diccionario. No usar borrado en cascada para historial. Índices en FK y búsquedas frecuentes. Fechas de eventos timestamptz UTC, nacimiento date; latitud/longitud numeric con rango válido; horas numeric no negativas, cupos integer positivos, boolean para indicadores. Texto con límites razonables documentados; URLs como texto, nunca archivos binarios. Campos obligatorios: identificadores, relaciones esenciales, nombres/títulos, correo, hash, estados y fechas de creación; perfil opcional puede omitir teléfono, foto, biografía, ubicación; ubicación opcional para virtual. Registrar nulabilidad campo por campo en migraciones y diccionario físico generado.
- Correo normalizado trim/lower y UNIQUE (restricción o índice funcional); hashes Argon2id. Tokens aleatorios de un solo uso, solo hash, expiración, invalidación tras uso. No almacenar JWT ni contraseñas claras.
- Roles iniciales: Administrador, Voluntario, Organización; se retira Moderador. Un usuario puede tener varios roles activos. Estado usuario activo/suspendido. Cargo de miembro administrador/coordinador; ambos gestionan actividades, solo administrador de organización gestiona miembros y perfil. Miembro activo/inactivo. No retirar último administrador activo.
- Organización pendiente/verificada/rechazada/suspendida; documento pendiente/aprobado/rechazado. Aprobación solo por admin general, con al menos un documento aprobado y ninguno pendiente; rechazo permite reenviar. Archivo privado. Categorías y habilidades activas/inactivas.
- Estados de actividad e inscripción conforme al diccionario. Usar códigos estables sin acentos en SQL y etiquetas españolas en UI; mapear explícitamente. Fechas: cierre <= inicio < fin; cupo > 0; no bajar cupo por debajo de aceptados/finalizados. Modalidad presencial/virtual/híbrida. Habilidades: básico/intermedio/avanzado; las obligatorias deben cumplirse al postular. Guardar motivo de cancelación de actividad y revisión en bitácora.detalle (sin nueva columna); mostrar observaciones de revisión al titular autorizado si corresponde. No implementar denuncias ni ocultamiento independiente; moderación mediante cancelación/suspensión.
- INSCRIPCION única (actividad,voluntario). No borrar ni reinscribir tras cancelación en esta versión. Aceptados ocupan cupo; finalizados conservan su plaza histórica. Pendientes y espera no ocupan cupo. Rechazados/cancelados terminales. Transiciones: pendiente→aceptada/rechazada/espera/cancelada; espera→aceptada/rechazada/cancelada; aceptada→cancelada/finalizada. Cancelación voluntaria antes de inicio; finalización por organización tras fin. Actividad cancelada cancela inscripciones pendientes/espera/aceptadas y notifica en una transacción. No cancelar actividad finalizada. Al finalizar, resolver pendientes/espera como rechazadas y registrar historial. Asistencia solo para participantes aceptados/finalizados, durante o después del evento; entrada/salida opcionales en pareja, salida >= entrada y dentro del intervalo de actividad. Horas calculadas de asistencia efectiva; si no hay horas registradas, no emitir certificado hasta completarlas. Certificado único por inscripción, solo actividad finalizada y asistencia asistió, horas positivas; código aleatorio único. No modificar asistencia certificada sin proceso futuro explícito. Impacto: beneficiarios estimados no negativos, horas agregadas derivadas de asistencias o sincronizadas al registrar impacto y actualizaciones; no sumar certificados además de asistencia.
- Notificación: marcar lectura y fecha juntas. Bitácora append-only, no incluir secretos ni datos sensibles; IP hash opcional con clave de servidor. URL de destino interna validada. Evidencias y certificados guardan referencias a objetos; documentos privados, descarga firmada/autorizada. El administrador general no tiene acceso indiscriminado a datos privados fuera de su función.

## Funciones SQL obligatorias
1. fn_cupos_disponibles(id_actividad): capacidad menos aceptados/finalizados; nunca ocultar inconsistencia con un valor ficticio.
2. fn_aceptar_inscripcion(id_inscripcion,id_usuario_responsable): transacción, bloquear fila ACTIVIDAD con FOR UPDATE antes de contar plazas y cambiar estado; verificar estado, fecha, organización autorizada y miembro activo; registrar historial, bitácora y notificación atómicamente. Si lleno, devolver conflicto sin alterar datos. Todas las rutas que cambien ocupación/cupo deben adquirir el mismo bloqueo en el mismo orden; no permitir aceptación por CRUD genérico. Permisos SQL mínimos, sin ejecución pública; identidad del actor proviene de sesión validada, nunca de un campo libre del cliente.
3. fn_horas_voluntariado(id_voluntario): suma de duración de asistencias efectivas sin duplicados.
4. fn_estadisticas_organizacion(id_organizacion): actividades, inscritos, asistencia, horas y beneficiarios con agregaciones separadas para evitar multiplicación por JOIN.
Trigger de historial de inscripción (creación y cambios de estado) con actor obtenido de contexto transaccional parametrizado por backend; si falta, rechazar escritura normal. Evitar duplicar historial en función de aceptación. Pruebas concurrentes reales PostgreSQL. No usar SQLite como sustituto de pruebas de funciones.

## Normalización y evidencias
1FN: valores atómicos, sin listas de roles/habilidades. 2FN: atributos de tablas puente dependen de ambas FK. 3FN: actividad referencia organización, categoría y ubicación; no copia sus nombres. Documentar dependencias funcionales y claves candidatas de las 23 tablas, justificar cualquier agregado persistido (impacto es un resultado documentado y horas agregadas deben mantenerse consistentes). Generar ERD con cardinalidades reales y diccionario físico. Proveer consultas SELECT, JOIN, GROUP BY y llamadas a funciones. Alembic es la única fuente ejecutable de cambios; schema.sql/functions.sql/triggers.sql serán exportaciones o archivos consumidos por migraciones, no una instalación paralela.

## Nota de entrega
No se modifica la estructura de 23 tablas por el cambio de proveedor de correo. TOKEN_CUENTA y email_verificado se mantienen para los flujos reales. Las cuentas ficticias preactivadas de demo se provisionan de forma controlada, sin simular verificación de correo real ni habilitar bypass para registro público.
