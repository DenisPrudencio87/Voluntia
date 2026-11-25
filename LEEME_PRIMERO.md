# Voluntia — inicio del desarrollo (revisión 2)
La documentación está preparada; la aplicación aún no está programada. No reinstales herramientas ni recrees el repositorio. Esta actualización sustituye archivos de instrucciones, no la rúbrica ni las referencias originales.

1. En la carpeta Voluntia existente, copia los archivos actualizados respetando las rutas. Antes de usar secretos, verifica que .gitignore los excluya. No incluir contraseñas ni cadenas de conexión en chat/Git.
2. `git status` y `git diff --stat` permiten revisar la actualización. Puedes dejar que Codex haga commit inicial de esta revisión en su primera rama de trabajo.
3. Abre VS Code en Voluntia, inicia Docker Desktop, verifica modo «Aprobar por mí», razonamiento alto si disponible. No necesitas acceso completo.
4. Pega el mensaje de inicio entregado junto con este paquete; Codex debe leer AGENTS.md, PROMPT_MAESTRO.md y docs activos, implementar y probar, no quedarse en un plan. Autoriza solo ramas/commits/PR/CI del repositorio privado existente y merges propios con CI verde; no autorices cambios remotos de infraestructura todavía.
5. Para reanudar: `Lee AGENTS.md, PROMPT_MAESTRO.md y docs/PROGRESO.md; verifica git status y continúa desde la primera tarea pendiente sin repetir trabajo comprobado.`
6. No necesitas configurar Mailpit, Angular o FastAPI a mano. Supabase/Render están preparados, credenciales y despliegue se configurarán cuando el código esté listo y probado. No habilites Auto-Deploy ni envíes secretos a Codex por chat. El correo real queda pendiente; no habilites registro público en demo remota.
7. Antes del examen comprueba URL desde otro equipo, CI, PR, funciones SQL y recorrido demo. Practica la guía y respeta reglas académicas. La nota depende del docente, en particular de la sustentación individual.

## Cambios respecto al original
23 de 29 tablas, sin moderador independiente ni extras pospuestos. Revisión 2 conserva ese alcance y ajusta Python, correo, API externa, portabilidad y estado del repositorio/despliegue. No se crean servicios ni se ejecutan pruebas de aplicación con este paquete.
