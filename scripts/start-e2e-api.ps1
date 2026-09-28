$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONPATH = Join-Path $ProjectRoot 'apps\api'
$env:MEDFRAUD_DATA_DIR = Join-Path $ProjectRoot '.test-artifacts\e2e-data'
New-Item -ItemType Directory -Path $env:MEDFRAUD_DATA_DIR -Force | Out-Null
& '.\.venv\Scripts\python.exe' -m medfraud.cli init --admin-password 'E2e-Admin-Password-2026!' --analyst-password 'E2e-Analyst-Password-2026!'
& '.\.venv\Scripts\python.exe' -m uvicorn medfraud.main:app --host 127.0.0.1 --port 8010
