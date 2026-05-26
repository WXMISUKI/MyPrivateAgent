param(
    [string]$ImageName = "ghcr.io/wxmisuki/myprivateagent-backend",
    [string]$Tag = "latest",
    [ValidateSet("auto", "offline", "online")]
    [string]$InstallMode = "auto",
    [string]$PipIndexUrl = "https://pypi.tuna.tsinghua.edu.cn/simple",
    [string]$PipTrustedHost = "pypi.tuna.tsinghua.edu.cn",
    [string]$DockerConfig = "",
    [switch]$PrepareOnly,
    [switch]$Push
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$imageRef = "${ImageName}:$Tag"
$contextRoot = Join-Path $env:TEMP "myprivateagent-docker-build-context"

function Copy-WithRobocopy {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$ExcludeDirs = @(),
        [string[]]$ExcludeFiles = @()
    )

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $args = @($Source, $Destination, "/E")
    if ($ExcludeDirs.Count -gt 0) {
        $args += "/XD"
        $args += $ExcludeDirs
    }
    if ($ExcludeFiles.Count -gt 0) {
        $args += "/XF"
        $args += $ExcludeFiles
    }
    robocopy @args | Out-Host
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

Remove-Item -LiteralPath $contextRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $contextRoot -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot "Dockerfile") -Destination (Join-Path $contextRoot "Dockerfile")
Copy-WithRobocopy `
    -Source (Join-Path $repoRoot "backend") `
    -Destination (Join-Path $contextRoot "backend") `
    -ExcludeDirs @("__pycache__", "pytest-cache-files-1x_nnsdg") `
    -ExcludeFiles @("*.pyc")
Copy-WithRobocopy `
    -Source (Join-Path $repoRoot ".docker\wheelhouse") `
    -Destination (Join-Path $contextRoot ".docker\wheelhouse")

if ($PrepareOnly) {
    Write-Host "Docker build context prepared: $contextRoot"
    exit 0
}

$dockerPrefix = @()
if ($DockerConfig.Trim()) {
    $dockerPrefix += @("--config", $DockerConfig)
}

$buildArgs = @(
    "build",
    "--build-arg", "PIP_INDEX_URL=$PipIndexUrl",
    "--build-arg", "PIP_TRUSTED_HOST=$PipTrustedHost",
    "--build-arg", "INSTALL_FROM_WHEELHOUSE=$InstallMode",
    "-t", $imageRef,
    $contextRoot
)

docker @dockerPrefix @buildArgs

if ($Push) {
    docker @dockerPrefix push $imageRef
}

Write-Host "Image ready: $imageRef"
