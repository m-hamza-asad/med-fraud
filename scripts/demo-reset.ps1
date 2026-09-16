param([string]$AdminPassword, [string]$AnalystPassword)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
if (-not $AdminPassword) { $AdminPassword = Read-Host 'Disposable demo admin password (12+ characters)' -MaskInput }
if (-not $AnalystPassword) { $AnalystPassword = Read-Host 'Disposable demo analyst password (12+ characters)' -MaskInput }
$Database = Join-Path $ProjectRoot 'data\local\medfraud.sqlite3'
if (Test-Path -LiteralPath $Database) {
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  Copy-Item -LiteralPath $Database -Destination (Join-Path $ProjectRoot "data\backups\pre-demo-reset-$stamp.sqlite3")
  Remove-Item -LiteralPath $Database
}
$env:PYTHONPATH = Join-Path $ProjectRoot 'apps\api'
& '.\.venv\Scripts\python.exe' -m medfraud.cli init --admin-password $AdminPassword --analyst-password $AnalystPassword
& '.\.venv\Scripts\python.exe' scripts\generate_assets.py --load-demo
Write-Host 'Disposable demo state reset. Previous database was backed up when present.'
