param(
    [Parameter(Mandatory = $true)][string]$SourceArchive,
    [Parameter(Mandatory = $true)][string]$Python,
    [string]$NodeVersion = '24.22.1'
)
$ErrorActionPreference = 'Stop'
if ($NodeVersion -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid Node version' }
$qaRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('eletroprojeto-windows-qa-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $qaRoot | Out-Null
$archiveName = "node-v$NodeVersion-win-x64.zip"
$download = Join-Path $qaRoot $archiveName
Invoke-WebRequest -UseBasicParsing "https://nodejs.org/dist/v$NodeVersion/$archiveName" -OutFile $download
$checksums = (Invoke-WebRequest -UseBasicParsing "https://nodejs.org/dist/v$NodeVersion/SHASUMS256.txt").Content
$expected = (($checksums -split "`n") | Where-Object { $_.Trim().EndsWith(" $archiveName") }) -split '\s+'
if (-not $expected -or (Get-FileHash $download -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[0].ToLowerInvariant()) { throw 'Node checksum mismatch' }
Expand-Archive $download (Join-Path $qaRoot 'node')
$nodeHome = Join-Path $qaRoot "node\node-v$NodeVersion-win-x64"
$env:PATH = "$nodeHome;$env:PATH"
$env:ELETROPROJETO_PYTHON = $Python
$env:AUTH_MODE = 'local'
$env:NEXT_PUBLIC_AUTH_MODE = 'local'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
$source = Join-Path $qaRoot 'source'
Expand-Archive $SourceArchive $source
Set-Location (Join-Path $source 'frontend')
$node = Join-Path $nodeHome 'node.exe'
$npmCli = Join-Path $nodeHome 'node_modules\npm\bin\npm-cli.js'
function Run-Npm {
    param([string[]]$Arguments)
    & $node $npmCli @Arguments
    if ($LASTEXITCODE -ne 0) { throw "npm QA failed: $Arguments" }
}
Run-Npm -Arguments @('ci')
Run-Npm -Arguments @('run', 'types:sync')
Run-Npm -Arguments @('run', 'typecheck')
Run-Npm -Arguments @('test')
& $node (Join-Path $source 'frontend\node_modules\@playwright\test\cli.js') install chromium
if ($LASTEXITCODE -ne 0) { throw 'Browser install failed' }
Run-Npm -Arguments @('run', 'test:e2e')
Run-Npm -Arguments @('run', 'build:webpack')
Write-Output "Windows QA passed. Isolated artifacts: $qaRoot"
