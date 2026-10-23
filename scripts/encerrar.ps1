param([switch]$ForceNew)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$candidates = @((Join-Path $root 'backend/.venv-windows/Scripts/python.exe'), (Join-Path $root 'backend/.venv/Scripts/python.exe'))
$python = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) { $python = 'python' }
$arguments = @((Join-Path $PSScriptRoot 'continuity.py'), 'encerrar')
if ($ForceNew) { $arguments += '--force-new' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Continuidade falhou. Consulte a saída; não assumir ponto verificado.' }
