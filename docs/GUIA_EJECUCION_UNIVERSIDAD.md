# Ejecución desde la computadora de la universidad

Guía preparada y scripts probados en Windows del entorno de desarrollo. No se ha
probado una computadora física de la universidad ni una base Supabase remota.

## Preparar antes de salir

1. Confirmar acceso privado al repositorio existente. Llevar un clon actualizado y
   conexión a Internet para descargar dependencias. No cambiar la visibilidad.
2. Comprobar Node 24.15 o posterior de la serie 24 (probado 24.21.0), `npm.cmd`, Python 3.13 y Git. Los scripts no instalan software
   del sistema ni requieren administrador. Si faltan herramientas, usar un equipo
   ya preparado o la URL demo después de su despliegue autorizado.
3. Elegir PostgreSQL de demostración separado. No utilizar producción para pruebas
   ni copiar secretos a una USB compartida. Las claves de demo se entregan de forma
   privada. Nunca mostrar `.env` o `.local/demo-credentials.json` al proyectar.
4. Ensayar el recorrido de la guía de sustentación. Llevar un respaldo local de
   los datos ficticios y conocer las limitaciones de red/arranque en frío.

## Alternativa A: URL HTTPS

URL asignada: **https://voluntia-35ly.onrender.com**. Despliegue manual del
propietario y comprobación pública pendientes; no se presenta todavía como URL
funcional. Tras desplegar, abrir `/api/health` y `/api/ready`: ambos deben responder
200; ready comprueba conexión y revisión Alembic. Abrir `/docs` para FastAPI.
Acceder con cada una de las tres cuentas ficticias entregadas privadamente y
recorrer los paneles de la guía de sustentación. No mostrar contraseñas al proyectar.
Sin correo real: registro y recuperación permanecen cerrados, y se usan cuentas
ficticias preactivadas. Una URL de Render configurada no constituye evidencia de
publicación funcional. No inventar una URL ni afirmar que ya está disponible.

## Alternativa B: Windows sin Docker

Requiere Node/Python y una base PostgreSQL de demo ya migrada y accesible. La
aplicación no invoca Docker durante su instalación/ejecución por esta vía.

```powershell
git clone https://github.com/DenisPrudencio87/Voluntia.git
cd Voluntia
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1 -ClosedDemo
```

El argumento `Bypass` solo afecta ese proceso. Abrir `.env` privadamente en un editor:
configurar `DATABASE_URL` con el usuario de ejecución de la demo y TLS cuando la
base sea remota. Mantener `APP_ENV=local`, `STORAGE_BACKEND=local`,
`EMAIL_MODE=disabled`, `PUBLIC_SIGNUP_ENABLED=false` para esta ejecución local
cerrada. Si la base de demo conserva referencias de Supabase Storage, configurar
`STORAGE_BACKEND=supabase` y sus variables servidor autorizadas; usar storage local
solo con sus archivos ficticios locales correspondientes. No copiar las claves de Storage al frontend. El secreto JWT se genera
localmente. `setup` no sobrescribe un `.env` existente.

Si la BD remota todavía no tiene el esquema, detener ese paso: aplicar migraciones
requiere autorización específica. Puede usarse una BD local preparada. El comando
de inicio nunca aplica migraciones ni resetea datos.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1 -Built
# Navegador: http://localhost:8000
# Swagger: http://localhost:8000/docs
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop.ps1
```

`-Built` sirve Angular compilado desde FastAPI en una sola URL. Sin ese argumento,
inicia Angular en 4200 y backend en 8000, con proxy del mismo origen.
Se pueden elegir puertos sin matar procesos ajenos:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1 -BackendPort 8011 -FrontendPort 4211
```

Los procesos se registran con PID, hora de creación y ruta. `stop` comprueba esos
datos y solo detiene los procesos del proyecto. Los logs están en `.runtime`.
No compartir logs de pruebas que puedan contener datos de cuentas ficticias.

### Configuración portátil privada para USB

Cuando se complete la integración remota, el responsable preparará
`.local/universidad.env`, con APP_ENV=local, PUBLIC_BASE_URL=http://localhost:8000,
EMAIL_MODE=disabled, PUBLIC_SIGNUP_ENABLED=false, usuario PostgreSQL runtime con TLS
y STORAGE_BACKEND=supabase con las variables servidor del bucket demo. Contendrá
JWT local propio y ninguna contraseña del propietario/migrador ni token de GitHub.
**El archivo está pendiente de crear y comprobar**; no copiar render.env sin adaptar,
porque APP_ENV=demo exige HTTPS y cookies Secure, incompatibles con localhost HTTP.

Tras comprobar el repositorio público y recibir ese archivo privado, el recorrido
mínimo de una PC nueva será:

```powershell
git clone https://github.com/DenisPrudencio87/Voluntia.git
cd Voluntia
# Copiar privadamente universidad.env de la USB a .env en esta carpeta.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1 -ClosedDemo
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1 -Built
# http://localhost:8000 ; Swagger http://localhost:8000/docs
# Al terminar:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop.ps1
```

Setup conserva un .env preexistente; no migra Supabase. Si se desea diagnóstico,
ejecutar check.ps1 antes de start. Llevar únicamente universidad.env y las claves
de cuentas ficticias remotas entregadas privadamente; no llevar supabase-input.env,
backups ni contraseña de propietario. La configuración servidor de Storage es
secreta: no dejarla en una PC compartida ni publicarla en el repositorio.
La clonación sin autenticación está pendiente de la revisión de exposición y del
cambio autorizado a público; verificar su estado en EVIDENCIAS_DESPLIEGUE.

## Alternativa C: Docker local aislado

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1 -Docker
.\.venv\Scripts\python.exe -m scripts.seed_demo
docker compose --profile app up -d --build app
```

Abrir `http://localhost:8080`. PostgreSQL usa `127.0.0.1:55432`, SMTP Mailpit 1025
y buzón `http://localhost:8025`. Todos se enlazan solo a loopback. El seed exige
base vacía; si ya existe una demo, usar esas cuentas privadas o una base nueva
dedicada. No borrar volúmenes para arreglar un error de instalación.

## Diagnóstico rápido

| Síntoma | Comprobación y respuesta |
|---|---|
| Puerto ocupado | Ejecutar check; elegir otro puerto. No finalizar procesos desconocidos. |
| API 503/ready no disponible | Revisar conectividad y esquema con `python -m scripts.diagnose`; no imprimir DSN. |
| Angular no abre | Revisar `.runtime/frontend-error.log`; repetir setup si faltan paquetes. Proxy JSON se genera UTF-8 sin BOM. |
| Error de PowerShell por políticas | Usar el comando con `-ExecutionPolicy Bypass` por proceso; no cambiar políticas globales. |
| Registro cerrado | Es el comportamiento esperado sin SMTP. Usar cuenta ficticia provisionada. |
| Error SMTP local | Arrancar Mailpit y revisar host/puerto. No fingir verificación de correo. |
| No publica actividad | Verificar organización/documentos y cierre/inicio futuros. |
| No emite certificado | Actividad finalizada, asistencia efectiva con entrada/salida y horas positivas. |
| 429 en login | Esperar el intervalo indicado. No desactivar el limitador. |

Si la red institucional bloquea la BD remota, usar la alternativa local preparada.
La instalación limpia y arranque Windows verificados se registran en PROGRESO;
la conectividad específica de la universidad debe comprobarla el estudiante.
