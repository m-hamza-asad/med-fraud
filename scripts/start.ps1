param([int]$ApiPort = 8000, [int]$WebPort = 5173)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run scripts\setup.ps1 first.' }
function Test-Port([int]$Port) {
  $client = [System.Net.Sockets.TcpClient]::new()
  try {
    $connection = $client.ConnectAsync('127.0.0.1', $Port)
    if (-not $connection.Wait(300)) { return $false }
    return $client.Connected
  } catch {
    return $false
  } finally {
    $client.Dispose()
  }
}
while (Test-Port $ApiPort) { $ApiPort++ }
while (Test-Port $WebPort) { $WebPort++ }
$env:PYTHONPATH = Join-Path $ProjectRoot 'apps\api'
$env:MEDFRAUD_API_PORT = "$ApiPort"
$apiArgs = @('-m','uvicorn','medfraud.main:app','--host','127.0.0.1','--port',"$ApiPort")
$api = Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList $apiArgs -PassThru -WindowStyle Hidden
$viteEntry = Join-Path $ProjectRoot 'apps\web\node_modules\vite\bin\vite.js'
$webArgs = @("`"$viteEntry`"",'--host','127.0.0.1','--port',"$WebPort")
$web = Start-Process -FilePath 'node.exe' -ArgumentList $webArgs -WorkingDirectory (Join-Path $ProjectRoot 'apps\web') -PassThru -WindowStyle Hidden
function Find-ListenerPid([int]$Port) {
  $line = netstat -ano | Select-String (":$Port\s+.*LISTENING") | Select-Object -First 1
  if ($line -and $line.Line -match '\s(\d+)$') { return [int]$Matches[1] }
  return $null
}
$apiListener = $null; $webListener = $null; $apiReady = $false; $webReady = $false
for ($attempt = 0; $attempt -lt 40 -and (-not $apiReady -or -not $webReady); $attempt++) {
  Start-Sleep -Milliseconds 250
  $apiListener = Find-ListenerPid $ApiPort
  $webListener = Find-ListenerPid $WebPort
  try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/v1/health" -TimeoutSec 1
    $apiReady = $health.status -in @('ready', 'degraded')
  } catch { $apiReady = $false }
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$WebPort/" -TimeoutSec 1
    $webReady = $response.StatusCode -eq 200
  } catch { $webReady = $false }
}
if (-not $apiReady -or -not $webReady) {
  foreach ($id in @($api.Id, $web.Id)) { Stop-Process -Id $id -ErrorAction SilentlyContinue }
  throw 'A Med Fraud service did not become healthy within 10 seconds. Check docs\TROUBLESHOOTING.md.'
}
if (-not $apiListener) { $apiListener = $api.Id }
if (-not $webListener) { $webListener = $web.Id }
@{ apiPid = $api.Id; apiListenerPid = $apiListener; webPid = $web.Id; webListenerPid = $webListener; apiPort = $ApiPort; webPort = $WebPort } | ConvertTo-Json | Set-Content -LiteralPath 'data\local\processes.json'
Write-Host "Application: http://127.0.0.1:$WebPort"
Write-Host "API health:  http://127.0.0.1:$ApiPort/api/v1/health"
Write-Host 'Use scripts\stop.ps1 to stop only these recorded project processes.'
