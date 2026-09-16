param([Parameter(Mandatory=$true)][string]$Source)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Database = Join-Path $ProjectRoot 'data\local\medfraud.sqlite3'
$ProcessState = Join-Path $ProjectRoot 'data\local\processes.json'
if (Test-Path -LiteralPath $ProcessState) { throw 'Stop the application with scripts\stop.ps1 before restore so SQLite is not replaced while open.' }
$ResolvedSource = (Resolve-Path -LiteralPath $Source).Path
& '.\.venv\Scripts\python.exe' 'scripts\verify_db.py' $ResolvedSource schema
if (Test-Path -LiteralPath $Database) { Copy-Item -LiteralPath $Database -Destination (Join-Path $ProjectRoot ('data\backups\pre-restore-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sqlite3')) }
$Temporary = Join-Path $ProjectRoot 'data\local\restore-candidate.sqlite3'
Copy-Item -LiteralPath $ResolvedSource -Destination $Temporary
if (Test-Path -LiteralPath $Database) {
  [System.IO.File]::Move($Temporary, $Database, $true)
} else {
  Move-Item -LiteralPath $Temporary -Destination $Database
}
Write-Host 'Restore completed; the prior active database was backed up.'
