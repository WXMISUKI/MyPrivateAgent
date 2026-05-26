param(
    [string]$PythonImage = "python:3.11-slim",
    [string]$PipIndexUrl = "https://pypi.tuna.tsinghua.edu.cn/simple",
    [string]$PipTrustedHost = "pypi.tuna.tsinghua.edu.cn",
    [switch]$Clear
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$wheelhouse = Join-Path $repoRoot ".docker\wheelhouse\backend"

if ($Clear -and (Test-Path -LiteralPath $wheelhouse)) {
    Remove-Item -LiteralPath $wheelhouse -Recurse -Force
}
New-Item -ItemType Directory -Path $wheelhouse -Force | Out-Null

$pipFlags = "-i $PipIndexUrl"
if ($PipTrustedHost.Trim()) {
    $pipFlags = "$pipFlags --trusted-host $PipTrustedHost"
}

$downloadCommand = @"
set -eux
python -m pip install --upgrade pip $pipFlags
python -m pip download -r /src/backend/requirements.txt -d /wheelhouse $pipFlags
"@

docker run --rm `
    -v "${repoRoot}:/src" `
    -v "${wheelhouse}:/wheelhouse" `
    $PythonImage `
    sh -c $downloadCommand

Write-Host "Wheelhouse prepared: $wheelhouse"
