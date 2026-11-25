param([switch]$Docker,[switch]$ClosedDemo)
. (Join-Path $PSScriptRoot 'common.ps1')
Set-Location $ProjectRoot
$nodeMajor = [int](& node -p 'Number.parseInt(process.versions.node)')
$nodeMinor = [int](& node -p 'Number(process.versions.node.split(".")[1])')
if ($nodeMajor -ne 24 -or $nodeMinor -lt 15) { throw 'Se requiere Node 24.15 o superior de la serie 24. No se instalará software global.' }
Get-Command npm.cmd -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath $PythonExe)) {
    Invoke-Checked 'py' @('-3.13','-m','venv','.venv')
}
Invoke-Checked $PythonExe @('-c','import sys; assert sys.version_info[:2] == (3,13), "Se requiere Python 3.13"')
Invoke-Checked $PythonExe @('-m','pip','install','-r','backend/requirements-dev.txt')
if ($ClosedDemo) { Invoke-Checked $PythonExe @('scripts/configure_local.py','--closed-demo') }
else { Invoke-Checked $PythonExe @('scripts/configure_local.py') }
Push-Location (Join-Path $ProjectRoot 'frontend')
try {
    Invoke-Checked 'npm.cmd' @('ci','--cache','../.local/npm-cache')
    Invoke-Checked 'npm.cmd' @('run','build')
} finally { Pop-Location }
if ($Docker) {
    Invoke-Checked 'docker' @('compose','up','-d','--wait','db','mailpit')
    Invoke-Checked $PythonExe @('-m','scripts.migrate','--local')
}
Write-Host 'Instalación lista. Usa scripts/check.ps1 y scripts/start.ps1. Sin Docker: configura una BD de demo separada en .env; no se han aplicado migraciones remotas.'
