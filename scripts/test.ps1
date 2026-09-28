$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONPATH = Join-Path $ProjectRoot 'apps\api'
& '.\.venv\Scripts\python.exe' -m pytest
if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
& '.\.venv\Scripts\python.exe' -m compileall -q apps\api scripts tests\backend
if ($LASTEXITCODE -ne 0) { throw 'Python compile check failed.' }
npm --prefix apps/web run test
if ($LASTEXITCODE -ne 0) { throw 'Frontend unit tests failed.' }
npm --prefix apps/web run typecheck
if ($LASTEXITCODE -ne 0) { throw 'Frontend type check failed.' }
npm --prefix apps/web run lint
if ($LASTEXITCODE -ne 0) { throw 'Frontend lint failed.' }
npm --prefix apps/web run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend production build failed.' }
