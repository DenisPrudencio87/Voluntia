# Brechas y acciones posteriores

La implementación local y sus evidencias no equivalen a publicación ni a producción.
No se estima una nota oficial. Consultar PROGRESO para la última validación.

| Pendiente | Motivo / acción concreta |
|---|---|
| Supabase remoto | Requiere autorización específica para migración y grants. Confirmar Session pooler, rol runtime y TLS; ejecutar la guía sin usar base compartida de terceros. |
| Storage externo real | Integración implementada y contrato/fallos probados localmente. Falta bucket privado autorizado, upload/download reales y comprobación de permisos con credenciales del proyecto. |
| Render/HTTPS | Docker local comprobado. Servicio existente y Auto-Deploy no modificados. Falta autorización de despliegue manual y smoke externo/persistencia tras reinicio. |
| Correo real | Proveedor pendiente. Mailpit real local comprobado. Demo remota mantiene registro/recuperación cerrados; no se habilita producción abierta con cuentas preactivadas. |
| Equipo universitario | Scripts Windows comprobados en entorno de desarrollo y clon limpio según PROGRESO. Falta ensayo en la PC/red concretas; guía incluye contingencia. |
| Sustentación | Documentada, pero el dominio y ensayo corresponden al estudiante. No puede certificarse automáticamente. |
| Producción | Revisión de privacidad, consentimiento, respaldo remoto y restauración, abuso/proxy, retención e incidentes antes de usuarios reales. |
| Tamaño Angular | Advertencia ~615 kB iniciales, ~114 kB transferencia estimada. Bootstrap completo y carga lazy; futura optimización sin ocultar el presupuesto actual. |
| TestClient | Aviso de deprecación del adaptador HTTPX en Starlette. Pruebas actuales pasan; actualizar adaptador de desarrollo en un hito compatible. |

Se continúa cualquier tarea local independiente de esos permisos. No se necesitan
secretos de nube para ejecutar la demo local. Las credenciales se configuran por
canales privados, nunca pegándolas en chat ni incorporándolas al repositorio.
