# Guía detallada de sustentación

El estudiante debe comprender y poder modificar el código que presenta. La rúbrica
evalúa ese dominio; esta guía ayuda a ensayar, pero no sustituye la sustentación ni
garantiza nota. Los datos de la demo son ficticios y las contraseñas se mantienen privadas.

## Relato inicial (1–2 minutos)

Voluntia conecta personas con organizaciones que publican oportunidades sociales.
Una postulación deja trazabilidad desde la solicitud hasta las horas efectivas y
un certificado verificable. Se conserva el historial; rechazar o cancelar no borra
participación pasada. Tres responsabilidades: voluntario participa, organización
gestiona sus actividades y administrador supervisa/verifica.

La arquitectura es un monolito modular: Angular/Bootstrap → HTTP `/api/v1` → routers
FastAPI → servicios de negocio → SQLAlchemy Core/PostgreSQL. Una URL sirve frontend
compilado y API en Docker. Storage externo se consume solo desde backend. Explicar
qué se verificó localmente y qué sigue pendiente de publicación/autorización.

## Preparación privada

Ejecutar instalación y `scripts.seed_demo` exclusivamente en una base local vacía.
Abrir privadamente `.local/demo-credentials.json` y usar tres perfiles de navegador
separados. El seed crea organización verificada, otra pendiente con documento
ficticio, dos actividades futuras y un escenario histórico en curso con una
inscripción aceptada. `.local/demo-manifest.json` contiene sus identificadores y
horas UTC, sin contraseñas. No proyectar esos archivos de credenciales.

El escenario histórico permite demostrar asistencia/fin/certificado en el examen
sin esperar días ni alterar el reloj del servidor. Fue provisionado como dato
ficticio desde consola, no mediante una ruta web de bypass. Para demostrar creación
en vivo usar una actividad futura; las reglas de fechas permanecen activas.

## Recorrido sugerido (12–18 minutos)

1. **Visitante:** inicio, misión, categorías y estadísticas SQL reales. Catálogo:
   combinar texto, categoría, modalidad, ubicación, fecha y cupos; mostrar vacío
   cuando no hay resultados. Abrir detalle y perfil público de organización.
   Reducir ancho a 360 px y abrir navegación móvil.
2. **Administrador:** entrar con su cuenta privada, panel Administración. Abrir
   Red Solidaria (demo), descargar constancia ficticia pendiente, aprobar documento
   con motivo y después aprobar organización. Mostrar que sin documento aprobado
   el servidor rechaza aprobación. Consultar bitácora del cambio.
3. **Organización:** entrar en otra sesión. Seleccionar organización, crear borrador
   con categoría/fechas/cupo/modalidad/habilidades. Mostrar validación de fechas y
   requisito de lugar si es presencial. Publicar y confirmar visibilidad pública.
   Explicar por qué una organización pendiente no puede publicar.
4. **Voluntario:** editar perfil y habilidades, postular a una actividad futura con
   motivación, consultar estado e historial. Una segunda postulación es conflicto.
   Mostrar notificaciones y que cancelar antes de inicio impide reinscribirse.
5. **Organización:** aceptar postulación. Explicar bloqueo de cupo y función SQL;
   lista de espera no ocupa plaza y su promoción es manual. Con capacidad 1,
   intentar aceptar otro postulante devuelve conflicto; cancelar aceptado libera
   plaza. La suite concurrente demuestra que dos peticiones no ocupan la última.
6. **Participación histórica:** gestionar Taller comunitario de la demo, registrar
   asistencia de la inscripción aceptada con entrada/salida dentro del evento.
   Copiar sus horas del manifiesto privadamente y convertirlas a hora local de UI.
   Finalizar después del fin y guardar impacto/beneficiarios. Las horas se calculan,
   no se introducen manualmente ni se suman otra vez desde certificados.
7. **Certificado:** explicar el aviso de visibilidad pública mínima y emitir.
   Voluntario descarga PDF propio. Verificar código como visitante: nombre,
   actividad, organización, fecha y horas, sin correo ni documento de identidad.
   Intentar descargar desde otra cuenta debe fallar. Una asistencia certificada
   queda protegida contra cambios.
8. **Correo local:** registrar una cuenta ficticia distinta usando Mailpit local,
   abrir enlace de verificación y recuperar contraseña. Demostrar que repetir un
   token falla. No decir que esto prueba entrega real por un proveedor externo.
9. **Ingeniería:** Swagger, funciones SQL, ERD, test de concurrencia, PR y CI.
   Mostrar Docker health/ready y los scripts Windows. Mostrar la URL pública solo
   si ya fue desplegada y comprobada con autorización; explicar la brecha si falta.

## Archivos que debes saber explicar

| Concepto | Ruta y símbolo que localizar |
|---|---|
| Arranque/rutas/errores/SPA | `backend/app/main.py`: `security_headers`, `database_error`, `frontend` |
| Configuración cerrada | `backend/app/config.py`: `Settings.validate_environment` |
| Sesión/roles/CSRF/abuso | `backend/app/security/session.py`: `current_user`, `valid_csrf`, `RateLimiter` |
| Correo/tokens | `backend/app/services/accounts.py`: `issue_token`, `consume_token`; `services/mail.py`: `send_account_mail` |
| Reglas de estados | `backend/app/services/domain.py`: `change_activity_state` |
| Postular/aceptar | `backend/app/routers/activities.py`: `apply`, `application_state` |
| Asistencia/impacto/certificado | `backend/app/routers/participation.py`; `services/certificates.py` |
| API externa y archivos | `backend/app/services/storage.py`: `validate_file`, `put_object`, `download` |
| Transacción | `backend/app/db.py`: `transaction`, `actor_context`; dependencias `scope="function"` |
| Modelo relacional | `database/schema.sql`, `functions.sql`, `triggers.sql`, `invariants.sql`; `backend/migrations/versions` |
| Angular modular | `frontend/src/app/app.routes.ts`, `services`, `guards`, `models`, `pages` |
| Formularios | `frontend/src/app/components/record-form.ts`; `skills-editor.ts` |
| Caso concurrente real | `backend/tests/test_database.py`: `test_last_place_concurrent`, `test_failure_inside_acceptance_rolls_back_all` |
| Integración UI completa | `frontend/e2e/journey.spec.ts` y fixtures `scripts/e2e_*` |
| CI/paquete | `.github/workflows/ci.yml`, `Dockerfile`, `scripts/start.ps1` |

Para obtener líneas actuales sin números obsoletos:

```powershell
rg -n 'def current_user|def change_activity_state|def application_state|def transaction' backend/app
rg -n 'fn_aceptar_inscripcion|FOR UPDATE|CREATE TRIGGER' database
rg -n 'authGuard|submit\(|loadComponent' frontend/src/app
```

## Explicar la función de aceptación

En una transacción se obtiene la actividad con `FOR UPDATE`, después la inscripción.
Se comprueba actor desde contexto de sesión, membresía activa, organización
verificada, estado/plazo y plazas. Solo entonces cambia a aceptada. El trigger
inserta historial, bitácora y notificación. Otro proceso espera el mismo bloqueo,
vuelve a contar y encuentra el cupo ocupado. Si falla la notificación, PostgreSQL
revierte también el estado y el historial. No es suficiente contar en Angular ni
hacer SELECT y UPDATE sin bloqueo. El commit ocurre antes de responder HTTP.

## Preguntas para ensayar

| Pregunta | Idea que debes demostrar con código |
|---|---|
| ¿Por qué 23 tablas y no una tabla enorme? | Entidades y relaciones del alcance; roles/habilidades/membresías son relaciones, sin listas de texto. |
| ¿Cómo justificas 3FN? | Claves candidatas del diccionario; cada atributo depende de la clave de su entidad/relación, sin copiar nombres de otras entidades. Impacto agregado se sincroniza. |
| ¿Qué impide dos aceptados en la última plaza? | Bloqueo compartido de actividad, conteo dentro de transacción y test con dos conexiones. |
| ¿Puede un usuario cambiar el id de organización? | Backend consulta membresía y propiedad en cada operación; guard Angular es solo UX. |
| ¿Por qué cookie y CSRF? | HttpOnly limita lectura del token por JS; cookie se envía automáticamente, por eso se exige CSRF y Origin. XSS y CSRF son riesgos distintos. |
| ¿Qué ocurre al suspender una cuenta? | Estado consultado en cada petición, aun con JWT vigente; cambio de versión revoca sesiones. |
| ¿Qué sucede si SMTP falla? | 503 controlado y rollback; reintento disponible, sin fingir envío. |
| ¿Qué API externa usas? | Supabase Storage por HTTP, credencial solo servidor, archivos privados y firma temporal. Distinguir contrato de test y prueba real pendiente. |
| ¿Cómo evitas duplicar horas? | Se derivan de asistencia efectiva, agregaciones separadas y certificado como instantánea, no otra suma. |
| ¿Por qué no borrar historial? | Trazabilidad de decisiones y participación; estados terminales y registros append-only. |
| ¿Qué es health frente a ready? | Proceso vivo frente a DB/esquema accesibles; ambos insuficientes para afirmar funcionamiento externo completo. |
| ¿Qué aprendiste de CI? | Detectó respuesta 201 antes de commit; consulta inmediata 404. Scope de dependencia corregido y E2E volvió a pasar. |
| ¿Por qué un worker? | Limitador en memoria; al escalar se necesita estado compartido. |
| ¿Está listo para producción? | Presentar pruebas y límites reales, correo/Storage/despliegue/privacidad/backups remotos pendientes. |

## Evidencia SQL y Git

Abrir `database/queries.sql` y ejecutar SELECT, JOIN, GROUP BY y las funciones sobre
la base ficticia. Contar tablas del esquema `voluntia` (23), enseñar una UNIQUE y un
CHECK. Consultar historial ordenado. No usar credenciales ni documentos reales.

En GitHub abrir PR #1–#4 y el hito final, commits descriptivos y ejecuciones de CI
en verde. Enseñar un fallo resuelto sin ocultarlo. El workflow tiene pruebas de
PostgreSQL, Angular y navegador. No confundir una captura de CI con dominio del código:
debes poder explicar qué valida cada prueba y qué no demuestra.
# Lectura complementaria de auditoría

Leer [AUDITORIA_FINAL.md](AUDITORIA_FINAL.md) para explicar los defectos corregidos,
por qué now() y clock_timestamp() difieren, la revocación de membresías, la 3FN real,
las claves actuales de Storage y las evidencias que todavía faltan. No presentar
contratos MockTransport ni una demo local como despliegue o consumo remoto probado.
