param([int]$BackendPort=8000,[int]$FrontendPort=4200)
. (Join-Path $PSScriptRoot 'common.ps1')
Set-Location $ProjectRoot
Invoke-Checked 'node' @('--version')
Invoke-Checked 'npm.cmd' @('--version')
if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Falta venv. Ejecuta scripts/setup.ps1.' }
Invoke-Checked $PythonExe @('--version')
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.env'))) { throw 'Falta .env; ejecutar setup.' }
Invoke-Checked $PythonExe @('-m','scripts.diagnose')
foreach ($port in @($BackendPort,$FrontendPort)) {
    $occupied = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    Write-Host "Puerto ${port}: $(if ($occupied) {'ocupado (verificar si corresponde a Voluntia)'} else {'disponible'})"
}
Write-Host 'Diagnóstico terminado. Docker no es requisito de ejecución del proceso de aplicación.'
