# Plan de pruebas obligatorio
Usar PostgreSQL descartable; jamás ejecutar limpieza contra producción. Adaptadores fake para correo/storage solo en test. Datos ficticios, fechas relativas a reloj de prueba; separar fixtures de seeds demo. CI debe fallar si falla cualquier prueba requerida.

| ID | Escenario | Resultado esperado |
|---|---|---|
| DB01 | Migrar BD vacía y consultar restricciones | 23 tablas producto, FK/PK/UNIQUE/CHECK válidas |
| DB02 | Correo duplicado con mayúsculas | Rechazo, una cuenta |
| DB03 | Inscripción duplicada concurrente | Una inscripción, conflicto |
| DB04 | Dos aceptaciones simultáneas para último cupo, conexiones separadas | Una aceptación, otra conflicto; historial y notificación coherentes |
| DB05 | Error dentro de aceptación | Rollback total, sin historial/aviso huérfano |
| DB06 | Fechas/cupo inválidos, FK inexistente | Rechazo |
| DB07 | Horas/estadísticas con múltiples inscritos/evidencias | Sin duplicación |
| API01 | Registro, verificar, login, logout, recuperar | Tokens de un uso, sesión válida, contraseña anterior inválida |
| API02 | Usuario suspendido con token vigente | 403/401 |
| API03 | Visitante/voluntario intenta ruta admin | 401/403 |
| API04 | Organización A modifica actividad/documento B | 403/404 sin fuga |
| API05 | Organización pendiente publica | Rechazo |
| API06 | Borrador, vencida, cancelada/finalizada recibe postulación | Rechazo |
| API07 | Habilidad obligatoria ausente | Rechazo claro |
| API08 | Espera, cancelación y promoción | Cupo liberado, historial y avisos |
| API09 | Asistencia inválida o certificado sin asistencia | Rechazo |
| API10 | Certificado duplicado y código inválido | Sin duplicación, respuesta pública mínima |
| API11 | Archivo falso, demasiado grande, descarga ajena | Rechazo |
| API12 | CSRF inválido, abuso de login/registro | Rechazo/429 |
| API13 | Proveedor correo falla | Error controlado, reintento de envío disponible |
| API14 | Cancelación actividad | Historial y avisos de todos los afectados, transacción |
| API15 | Suspensión organización y último admin | Bloqueos correctos |
| UI01 | Formularios inválidos y error API | Mensajes claros |
| UI02 | Catálogo filtros combinados y paginación | Resultados reales |
| E2E01 | Admin aprueba organización, publica, voluntario postula, acepta, asistencia, impacto, certificado y verificación | Flujo completo con datos persistentes; reloj/fixture de test para fechas, no saltarse reglas en producción |
| E2E02 | Recorrido móvil 360px y escritorio 1280px | Sin overflow horizontal general, navegación usable |
| OPS01 | Docker build y smoke test | /, /api/health, /api/ready funcionales |
| OPS02 | CI en PR | Build frontend y tests backend/DB exitosos, E2E según workflow |
| OPS03 | URL real, correo y storage reales, reinicio | HTTPS, persistencia, operaciones reales verificadas tras autorización |

Registrar comando, duración si disponible, fecha, éxito/fallo y evidencia. No inventar resultados. Añadir pruebas cuando se detecte una regresión. Usar Playwright y Pytest; TestSprite opcional únicamente si ya disponible y sin transmitir datos sensibles, no es requisito.
