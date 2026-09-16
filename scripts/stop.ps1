$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$State = Join-Path $ProjectRoot 'data\local\processes.json'
if (-not (Test-Path -LiteralPath $State)) { Write-Host 'No recorded project processes.'; exit 0 }
$processes = Get-Content -LiteralPath $State -Raw | ConvertFrom-Json
foreach ($id in @($processes.apiPid, $processes.apiListenerPid, $processes.webPid, $processes.webListenerPid) | Select-Object -Unique) {
  $process = Get-Process -Id $id -ErrorAction SilentlyContinue
  if ($process) { Stop-Process -Id $id }
}
Remove-Item -LiteralPath $State
Write-Host 'Stopped recorded Med Fraud processes.'
