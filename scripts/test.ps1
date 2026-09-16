$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONPATH = Join-Path $ProjectRoot 'apps\api'
& '.\.venv\Scripts\python.exe' -m pytest
& '.\.venv\Scripts\python.exe' -m compileall -q apps\api scripts tests\backend
npm --prefix apps/web run test
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run build
