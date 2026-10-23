$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path $python)) { $python = 'python' }
& $python (Join-Path $PSScriptRoot 'continuity.py') retomar
if ($LASTEXITCODE -ne 0) { throw 'Retomada encontrou uma pendência. Consulte a saída.' }
