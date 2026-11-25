# Plan ejecutable por fases
En cada fase: inspeccionar → implementar → ejecutar pruebas → corregir → registrar resultados → commit. No iniciar características nuevas si el flujo crítico anterior falla. Git desde fase 0; crear ramas feature/*, PR por hitos cuando autorizado.

| Fase | Entregables y puerta de salida |
|---|---|
| 0 | Inventario node/npm/python/git/docker/gh, comprobar directorio, versiones, .gitignore, README, estructura, entorno de test aislado. No sobrescribir trabajo previo. |
| 1 | Migraciones 23 tablas, catálogos, ERD, diccionario, funciones y trigger; PostgreSQL limpio migra correctamente y constraints/concurrencia probados. |
| 2 | API auth, roles, perfiles, correo adaptador, autorización y errores; pruebas de registro/login/verificación/recuperación/permisos. |
| 3 | Organización, documentos, categorías/habilidades, actividades, inscripciones/cupos, asistencia, impacto, certificados, notificaciones, bitácora; pruebas de ciclo completo. |
| 4 | Angular Bootstrap responsive, rutas y paneles reales; build y pruebas frontend. |
| 5 | Integración UI/API/DB, Playwright escritorio/móvil; ningún botón muerto. |
| 6 | Seguridad, casos negativos, concurrencia, revisión de dependencias y secretos, pruebas completas. |
| 7 | CI real con PostgreSQL, ramas y PR; matriz de evidencia, logs y estados comprobados. |
| 8 | Docker build/run, configuración Supabase/Storage/Render y guía; despliegue real solo con autorización y credenciales; smoke test público, persistencia y HTTPS. |
| 9 | Guía de sustentación, demo reproducible con datos ficticios, SQL ejemplos y preguntas, informe de brechas. |

Prioridad de rescate si tiempo limitado: completar flujo administrador→organización→actividad→voluntario→aceptación→asistencia→impacto→certificado, UI responsive, DB funciones, CI y despliegue. No abandonar validaciones o seguridad para añadir extras. Si algo falta, marcar pendiente con evidencia y no declarar proyecto completo.
