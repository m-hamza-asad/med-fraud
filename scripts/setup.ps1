param(
  [string]$AdminPassword,
  [string]$AnalystPassword
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$BundledPython = 'C:\Users\Yoga 9\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python -and (Test-Path -LiteralPath $BundledPython)) { $Python = $BundledPython }
if (-not $Python) { throw 'Python 3.12 or 3.13 is required. No compatible system or Codex-bundled Python was found.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { & $Python -m venv .venv }
& '.\.venv\Scripts\python.exe' -m pip install --disable-pip-version-check -r requirements.txt
npm install --prefix apps/web
if (-not $AdminPassword) { $AdminPassword = Read-Host 'Initial admin password (12+ characters)' -MaskInput }
if (-not $AnalystPassword) { $AnalystPassword = Read-Host 'Initial analyst password (12+ characters)' -MaskInput }
$env:PYTHONPATH = Join-Path $ProjectRoot 'apps\api'
& '.\.venv\Scripts\python.exe' -m medfraud.cli init --admin-password $AdminPassword --analyst-password $AnalystPassword
& '.\.venv\Scripts\python.exe' scripts\generate_assets.py
Write-Host 'Setup complete. Run .\scripts\start.ps1'

