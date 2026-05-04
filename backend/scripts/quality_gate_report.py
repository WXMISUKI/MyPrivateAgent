"""Run the quality gate checks and emit a machine-readable report."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GateStep:
    name: str
    command: list[str]
    cwd: Path = ROOT_DIR


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run quality gate checks and write a summary report.")
    parser.add_argument("--output", type=str, default="quality-gate-report.json", help="JSON report path.")
    parser.add_argument("--summary", type=str, default="quality-gate-summary.md", help="Markdown summary path.")
    parser.add_argument("--window-days", type=int, default=14, choices=[0, 7, 14, 30])
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--max-open-actions", type=int, default=10)
    parser.add_argument("--max-long-blocked-actions", type=int, default=0)
    return parser


def _run_step(step: GateStep) -> dict[str, Any]:
    started_at = monotonic()
    completed = subprocess.run(
        step.command,
        cwd=str(step.cwd),
        capture_output=True,
        text=True,
    )
    duration_seconds = round(monotonic() - started_at, 3)
    return {
        "name": step.name,
        "command": " ".join(shlex.quote(part) for part in step.command),
        "cwd": str(step.cwd),
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "duration_seconds": duration_seconds,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _build_steps(args: argparse.Namespace) -> list[GateStep]:
    python = sys.executable
    if os.name == "nt":
        return [
            GateStep(
                "Quality gate smoke",
                [
                    "cmd",
                    "/c",
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "backend/scripts/quality_gate_smoke.ps1",
                    "-CondaEnv",
                    "myenv",
                ],
            )
        ]
    return [
        GateStep("Backend smoke_check.py", [python, "backend/scripts/smoke_check.py"]),
        GateStep("Backend auth_session_smoke.py", [python, "backend/scripts/auth_session_smoke.py"]),
        GateStep("Backend multi_agent_policy_smoke.py", [python, "backend/scripts/multi_agent_policy_smoke.py"]),
        GateStep("Backend multi_agent_provider_failover_smoke.py", [python, "backend/scripts/multi_agent_provider_failover_smoke.py"]),
        GateStep(
            "Backend governance regression tests",
            [
                python,
                "-m",
                "unittest",
                "tests.agent_framework.test_doctor_script",
                "tests.agent_framework.test_health_router",
                "tests.agent_framework.test_runtime_surface_config_service",
            ],
        ),
        GateStep(
            "Backend capability-gap governance smoke",
            [
                python,
                "backend/scripts/capability_gap_governance_smoke.py",
                "--window-days",
                str(args.window_days),
                "--limit",
                str(args.limit),
                "--max-open-actions",
                str(args.max_open_actions),
                "--max-long-blocked-actions",
                str(args.max_long_blocked_actions),
            ],
        ),
        GateStep(
            "Frontend health-alert smoke",
            [
                "npm",
                "test",
                "--",
                "--run",
                "src/components/__tests__/ChatView.test.js",
                "src/components/__tests__/SettingsView.test.js",
            ],
            cwd=ROOT_DIR / "frontend-vue",
        ),
    ]


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Quality Gate Report",
        "",
        f"- Status: {'PASS' if report['passed'] else 'FAIL'}",
        f"- Steps: {report['step_count']}",
        f"- Failed: {len(report['failed_steps'])}",
        "",
        "| Step | Status | Exit | Seconds |",
        "| --- | --- | ---: | ---: |",
    ]
    for step in report["steps"]:
        status = "PASS" if step["passed"] else "FAIL"
        lines.append(
            f"| {step['name']} | {status} | {step['exit_code']} | {step['duration_seconds']} |"
        )
    if report["failed_steps"]:
        lines.append("")
        lines.append("## Failed Steps")
        for step in report["failed_steps"]:
            lines.append(f"- {step['name']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    steps = [_run_step(step) for step in _build_steps(args)]
    failed_steps = [step for step in steps if not step["passed"]]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root_dir": str(ROOT_DIR),
        "python": sys.executable,
        "platform": sys.platform,
        "passed": len(failed_steps) == 0,
        "step_count": len(steps),
        "failed_steps": [{"name": step["name"], "exit_code": step["exit_code"]} for step in failed_steps],
        "steps": steps,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(_render_summary(report), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
