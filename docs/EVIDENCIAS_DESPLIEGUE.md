# Finalización e integración real: evidencia y pendientes

Actualizado: 25/11/2026, America/Lima. Este registro no acredita un despliegue hasta
que se complete y se compruebe la URL. No contiene secretos.

## Autorización vigente

El propietario autorizó conexión/migraciones/grants en Supabase existente,
creación de runtime, Storage privado, datos ficticios y publicación del repositorio
original tras revisar exposición de secretos. No autoriza cambiar sus claves
existentes, borrar información ni reescribir historial. Importará variables y
desplegará manualmente en Render; Auto-Deploy permanece desactivado.

## Estado observado

| Elemento | Evidencia / estado |
|---|---|
| Código auditado localmente | `6bc74fb8cad8d598e3b34be148525125d0f9c076`, rama feature/auditoria-final |
| PR auditoría | [#6](https://github.com/DenisPrudencio87/Voluntia/pull/6); integración pendiente de consultar checks finales |
| Pruebas clon limpio | Backend 58 aprobadas; Angular 8; Playwright 8 escritorio/móvil; build correcto |
| Windows | Setup, check, start compilado, start desarrollo y stop aprobados; rol SQL limitado |
| Docker | Imagen final, PORT=10000, UID 999, health/ready y archivos/roles HTTP aprobados localmente |
| Credenciales de entrada | `.local/supabase-input.env` presente e ignorado; no se imprimieron valores; claves usadas solo en memoria para comparación de exposición |
| PostgreSQL Supabase | Autorizado, conexión real pendiente |
| Runtime remoto | Creación y permisos pendientes; no se usará propietario como cuenta web |
| Migraciones remotas | Pendientes; head esperado 0003 y 23 tablas de producto |
| Storage remoto | Bucket esperado voluntia-demo-private; configuración y operaciones reales pendientes |
| Demo remota | Seed/cuentas pendientes; archivo destino `.local/demo-credentials-remote.json` |
| Configuración Render | `.local/render.env` pendiente de runtime y Storage comprobados |
| Visibilidad GitHub | Última observación privada; cambio autorizado condicionado a revisión completa de exposición |
| Clonación anónima | Pendiente del cambio seguro a público |
| Render | URL asignada por propietario: https://voluntia-35ly.onrender.com ; despliegue y verificación pública pendientes |

La consulta más reciente de GitHub fue detenida antes de ejecutarse porque el
servicio de revisión automática de comandos protegidos alcanzó su límite de uso.
No constituye un fallo de CI ni un rechazo de seguridad del código. Requiere
restablecer la disponibilidad de la revisión para continuar el orden autorizado;
no se ha intentado eludirla.

Revisión independiente local de exposición: **285 objetos Git (blobs/commits)**
en **17 refs locales**; cero coincidencias de las dos credenciales Supabase reales
de entrada, cero patrones de claves privadas/GitHub/Storage y cero rutas privadas
versionadas encontradas. Informe sin valores en `.local/public-exposure-local.json`.
No se refrescaron refs remotas ni se revisaron aún PR/logs/artefactos; por tanto esta
comprobación parcial no autoriza por sí sola cambiar visibilidad.

## Secuencia pendiente, sin repetir la auditoría

1. Consultar PR #6 y CI de su SHA; revisar diff propio e integrar solo con checks
   satisfactorios. Sincronizar main y registrar SHA estable.
2. Cargar privadamente supabase-input.env, codificar contraseña al construir URI,
   confirmar proyecto/destino, TLS y Session pooler 5432. Inspeccionar sin limpiar.
3. Respaldar si hay datos, crear runtime solo si falta, migrar y aplicar grants;
   comprobar 23 PK/tablas, 29 FK, restricciones, índices, cuatro funciones, triggers
   y Alembic 0003. Ningún pytest/fixture/reset remoto.
4. Verificar bucket privado y operaciones reales con PDF/evidencia/certificado,
   acceso autorizado, firma temporal y denegación pública. Registrar resultados
   sin claves ni URLs firmadas.
5. Generar demo solo si la aplicación está vacía, preservando cuentas y archivos
   locales. Guardar credenciales remotas en su archivo separado.
6. Generar render.env exclusivamente con runtime, JWT propio y variables de demo;
   preparar configuración localhost separada para universidad, sin propietario.
7. Revisar secretos en contenido/historial/refs/PR/logs/artefactos antes de hacer
   público el repositorio. Comprobar visibilidad y clonación sin credenciales.
8. Actualizar evidencias y guías, integrar cambios propios con CI verde y dejar
   main limpio/sincronizado. Entregar pasos de importación y deploy manual Render.

Los procedimientos técnicos detallados ya están en
[AUDITORIA_FINAL](AUDITORIA_FINAL.md) y [GUIA_DESPLIEGUE](GUIA_DESPLIEGUE.md).
No corresponde repetir instalación ni pruebas aprobadas salvo cambios relevantes.
