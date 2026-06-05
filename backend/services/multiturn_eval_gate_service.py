"""Deterministic multi-turn evaluation gate for control-plane evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


MULTITURN_EVAL_GATE_VERSION = "multiturn-agent-evaluation-gate-v1"

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_BLOCKED = "blocked"


@dataclass(frozen=True)
class MultiTurnEvalGateService:
    """Evaluates local scenarios without invoking chat, tools, retrieval, or models."""

    def load_scenario(self, path: str | Path) -> Dict[str, Any]:
        scenario_path = Path(path)
        suffix = scenario_path.suffix.lower()
        text = scenario_path.read_text(encoding="utf-8")
        if suffix == ".json":
            return json.loads(text)
        if suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except ImportError as exc:  # pragma: no cover - optional dependency path
                raise ValueError("YAML scenario parsing requires PyYAML") from exc
            loaded = yaml.safe_load(text)
            return loaded if isinstance(loaded, dict) else {}
        raise ValueError(f"Unsupported scenario file type: {scenario_path.suffix}")

    def load_scenarios(self, directory: str | Path) -> List[Dict[str, Any]]:
        scenario_dir = Path(directory)
        scenarios: List[Dict[str, Any]] = []
        for path in sorted(scenario_dir.iterdir()):
            if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            scenario = self.load_scenario(path)
            scenario.setdefault("_source_path", str(path))
            scenarios.append(scenario)
        return scenarios

    def evaluate_directory(self, directory: str | Path) -> Dict[str, Any]:
        return self.build_report(self.evaluate_scenario(scenario) for scenario in self.load_scenarios(directory))

    def build_report(self, results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        result_list = list(results)
        status_counts: Dict[str, int] = {
            STATUS_PASSED: 0,
            STATUS_FAILED: 0,
            STATUS_SKIPPED: 0,
            STATUS_BLOCKED: 0,
        }
        for result in result_list:
            status = str(result.get("status") or STATUS_BLOCKED)
            status_counts[status] = status_counts.get(status, 0) + 1
        overall_status = STATUS_PASSED
        if status_counts[STATUS_BLOCKED]:
            overall_status = STATUS_BLOCKED
        elif status_counts[STATUS_FAILED]:
            overall_status = STATUS_FAILED
        return {
            "contract_version": MULTITURN_EVAL_GATE_VERSION,
            "execution_mode": "deterministic_contract_check",
            "overall_status": overall_status,
            "scenario_count": len(result_list),
            "status_counts": status_counts,
            "behavior_boundary": {
                "chat_execution_changed": False,
                "model_invocation": False,
                "tool_execution": False,
                "retrieval_invocation": False,
                "state_mutation": False,
            },
            "results": result_list,
        }

    def evaluate_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        scenario_id = str(scenario.get("id") or "").strip()
        base = {
            "contract_version": MULTITURN_EVAL_GATE_VERSION,
            "scenario_id": scenario_id or "unknown",
            "title": str(scenario.get("title") or ""),
            "execution_mode": "deterministic_contract_check",
            "assertions": [],
        }

        if scenario.get("enabled", True) is False:
            return {**base, "status": STATUS_SKIPPED, "reason": "scenario_disabled"}

        blocked_reason = self._blocked_reason(scenario)
        if blocked_reason:
            return {**base, "status": STATUS_BLOCKED, "reason": blocked_reason}

        evidence = scenario.get("evidence") or {}
        assertions = scenario.get("assertions") or {}
        assertion_results = self._evaluate_assertions(assertions, evidence)
        failed = [item for item in assertion_results if not item["passed"]]
        return {
            **base,
            "status": STATUS_FAILED if failed else STATUS_PASSED,
            "assertions": assertion_results,
            "failed_count": len(failed),
        }

    @staticmethod
    def _blocked_reason(scenario: Dict[str, Any]) -> Optional[str]:
        if not str(scenario.get("id") or "").strip():
            return "missing_scenario_id"
        turns = scenario.get("turns")
        if not isinstance(turns, list) or not turns:
            return "missing_turns"
        assertions = scenario.get("assertions")
        if not isinstance(assertions, dict) or not assertions:
            return "missing_assertions"
        evidence = scenario.get("evidence")
        if not isinstance(evidence, dict):
            return "missing_evidence"
        return None

    def _evaluate_assertions(self, assertions: Dict[str, Any], evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        results.extend(self._expected_values("grounding", assertions.get("grounding"), evidence.get("grounding")))
        results.extend(self._expected_values("promptops", assertions.get("promptops"), evidence.get("promptops")))
        results.extend(self._expected_values("memoryops", assertions.get("memoryops"), evidence.get("memoryops")))
        results.extend(self._expected_values("response", assertions.get("response"), evidence.get("response")))
        results.extend(self._expected_tool_results(assertions.get("tools"), evidence.get("tools")))
        return results

    def _expected_values(self, group: str, expected: Any, actual: Any) -> List[Dict[str, Any]]:
        if expected is None:
            return []
        if not isinstance(expected, dict):
            return [self._result(group, "", expected, actual, False, "invalid_expected_shape")]
        actual_dict = actual if isinstance(actual, dict) else {}
        return [
            self._result(group, key, expected_value, self._resolve_path(actual_dict, key), self._resolve_path(actual_dict, key) == expected_value)
            for key, expected_value in expected.items()
        ]

    def _expected_tool_results(self, expected: Any, actual: Any) -> List[Dict[str, Any]]:
        if expected is None:
            return []
        expected_tools = expected.get("expected_tool_names", []) if isinstance(expected, dict) else []
        actual_tools = actual.get("called_tool_names", []) if isinstance(actual, dict) else []
        expected_set = set(str(item) for item in expected_tools)
        actual_set = set(str(item) for item in actual_tools)
        return [
            self._result(
                "tools",
                "expected_tool_names",
                sorted(expected_set),
                sorted(actual_set),
                expected_set.issubset(actual_set),
            )
        ]

    @staticmethod
    def _resolve_path(payload: Dict[str, Any], path: str) -> Any:
        if path in payload:
            return payload.get(path)
        current: Any = payload
        for part in str(path).split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    @staticmethod
    def _result(
        group: str,
        path: str,
        expected: Any,
        actual: Any,
        passed: bool,
        reason: str = "",
    ) -> Dict[str, Any]:
        return {
            "group": group,
            "path": path,
            "expected": expected,
            "actual": actual,
            "passed": bool(passed),
            "reason": reason or ("matched" if passed else "mismatch"),
        }


_multiturn_eval_gate_service: Optional[MultiTurnEvalGateService] = None


def get_multiturn_eval_gate_service() -> MultiTurnEvalGateService:
    global _multiturn_eval_gate_service
    if _multiturn_eval_gate_service is None:
        _multiturn_eval_gate_service = MultiTurnEvalGateService()
    return _multiturn_eval_gate_service
