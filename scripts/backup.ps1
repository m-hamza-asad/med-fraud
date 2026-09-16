param([string]$Destination)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Database = Join-Path $ProjectRoot 'data\local\medfraud.sqlite3'
if (-not (Test-Path -LiteralPath $Database)) { throw 'No active database exists.' }
if (-not $Destination) { $Destination = Join-Path $ProjectRoot ('data\backups\medfraud-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sqlite3') }
Copy-Item -LiteralPath $Database -Destination $Destination
& '.\.venv\Scripts\python.exe' 'scripts\verify_db.py' $Destination
Write-Host "Verified backup: $Destination"
