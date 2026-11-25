param([int]$BackendPort=8000,[int]$FrontendPort=4200,[switch]$Built)
. (Join-Path $PSScriptRoot 'common.ps1')
Set-Location $ProjectRoot
if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Ejecuta setup antes de iniciar.' }
Assert-PortFree $BackendPort
if (-not $Built) { Assert-PortFree $FrontendPort }
$runtimeRoot = Join-Path $ProjectRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
$recordsPath = Join-Path $runtimeRoot 'processes.json'
if (Test-Path -LiteralPath $recordsPath) { throw 'Hay un registro de ejecución. Usa stop.ps1 antes de iniciar de nuevo.' }
$records = @()
$previousOrigin = $env:PUBLIC_BASE_URL
try {
    $env:PUBLIC_BASE_URL = if ($Built) { "http://localhost:$BackendPort" } else { "http://localhost:$FrontendPort" }
    $server = Start-Process -WindowStyle Hidden -PassThru -FilePath $PythonExe -WorkingDirectory $ProjectRoot -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port',"$BackendPort") -RedirectStandardOutput (Join-Path $runtimeRoot 'backend.log') -RedirectStandardError (Join-Path $runtimeRoot 'backend-error.log')
    $records += @{ Id=$server.Id; Started=$server.StartTime.ToUniversalTime().Ticks; Marker=$ProjectRoot }
    if (-not $Built) {
        $node = (Get-Command node).Source
        $proxyPath = Join-Path $runtimeRoot 'proxy.json'
        $proxySettings = @{}
        foreach ($route in @('/api','/docs','/openapi.json')) { $proxySettings[$route] = @{ target="http://127.0.0.1:$BackendPort"; secure=$false } }
        [System.IO.File]::WriteAllText($proxyPath, (ConvertTo-Json -Depth 4 -InputObject $proxySettings), (New-Object System.Text.UTF8Encoding($false)))
        $cliPath = '"' + (Join-Path $ProjectRoot 'frontend\node_modules\@angular\cli\bin\ng.js') + '"'
        $client = Start-Process -WindowStyle Hidden -PassThru -FilePath $node -WorkingDirectory (Join-Path $ProjectRoot 'frontend') -ArgumentList @($cliPath,'serve','--host','localhost','--port',"$FrontendPort",'--proxy-config',('"'+$proxyPath+'"')) -RedirectStandardOutput (Join-Path $runtimeRoot 'frontend.log') -RedirectStandardError (Join-Path $runtimeRoot 'frontend-error.log')
        $records += @{ Id=$client.Id; Started=$client.StartTime.ToUniversalTime().Ticks; Marker=$ProjectRoot }
    }
    ConvertTo-Json -InputObject @($records) | Set-Content -Encoding UTF8 -LiteralPath $recordsPath
    Invoke-Checked $PythonExe @('-m','scripts.wait_ready',"http://localhost:$BackendPort/api/ready")
    if (-not $Built) { Invoke-Checked $PythonExe @('-m','scripts.wait_ready',"http://localhost:$FrontendPort") }
    Write-Host $(if ($Built) { "Voluntia: http://localhost:$BackendPort" } else { "Voluntia: http://localhost:$FrontendPort | API: http://localhost:$BackendPort/docs" })
} catch {
    ConvertTo-Json -InputObject @($records) | Set-Content -Encoding UTF8 -LiteralPath $recordsPath
    & (Join-Path $PSScriptRoot 'stop.ps1')
    throw
} finally { $env:PUBLIC_BASE_URL = $previousOrigin }
