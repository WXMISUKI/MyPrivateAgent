param(
  [string]$CondaEnv = "myenv",
  [int]$GovernanceWindowDays = 14,
  [int]$GovernanceLimit = 200,
  [int]$MaxOpenActions = 10,
  [int]$MaxLongBlockedActions = 0
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

function Run-Step {
  param(
    [string]$Name,
    [scriptblock]$Action
  )
  Write-Host ""
  Write-Host "==> $Name"
  & $Action
}

Run-Step "Backend smoke_check.py" {
  Invoke-ExternalCommand "conda" @("run", "-n", $CondaEnv, "python", "backend/scripts/smoke_check.py")
}

Run-Step "Backend auth_session_smoke.py" {
  Invoke-ExternalCommand "conda" @("run", "-n", $CondaEnv, "python", "backend/scripts/auth_session_smoke.py")
}

Run-Step "Backend multi_agent_policy_smoke.py" {
  Invoke-ExternalCommand "conda" @("run", "-n", $CondaEnv, "python", "backend/scripts/multi_agent_policy_smoke.py")
}

Run-Step "Backend multi_agent_provider_failover_smoke.py" {
  Invoke-ExternalCommand "conda" @("run", "-n", $CondaEnv, "python", "backend/scripts/multi_agent_provider_failover_smoke.py")
}

Run-Step "Backend runtime_contract_smoke.py" {
  Invoke-ExternalCommand "conda" @("run", "-n", $CondaEnv, "python", "backend/scripts/runtime_contract_smoke.py")
}

Run-Step "Backend governance regression tests" {
  Invoke-ExternalCommand "conda" @(
    "run",
    "-n",
    $CondaEnv,
    "python",
    "-m",
    "unittest",
    "tests.agent_framework.test_doctor_script",
    "tests.agent_framework.test_health_router",
    "tests.agent_framework.test_runtime_contract_smoke",
    "tests.agent_framework.test_runtime_surface_config_service"
  )
}

Run-Step "Backend capability-gap governance smoke" {
  Invoke-ExternalCommand "conda" @(
    "run",
    "-n",
    $CondaEnv,
    "python",
    "backend/scripts/capability_gap_governance_smoke.py",
    "--window-days",
    $GovernanceWindowDays.ToString(),
    "--limit",
    $GovernanceLimit.ToString(),
    "--max-open-actions",
    $MaxOpenActions.ToString(),
    "--max-long-blocked-actions",
    $MaxLongBlockedActions.ToString()
  )
}

Run-Step "Frontend health-alert smoke" {
  Invoke-ExternalCommand "powershell" @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    "backend/scripts/frontend_health_alert_smoke.ps1"
  )
}

Write-Host ""
Write-Host "PASS: quality_gate_smoke"
