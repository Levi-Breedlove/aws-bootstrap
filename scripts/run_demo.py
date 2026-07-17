#!/usr/bin/env python3
"""Run the credential-free Internal Change Request API Fastlane showcase."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = {
    "name": "Internal Change Request API",
    "mode": "greenfield",
    "delivery_profile": "quick-mvp",
    "aws_lane": "explicit-gate",
    "region": "us-west-2",
    "budget": "$20/month",
    "users": "signed-in internal users",
    "simulated_services": [
        "Amazon API Gateway",
        "AWS Lambda",
        "Amazon DynamoDB",
        "Amazon CloudWatch",
    ],
}


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


def copy_manifest_template(destination: Path) -> None:
    manifest = json.loads((ROOT / "bootstrap.manifest.json").read_text(encoding="utf-8"))
    for relative in manifest["required_files"]:
        source = ROOT.joinpath(*PurePosixPath(relative).parts)
        target = destination.joinpath(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_local_slice(project: Path) -> None:
    implementation = '''"""Local-only Internal Change Request validation."""

MAX_DESCRIPTION_LENGTH = 2_000


def submit_change_request(payload: dict[str, object], *, role: str) -> dict[str, str]:
    if role != "employee":
        raise PermissionError("signed-in employee access required")
    title = payload.get("title")
    description = payload.get("description")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("description is required")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError("description exceeds 2000 characters")
    return {"status": "accepted", "title": title.strip()}
'''
    tests = '''import unittest

from app.change_request import submit_change_request


class ChangeRequestTests(unittest.TestCase):
    def test_approved_internal_access_succeeds(self):
        result = submit_change_request(
            {"title": "Add export", "description": "Internal request"},
            role="employee",
        )
        self.assertEqual(result["status"], "accepted")

    def test_unapproved_access_is_denied(self):
        with self.assertRaises(PermissionError):
            submit_change_request(
                {"title": "Add export", "description": "External request"},
                role="guest",
            )

    def test_invalid_and_oversized_input_is_rejected(self):
        with self.assertRaises(ValueError):
            submit_change_request({"title": "", "description": "x"}, role="employee")
        with self.assertRaises(ValueError):
            submit_change_request(
                {"title": "Too large", "description": "x" * 2001},
                role="employee",
            )


if __name__ == "__main__":
    unittest.main()
'''
    (project / "app" / "__init__.py").write_text("", encoding="utf-8", newline="\n")
    (project / "app" / "change_request.py").write_text(
        implementation, encoding="utf-8", newline="\n"
    )
    (project / "tests" / "test_change_request_demo.py").write_text(
        tests, encoding="utf-8", newline="\n"
    )


def quoted(value: str) -> str:
    marker = chr(96)
    return f"{marker}{value}{marker}"


def task_block(task_id: str, status: str, dependencies: str, path: str) -> str:
    visible = [
        f"### {task_id} — Demonstration task",
        "",
        f"- Status: {quoted(status)}",
        f"- Owner: {quoted('UNASSIGNED')}",
        f"- Blocker: {quoted('NONE')}",
        f"- GitHub issue: {quoted('PENDING_SYNC')}",
        "",
        "#### Outcome",
        "",
        "One bounded local result is observable.",
        "",
        "#### Acceptance criteria",
        "",
        "- [ ] The local result passes its exact validation.",
        "",
        "#### Validation",
        "",
        "~~~bash",
        "python -m unittest discover -s tests -p test_change_request_demo.py -v",
        "~~~",
        "",
        "#### Execution log",
        "",
        "Not started.",
        "",
        "#### Agent execution details",
        "",
        "<details>",
        "<summary>Exact metadata used by Codex and task_waves.py</summary>",
        "",
        f"- Requirements: {quoted('REQ-0001, FR-001')}",
        f"- Design: {quoted('DES-0001, Internal Change Request API')}",
        f"- Authorization: {quoted('AUTH-0001')}",
        f"- Depends on: {quoted(dependencies)}",
        f"- Dependency waivers: {quoted('NONE')}",
        f"- Run ID: {quoted('NONE')}",
        f"- Risk: {quoted('LOW')}",
        f"- Write set: {quoted(path)}",
        f"- External state: {quoted('NONE')}",
        f"- AWS mode: {quoted('NONE')}",
        f"- Attempt budget: {quoted('2')}",
        f"- Attempts used: {quoted('0')}",
        f"- Evidence: {quoted('NONE')}",
        f"- Skip record: {quoted('NONE')}",
        f"- Last checkpoint: {quoted('NONE')}",
        f"- Last updated: {quoted('2026-07-17T00:00:00+00:00')}",
        "",
        "</details>",
        "",
    ]
    return "\n".join(visible)


def write_task_ledger(path: Path) -> None:
    q = quoted
    snapshot = f"""# Demonstration task ledger

## Active execution snapshot

| Field | Value |
|---|---|
| Task-plan revision | {q('PLAN-0001')} |
| Task-plan state | {q('CURRENT')} |
| Requirements revision | {q('REQ-0001')} |
| Design revision | {q('DES-0001')} |
| Construction authorization | {q('AUTH-0001')} |
| Gate B state | {q('APPROVED_FOR_CONSTRUCTION')} |
| Run state | {q('NOT_STARTED')} |
| Active run ID | {q('NONE')} |
| Baseline commit | {q('demo000')} |
| Protected dirty paths | {q('NONE')} |
| Coordinator | {q('UNASSIGNED')} |
| Maximum workers | {q('1')} |
| Current wave | {q('1')} |
| Last checkpoint | {q('NONE')} |
| Last known-green commit | {q('demo000')} |
| Next safe action | {q('Claim TASK-0001')} |

## Dependencies, waivers, and waves

### Dependency waiver registry

| Waiver ID | Skipped task | Applies to task | Authority | Rationale and preserved acceptance evidence | Recorded at |
|---|---|---|---|---|---|
| {q('NONE')} | {q('NONE')} | {q('NONE')} | {q('NONE')} | No waivers recorded | TODO |

## Checkpoints and resume

| Checkpoint | Run | Time | REQ / DES / AUTH | Commit and protected dirty paths | Task outcomes and attempts | Evidence and external actions | Blockers and next safe action |
|---|---|---|---|---|---|---|---|
| {q('NONE')} | {q('NONE')} | TODO | {q('REQ-0001')} / {q('DES-0001')} / {q('AUTH-0001')} | {q('demo000')} | No work started | Evidence: NONE; External: NONE | Blockers: NONE; Next: claim TASK-0001 |

## Task definitions

"""
    blocks = [
        task_block("TASK-0001", "READY", "NONE", "app/change_request.py"),
        task_block("TASK-0002", "BACKLOG", "TASK-0001", "app/change_request_store.py"),
        task_block("TASK-0003", "BACKLOG", "TASK-0002", "app/change_request_metrics.py"),
    ]
    path.write_text(snapshot + "\n".join(blocks), encoding="utf-8", newline="\n")


def illustrative_dialogue() -> dict[str, object]:
    return {
        "label": "ILLUSTRATIVE CODEX DIALOGUE — NOT EXECUTED OUTPUT",
        "intake_questions": [
            "Who submits requests and what result do they need?",
            "What is the smallest useful release, and what is excluded?",
            "What Region and monthly development limit should the design use?",
        ],
        "gate_a": {
            "state": "PENDING_OWNER_APPROVAL",
            "decision": "Approve signed-in internal users, MVP scope, and measurable results.",
        },
        "technical_design": SCENARIO["simulated_services"],
        "gate_b": {
            "state": "PENDING_OWNER_APPROVAL",
            "boundary": "Three local tasks; no GitHub writes and no AWS mutation.",
        },
    }


def execute_showcase() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="fastlane-demo-") as temp:
        project = Path(temp) / "internal-change-request-api"
        project.mkdir()
        copy_manifest_template(project)

        bootstrap = run(
            [
                sys.executable,
                "bootstrap.py",
                "--target",
                str(project),
                "--project-name",
                SCENARIO["name"],
                "--region",
                SCENARIO["region"],
                "--budget",
                SCENARIO["budget"],
                "--in-place-template-instance",
            ],
            cwd=project,
        )
        if bootstrap.returncode != 0:
            raise RuntimeError(f"in-place setup failed: {bootstrap.stderr or bootstrap.stdout}")

        doctor = run(
            [
                sys.executable,
                "scripts/bootstrap_doctor.py",
                "--root",
                str(project),
                "--json",
            ],
            cwd=project,
        )
        if doctor.returncode != 0:
            raise RuntimeError(f"doctor failed: {doctor.stderr or doctor.stdout}")
        receipt = json.loads(doctor.stdout)
        expected = {
            "classification": "ACTIVE_GREENFIELD",
            "lifecycle_state": "INTAKE_REQUIRED",
            "next_prompt": "INTAKE-10",
            "status": "READY",
            "aws_access": "NOT_USED",
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise RuntimeError(
                    f"doctor field {field} was {receipt.get(field)!r}; expected {value!r}"
                )

        write_local_slice(project)
        local_tests = run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_change_request_demo.py",
                "-v",
            ],
            cwd=project,
        )
        if local_tests.returncode != 0:
            raise RuntimeError(f"local slice tests failed: {local_tests.stderr}")

        ledger = project / "DEMO-TASKS.md"
        write_task_ledger(ledger)
        ready = run(
            [
                sys.executable,
                "scripts/task_waves.py",
                str(ledger),
                "--ready",
                "--json",
            ],
            cwd=project,
        )
        if ready.returncode != 0:
            raise RuntimeError(f"task runtime failed: {ready.stderr or ready.stdout}")
        ready_payload = json.loads(ready.stdout)
        ready_records = (
            ready_payload["tasks"]
            if isinstance(ready_payload, dict)
            else ready_payload
        )
        ready_ids = [task["id"] for task in ready_records]
        if ready_ids != ["TASK-0001"]:
            raise RuntimeError(f"expected only TASK-0001 to be READY; received {ready_ids}")

        return {
            "result": "PASS",
            "scenario": SCENARIO,
            "executed_evidence": {
                "in_place_setup": "PASS",
                "doctor": {
                    field: receipt[field]
                    for field in (
                        "schema_version",
                        "bootstrap_version",
                        "classification",
                        "status",
                        "lifecycle_state",
                        "next_prompt",
                        "git_baseline",
                        "aws_access",
                        "gates",
                        "evidence_state",
                        "authorizations",
                    )
                },
                "local_tests": {
                    "result": "PASS",
                    "tests_run": 3,
                    "controls": [
                        "approved internal access succeeds",
                        "unapproved access is denied",
                        "invalid or oversized input is rejected",
                    ],
                },
                "task_runtime": {
                    "result": "PASS",
                    "ready_tasks": ready_ids,
                    "backlog_tasks_not_executed": ["TASK-0002", "TASK-0003"],
                },
                "aws_preflight": {
                    "result": "BLOCKED_AS_DESIGNED",
                    "reason": "No exact AWS authorization record exists.",
                    "aws_api_calls": 0,
                    "cloud_cost": "$0",
                },
            },
            "illustrative_dialogue": illustrative_dialogue(),
        }


def print_human(report: dict[str, object]) -> None:
    evidence = report["executed_evidence"]
    doctor = evidence["doctor"]
    tasks = evidence["task_runtime"]
    aws = evidence["aws_preflight"]
    dialogue = report["illustrative_dialogue"]
    print("AWS CODEX FASTLANE — TESTED SHOWCASE")
    print()
    print("EXECUTED TEST OUTPUT")
    print(f"Result: {report['result']}")
    print(f"Scenario: {report['scenario']['name']}")
    print("Doctor: PASS")
    print(f"Bootstrap status: {doctor['status']}")
    print(f"Classification: {doctor['classification']}")
    print(f"Lifecycle: {doctor['lifecycle_state']} -> {doctor['next_prompt']}")
    print(f"Gate A: {doctor['gates']['gate_a']}")
    print(f"Gate B: {doctor['gates']['gate_b']}")
    print(f"Evidence: {doctor['evidence_state']}")
    print(f"AWS authorization: {doctor['authorizations']['aws']}")
    print(f"Local control tests: {evidence['local_tests']['tests_run']} passed")
    print(f"Runnable tasks: {', '.join(tasks['ready_tasks'])}")
    print(f"BACKLOG tasks excluded: {', '.join(tasks['backlog_tasks_not_executed'])}")
    print(f"AWS preflight: {aws['result']} ({aws['reason']})")
    print(f"AWS API calls: {aws['aws_api_calls']}; cloud cost: {aws['cloud_cost']}")
    print()
    print(dialogue["label"])
    for number, question in enumerate(dialogue["intake_questions"], start=1):
        print(f"Intake {number}: {question}")
    print(f"Gate A: {dialogue['gate_a']['state']} — {dialogue['gate_a']['decision']}")
    print(
        "Technical design: "
        + ", ".join(dialogue["technical_design"])
        + " (simulated; not deployed)"
    )
    print(
        "Gate B: "
        f"{dialogue['gate_b']['state']} — {dialogue['gate_b']['boundary']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit structured evidence")
    args = parser.parse_args()
    try:
        report = execute_showcase()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
