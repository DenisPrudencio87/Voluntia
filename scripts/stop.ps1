. (Join-Path $PSScriptRoot 'common.ps1')
$recordsPath = Join-Path $ProjectRoot '.runtime\processes.json'
if (-not (Test-Path -LiteralPath $recordsPath)) { Write-Host 'No hay procesos registrados por Voluntia.'; return }
$records = Get-Content -Raw -LiteralPath $recordsPath | ConvertFrom-Json
foreach ($record in @($records)) {
    $ownedProcess = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
    if ($ownedProcess -and $ownedProcess.StartTime.ToUniversalTime().Ticks -eq $record.Started) {
        $details = Get-CimInstance Win32_Process -Filter "ProcessId=$($record.Id)"
        if ($details.CommandLine -and $details.CommandLine.Contains($ProjectRoot)) {
            Stop-Process -Id $record.Id
            Write-Host "Detenido proceso propio $($record.Id)"
        } else { Write-Warning "Proceso $($record.Id) no coincide con el proyecto; se conserva." }
    }
}
Remove-Item -LiteralPath $recordsPath
