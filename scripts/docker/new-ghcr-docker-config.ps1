param(
    [string]$Username = "WXMISUKI",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $OutputPath.Trim()) {
    $OutputPath = Join-Path $env:TEMP "docker-ghcr-myprivateagent"
}

$pat = Read-Host "Paste GitHub PAT"
$auth = [Convert]::ToBase64String(
    [Text.Encoding]::ASCII.GetBytes("${Username}:$($pat.Trim())")
)

Remove-Item -LiteralPath $OutputPath -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

@"
{
  "auths": {
    "ghcr.io": {
      "auth": "$auth"
    }
  }
}
"@ | Set-Content -Encoding ASCII (Join-Path $OutputPath "config.json")

Remove-Variable pat -ErrorAction SilentlyContinue
Remove-Variable auth -ErrorAction SilentlyContinue

Write-Host "Docker config created: $OutputPath"
Write-Host "Use with: docker --config `"$OutputPath`" push ghcr.io/wxmisuki/myprivateagent-backend:latest"
Write-Host "Delete after use: Remove-Item `"$OutputPath`" -Recurse -Force"
