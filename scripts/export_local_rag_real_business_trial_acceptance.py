from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.local_rag_real_business_trial_acceptance import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QUESTION_REPORT_PATH,
    DEFAULT_UPLOAD_REPORT_PATH,
    export_local_rag_real_business_trial_acceptance,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export local RAG real business trial acceptance report.",
    )
    parser.add_argument("--upload-report-path", type=Path, default=DEFAULT_UPLOAD_REPORT_PATH)
    parser.add_argument(
        "--question-report-path",
        type=Path,
        action="append",
        dest="question_report_paths",
        help="Question trial report JSON path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--negative-question-report-path",
        type=Path,
        action="append",
        dest="negative_question_report_paths",
        help="Question trial report expected to return insufficient evidence. Can be passed multiple times.",
    )
    parser.add_argument("--source-id")
    parser.add_argument("--document-path")
    parser.add_argument("--provider-base-url")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    question_report_paths = list(args.question_report_paths or [DEFAULT_QUESTION_REPORT_PATH])
    expected_modes = {str(path): "answerable" for path in question_report_paths}
    for path in args.negative_question_report_paths or []:
        question_report_paths.append(path)
        expected_modes[str(path)] = "insufficient_evidence"

    report = export_local_rag_real_business_trial_acceptance(
        output_dir=args.output_dir,
        upload_report_path=args.upload_report_path,
        question_report_paths=question_report_paths,
        expected_modes=expected_modes,
        source_id=args.source_id,
        document_path=args.document_path,
        provider_base_url=args.provider_base_url,
    )
    print(f"Local RAG real business trial acceptance JSON ready: {report.json_path}")
    print(f"Local RAG real business trial acceptance Markdown ready: {report.markdown_path}")
    print(f"Decision: {report.decision}")
    print(f"Reason: {report.reason_code}")
    print(f"Follow-Up Area: {report.follow_up_area}")
    if args.pretty:
        print(json.dumps(local_report_to_dict(report), ensure_ascii=False, indent=2))
    return 0 if report.decision != "blocked" else 1


def local_report_to_dict(report):
    from backend.capability_runtime.local_rag_real_business_trial_acceptance import (
        local_rag_real_business_trial_acceptance_to_dict,
    )

    return local_rag_real_business_trial_acceptance_to_dict(report)


if __name__ == "__main__":
    raise SystemExit(main())
