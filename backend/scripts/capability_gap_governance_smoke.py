"""Deterministic governance smoke that validates doctor gate on seeded benchmark data."""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from database import Base
    from models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus, User
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.database import Base
    from backend.models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus, User

from backend.scripts import doctor


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run capability-gap governance smoke against deterministic seeded benchmark data.",
    )
    parser.add_argument("--window-days", type=int, default=14, choices=[0, 7, 14, 30])
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--max-open-actions", type=int, default=10)
    parser.add_argument("--max-long-blocked-actions", type=int, default=0)
    return parser


def _timestamp(minutes_offset: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_offset)).isoformat().replace("+00:00", "Z")


def _trace_event(
    event_type: str,
    *,
    profile: str,
    provider: str = "volcengine-ark",
    model_name: str = "doubao",
    source: str | None = None,
    minutes_offset: int = 0,
    missing_parts: list[str] | None = None,
    error_category: str | None = None,
    agent_role: str | None = None,
) -> dict:
    payload = {
        "profile": profile,
        "provider": provider,
        "model_name": model_name,
    }
    if missing_parts is not None:
        payload["missing_parts"] = list(missing_parts)
        payload["completion_stage"] = "boundary_fallback"
    if error_category is not None:
        payload["error_category"] = error_category
    if agent_role is not None:
        payload["agent_role"] = agent_role
    event = {
        "event_type": event_type,
        "timestamp": _timestamp(minutes_offset),
        "payload": payload,
        "summary": f"benchmark:{event_type}",
        "detail": f"profile={profile}",
    }
    if source:
        event["source"] = source
    return event


def _seed_plan_item(session, *, user_id: int, objective: str, title: str, run_trace: list[dict]) -> None:
    plan = PlanRunRecord(
        user_id=user_id,
        objective=objective,
        source="smoke",
        status=PlanStatus.COMPLETED,
        summary="seeded governance benchmark plan",
        plan_metadata={"seeded": True},
    )
    session.add(plan)
    session.flush()
    session.add(
        PlanItemRecord(
            plan_id=plan.id,
            step_order=1,
            title=title,
            details="seeded benchmark trace",
            status=PlanStatus.COMPLETED,
            handoff_status=PlanHandoffStatus.MERGED,
            item_metadata={"run_trace": run_trace, "seeded": True},
        )
    )


def _seed_benchmark_dataset(session) -> None:
    user = User(username="governance_smoke", password_hash="smoke")
    session.add(user)
    session.flush()

    travel_trace = [
        _trace_event("tool_called", profile="travel_planning", minutes_offset=10),
        _trace_event("completion_retry", profile="travel_planning", minutes_offset=9),
        _trace_event(
            "capability_gap_fallback",
            profile="travel_planning",
            minutes_offset=8,
            missing_parts=["transport", "play"],
        ),
        _trace_event(
            "tool_failed",
            profile="travel_planning",
            minutes_offset=7,
            error_category="provider_timeout",
        ),
        _trace_event("completion_finalized", profile="travel_planning", minutes_offset=6),
    ]
    planning_trace = [
        _trace_event("tool_called", profile="planning", minutes_offset=5),
        _trace_event(
            "capability_gap_fallback",
            profile="planning",
            minutes_offset=4,
            missing_parts=["transport"],
        ),
        _trace_event(
            "pre_tool_use_blocked",
            profile="planning",
            source="hook",
            minutes_offset=3,
        ),
        _trace_event("completion_finalized", profile="planning", minutes_offset=2),
    ]
    research_trace = [
        _trace_event("tool_called", profile="research_compare", minutes_offset=5),
        _trace_event("completion_retry", profile="research_compare", minutes_offset=4),
        _trace_event(
            "child_completed",
            profile="research_compare",
            source="subagent",
            minutes_offset=3,
            agent_role="researcher",
        ),
        _trace_event("completion_finalized", profile="research_compare", minutes_offset=1),
    ]

    _seed_plan_item(
        session,
        user_id=user.id,
        objective="travel governance benchmark",
        title="travel benchmark item",
        run_trace=travel_trace,
    )
    _seed_plan_item(
        session,
        user_id=user.id,
        objective="planning governance benchmark",
        title="planning benchmark item",
        run_trace=planning_trace,
    )
    _seed_plan_item(
        session,
        user_id=user.id,
        objective="research governance benchmark",
        title="research benchmark item",
        run_trace=research_trace,
    )
    session.commit()


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        Base.metadata.create_all(bind=engine)

        session = session_factory()
        try:
            _seed_benchmark_dataset(session)
        finally:
            session.close()

        output = io.StringIO()
        with patch.object(doctor, "SessionLocal", session_factory):
            with redirect_stdout(output):
                code = doctor.main(
                    [
                        "--capability-gaps",
                        "--window-days",
                        str(args.window_days),
                        "--limit",
                        str(args.limit),
                        "--max-open-actions",
                        str(args.max_open_actions),
                        "--max-long-blocked-actions",
                        str(args.max_long_blocked_actions),
                    ]
                )

        payload = json.loads(output.getvalue())
        if code != 0:
            raise AssertionError(f"doctor gate should pass on seeded benchmark dataset: {payload}")
        if not payload.get("gate_passed"):
            raise AssertionError(f"governance gate reported failure on seeded benchmark dataset: {payload}")
        if payload.get("missing_profiles"):
            raise AssertionError(f"seeded benchmark dataset still has missing profiles: {payload}")
        if float(payload.get("catalog_coverage_ratio") or 0.0) < float(payload.get("catalog_coverage_threshold") or 0.0):
            raise AssertionError(f"catalog coverage below threshold: {payload}")
    finally:
        engine.dispose()

    print("PASS: capability_gap_governance_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
