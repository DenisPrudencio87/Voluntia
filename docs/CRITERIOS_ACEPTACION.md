# Matriz de aceptación — objetivo 20/20
Cada fila exige evidencia real (ruta de archivo, comando, resultado y fecha). Estado inicial PENDIENTE. No autocalificar como nota oficial.
| Criterio /4 | Condición verificable |
|---|---|
| Frontend | Angular compilable, Bootstrap responsive a 360 y 1280 px, formularios validados, componentes/servicios/guards, navegación y estados de error/vacío/carga, flujo E2E exitoso. |
| Backend | FastAPI modular, Swagger, Pydantic, reglas de negocio y permisos/propiedad probados, API Supabase Storage integrada con manejo de fallos; prueba externa real cuando credenciales autorizadas. Verificación/recuperación por Mailpit en local; correo real pendiente. |
| Base de datos | 23 tablas producto, ERD y dependencias 3FN, PK/FK/UNIQUE/CHECK, migración reproducible, cuatro funciones SQL y trigger; prueba concurrente de cupos y rollback, consultas demostrables. |
| Integración/Git | URL HTTPS pública funcional con datos persistentes, frontend/backend/DB integrados, ramas/commits/PR reales, GitHub Actions exitoso con build y tests; no considerar listo si solo local. |
| Sustentación | README reproducible, guía con archivos y líneas reales, demo de roles, explicación SQL/API/Angular/Git/CI/despliegue, estudiante realiza recorrido y responde preguntas. |

## Cierre de producto
Todos los módulos del alcance tienen endpoints, UI y datos reales; ninguna función pospuesta aparece como disponible. Credenciales fuera de Git; documentación privada con acceso correcto; no fallos críticos conocidos. Verificar URL desde navegador externo, sesión, persistencia tras reinicio y Storage real. Correo local probado con Mailpit; correo real pendiente para registro público. Verificar bloqueo de registro/recuperación en demo sin correo y ausencia de bypass. Verificar scripts Windows y clon limpio; indicar pruebas remotas pendientes. Para publicación con usuarios reales: revisar privacidad/consentimiento, backups y restauración, límites de abuso, retención de datos y gestión de incidentes. Si falta alguna comprobación, distinguir demo académica desplegable de preparación real para producción.
