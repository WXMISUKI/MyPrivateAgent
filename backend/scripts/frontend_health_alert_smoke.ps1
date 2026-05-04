param(
  [string]$FrontendDir = "frontend-vue"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-ExternalCommand {
  param(
    [string]$FilePath,
    [string[]]$ArgumentList
  )

  & $FilePath @ArgumentList
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    $argsText = ($ArgumentList | ForEach-Object { $_ }) -join " "
    throw "Command failed with exit code ${exitCode}: $FilePath $argsText"
  }
}

Write-Host "[smoke] run frontend health-alert tests..."
Push-Location $FrontendDir
try {
  Invoke-ExternalCommand "cmd" @(
    "/c",
    "npm",
    "test",
    "--",
    "--run",
    "src/components/__tests__/ChatView.test.js",
    "src/components/__tests__/SettingsView.test.js"
  )
} finally {
  Pop-Location
}
