from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


task_waves = load_module(
    "task_waves_under_test",
    REPOSITORY_ROOT / "scripts" / "task_waves.py",
)


def snapshot(
    *,
    task_plan: str = "PLAN-0001",
    task_plan_state: str = "CURRENT",
    gate_b: str = "APPROVED_FOR_CONSTRUCTION",
    run_state: str = "NOT_STARTED",
    run_id: str = "NONE",
    coordinator: str = "UNASSIGNED",
    maximum_workers: int = 2,
    current_wave: str = "1",
    protected_dirty_paths: str = "NONE",
    baseline_commit: str = "abc1234",
    last_known_green_commit: str = "abc1234",
    last_checkpoint: str = "NONE",
) -> str:
    return f"""## Active execution snapshot

| Field | Value |
|---|---|
| Task-plan revision | `{task_plan}` |
| Task-plan state | `{task_plan_state}` |
| Requirements revision | `REQ-0001` |
| Design revision | `DES-0001` |
| Construction authorization | `AUTH-0001` |
| Gate B state | `{gate_b}` |
| Run state | `{run_state}` |
| Active run ID | `{run_id}` |
| Baseline commit | `{baseline_commit}` |
| Protected dirty paths | `{protected_dirty_paths}` |
| Coordinator | `{coordinator}` |
| Maximum workers | `{maximum_workers}` |
| Current wave | `{current_wave}` |
| Last checkpoint | `{last_checkpoint}` |
| Last known-green commit | `{last_known_green_commit}` |
| Next safe action | `Claim a ready task` |

"""


def task_block(
    task_id: str,
    status: str,
    dependencies: str = "NONE",
    *,
    waivers: str = "NONE",
    owner: str | None = None,
    run_id: str | None = None,
    write_set: str | None = None,
    external_state: str = "NONE",
    aws_mode: str = "NONE",
    attempt_budget: int = 2,
    attempts_used: int | None = None,
    evidence: str | None = None,
    blocker: str | None = None,
    skip_record: str | None = None,
    checkpoint: str | None = None,
    authorization: str = "AUTH-0001",
) -> str:
    owner = owner or ("worker-1" if status == "IN_PROGRESS" else "UNASSIGNED")
    run_id = run_id or ("RUN-0001" if status == "IN_PROGRESS" else "NONE")
    attempts_used = attempts_used if attempts_used is not None else (
        1 if status == "IN_PROGRESS" else 0
    )
    evidence = evidence or ("EV-0001" if status == "DONE" else "NONE")
    blocker = blocker or (
        "Dependency unavailable; obtain fixture" if status == "BLOCKED" else "NONE"
    )
    skip_record = skip_record or (
        "SKIP-001" if status == "SKIPPED" else "NONE"
    )
    checkpoint = checkpoint or ("CP-0001" if status == "IN_PROGRESS" else "NONE")
    write_set = write_set or f"app/{task_id.lower()}.py"
    return f"""### {task_id} — Test task

- Status: `{status}`
- Requirements: `REQ-0001, FR-001`
- Design: `DES-0001, Section 10`
- Authorization: `{authorization}`
- Depends on: `{dependencies}`
- Dependency waivers: `{waivers}`
- Owner: `{owner}`
- Run ID: `{run_id}`
- Risk: `LOW`
- Write set: `{write_set}`
- External state: `{external_state}`
- AWS mode: `{aws_mode}`
- Attempt budget: `{attempt_budget}`
- Attempts used: `{attempts_used}`
- Evidence: `{evidence}`
- Blocker: `{blocker}`
- Skip record: `{skip_record}`
- GitHub issue: `PENDING_SYNC`
- Last checkpoint: `{checkpoint}`
- Last updated: `2026-07-17T00:00:00+00:00`

#### Outcome

The task's bounded behavior is implemented and observable.

#### Acceptance criteria

- [{'x' if status == 'DONE' else ' '}] The observable task result matches its requirement.

#### Validation

```bash
python -m unittest
```

#### Execution log

{'2026-07-17T00:00:00+00:00 coordinator observed validation pass.' if status == 'DONE' else 'Not started.'}

"""


def document(
    blocks: list[str],
    *,
    snapshot_text: str | None = None,
    waiver_rows: list[str] | None = None,
    checkpoint_rows: list[str] | None = None,
) -> str:
    waiver_rows = waiver_rows or []
    rows = "\n".join(waiver_rows) or "| `NONE` | `NONE` | `NONE` | `NONE` | No waivers recorded | TODO |"
    checkpoint_content = "\n".join(checkpoint_rows or []) or (
        "| `NONE` | `NONE` | TODO | `REQ-0001` / `DES-0001` / `AUTH-0001` | "
        "TODO | No work started | Evidence: NONE; External: NONE | "
        "Blockers: NONE; Next: start run |"
    )
    return (
        "# Tasks\n\n"
        + (snapshot_text or snapshot())
        + "## Dependencies, waivers, and waves\n\n"
        + "### Dependency waiver registry\n\n"
        + "| Waiver ID | Skipped task | Applies to task | Authority | Rationale and preserved acceptance evidence | Recorded at |\n"
        + "|---|---|---|---|---|---|\n"
        + rows
        + "\n\n## Checkpoints and resume\n\n"
        + "| Checkpoint | Run | Time | REQ / DES / AUTH | Commit and protected dirty paths | Task outcomes and attempts | Evidence and external actions | Blockers and next safe action |\n"
        + "|---|---|---|---|---|---|---|---|\n"
        + checkpoint_content
        + "\n\n## Task definitions\n\n"
        + "".join(blocks)
    )


def parse_document(text: str):
    tasks = task_waves.parse_tasks(text)
    snap = task_waves.parse_snapshot(text)
    waivers = task_waves.parse_waivers(text)
    by_id = task_waves.validate(tasks, snap, waivers)
    return tasks, snap, waivers, by_id


def write_matching_state(root: Path, tasks_text: str) -> Path:
    state = json.loads(
        (REPOSITORY_ROOT / "bootstrap.yaml").read_text(encoding="utf-8")
    )
    snap = task_waves.parse_snapshot(tasks_text)
    tasks = task_waves.parse_tasks(tasks_text)
    state["lifecycle"].update(
        {
            "requirements_revision": snap.get("Requirements revision"),
            "design_revision": snap.get("Design revision"),
            "construction_authorization": snap.get("Construction authorization"),
            "gate_a": "APPROVED_FOR_DESIGN",
            "gate_b": snap.get("Gate B state"),
        }
    )
    plan = snap.get("Task-plan revision")
    state_map = {
        "NOT_STARTED": "IDLE",
        "RUNNING": "RUNNING",
        "PAUSED": "CHECKPOINTED",
        "BLOCKED": "BLOCKED",
        "COMPLETE": "COMPLETE",
    }
    execution_state = state_map[snap.get("Run state")]
    checkpoint = snap.get("Last checkpoint")
    state["execution"].update(
        {
            "plan_revision": None if plan == "UNINITIALIZED" else plan,
            "plan_state": snap.get("Task-plan state"),
            "run_id": None if snap.get("Active run ID") == "NONE" else snap.get("Active run ID"),
            "coordinator": None
            if snap.get("Coordinator") in {"NONE", "UNASSIGNED"}
            else snap.get("Coordinator"),
            "mode": "NONE" if execution_state == "IDLE" else "AUTONOMOUS",
            "state": execution_state,
            "basis": None
            if execution_state == "IDLE"
            else {
                "requirements_revision": snap.get("Requirements revision"),
                "design_revision": snap.get("Design revision"),
                "construction_authorization": snap.get("Construction authorization"),
            },
            "active_tasks": sorted(
                task.task_id for task in tasks if task.status == "IN_PROGRESS"
            ),
            "attempts": {task.task_id: task.attempts_used for task in tasks},
            "last_checkpoint": None
            if execution_state == "IDLE" or checkpoint == "NONE"
            else {
                "id": checkpoint,
                "at": "2026-07-17T00:00:00+00:00",
                "evidence_ref": f"VERIFY.md#{checkpoint.lower()}",
            },
        }
    )
    path = root / "bootstrap.yaml"
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def write_task_project(root: Path, tasks_text: str) -> tuple[Path, Path]:
    tasks_path = root / "TASKS.md"
    tasks_path.write_text(tasks_text, encoding="utf-8")
    return tasks_path, write_matching_state(root, tasks_text)


def observed_task_text(text: str, *, count: int = 1) -> str:
    for _index in range(count):
        text = text.replace("- [ ]", "- [x]", 1)
        text = text.replace(
            "Not started.",
            "2026-07-17T00:00:00+00:00 coordinator observed validation pass.",
            1,
        )
    return text


def checkpoint_row(
    checkpoint_id: str,
    *,
    commit: str = "abc1234",
    dirty: str = "NONE",
    outcomes: str = "TASK-001 DONE attempts=1/2",
    evidence: str = "EV-0001",
    next_action: str = "resume or complete",
) -> str:
    return (
        f"| `{checkpoint_id}` | `RUN-0001` | 2026-07-17T00:00:00+00:00 | "
        f"`REQ-0001` / `DES-0001` / `AUTH-0001` | Commit: `{commit}`; Dirty: {dirty} | "
        f"{outcomes} | Evidence: {evidence}; External: NONE | "
        f"Blockers: NONE; Next: {next_action} |"
    )


def completion_evidence_row(
    *,
    evidence_id: str = "EV-0001",
    task_id: str = "TASK-001",
    command_or_observation: str = "python -m unittest tests.test_task_waves",
    result: str = "exit=0; 37 tests passed",
    actor: str = "codex-coordinator",
    observed_at: str = "2026-07-17T00:00:00+00:00",
    material: str = "Commit: abc1234",
    durable_source: str = "VERIFY.md#ev-0001",
    status: str = "LOCAL_PASS",
) -> str:
    return (
        f"| `{evidence_id}` | `{task_id}` | {command_or_observation} | {result} | "
        f"`{actor}` | {observed_at} | {material} | {durable_source} | `{status}` |"
    )


def completion_evidence_document(*rows: str) -> str:
    content = rows or (completion_evidence_row(),)
    return (
        "# Verification\n\n"
        "## Task completion evidence\n\n"
        "| Evidence ID | Task | Command or observation | Result | Actor | Observed at | Commit / worktree / artifact | Durable source | Status |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        + "\n".join(content)
        + "\n"
    )


def append_checkpoint(tasks_text: str, row: str) -> str:
    marker = "\n\n## Task definitions\n\n"
    if marker not in tasks_text:
        raise AssertionError("Task definitions marker is missing")
    return tasks_text.replace(marker, "\n" + row + marker, 1)


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def initialize_git(root: Path) -> str:
    git(root, "init", "-q")
    git(root, "config", "user.email", "tests@example.com")
    git(root, "config", "user.name", "Fastlane Tests")
    marker = root / "base.txt"
    marker.write_text("base\n", encoding="utf-8")
    git(root, "add", "base.txt")
    git(root, "commit", "-qm", "base")
    return git(root, "rev-parse", "HEAD")


class TaskWaveSafetyTests(unittest.TestCase):
    def test_canonical_project_ledger_resolves_root_state_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks_path = root / "docs" / "project" / "TASKS.md"
            tasks_path.parent.mkdir(parents=True)
            state_path = root / "bootstrap.yaml"
            state_path.write_text(
                json.dumps({"lifecycle": {}, "execution": {}}),
                encoding="utf-8",
            )

            observed_state_path, _state = task_waves.read_bootstrap_state(tasks_path)

            self.assertEqual(observed_state_path, state_path.resolve())
            self.assertEqual(task_waves.project_root_for_tasks(tasks_path), root.resolve())
            self.assertEqual(
                task_waves.coordinator_ledger_paths(tasks_path),
                {
                    "bootstrap.yaml",
                    "docs/project/TASKS.md",
                    "docs/project/VERIFY.md",
                },
            )
            self.assertEqual(
                task_waves.canonical_verify_reference(tasks_path, "cp-0001"),
                "docs/project/VERIFY.md#cp-0001",
            )

    def test_ready_selects_only_explicit_ready_tasks(self) -> None:
        text = document(
            [
                task_block("TASK-001", "BACKLOG"),
                task_block("TASK-002", "READY"),
                task_block("TASK-003", "DONE"),
                task_block("TASK-004", "READY", "TASK-001"),
            ]
        )
        tasks, _snap, waivers, by_id = parse_document(text)

        selected = task_waves.ready_tasks(tasks, by_id, waivers)

        self.assertEqual([task.task_id for task in selected], ["TASK-002"])

    def test_human_first_collapsed_metadata_remains_parser_compatible(self) -> None:
        block = """### TASK-9001 - Human-first task

- Status: `READY`
- Owner: `UNASSIGNED`
- Blocker: `NONE`
- GitHub issue: `PENDING_SYNC`

#### Outcome

The approved behavior is observable.

#### Acceptance criteria

- [ ] The observable result matches FR-001.

#### Validation

```bash
python -m unittest
```

#### Execution log

Not started.

#### Agent execution details

<details>
<summary>Exact metadata used by Codex and task_waves.py</summary>

- Requirements: `REQ-0001, FR-001`
- Design: `DES-0001, Section 10`
- Authorization: `AUTH-0001`
- Depends on: `NONE`
- Dependency waivers: `NONE`
- Run ID: `NONE`
- Risk: `LOW`
- Write set: `app/task-9001.py`
- External state: `NONE`
- AWS mode: `NONE`
- Attempt budget: `2`
- Attempts used: `0`
- Evidence: `NONE`
- Skip record: `NONE`
- Last checkpoint: `NONE`
- Last updated: `2026-07-17T00:00:00+00:00`

</details>

"""
        tasks, _snap, waivers, by_id = parse_document(document([block]))

        self.assertEqual(set(tasks[0].metadata), set(task_waves.REQUIRED_METADATA))
        self.assertEqual(
            [task.task_id for task in task_waves.ready_tasks(tasks, by_id, waivers)],
            ["TASK-9001"],
        )

    def test_missing_status_metadata_is_invalid(self) -> None:
        text = task_block("TASK-001", "READY").replace("- Status: `READY`\n", "")
        tasks = task_waves.parse_tasks(text)

        with self.assertRaisesRegex(ValueError, "missing Status metadata"):
            task_waves.validate(tasks)

    def test_duplicate_singleton_metadata_is_invalid(self) -> None:
        text = task_block("TASK-001", "READY").replace(
            "- Status: `READY`",
            "- Status: `BACKLOG`\n- Status: `READY`",
        )
        tasks = task_waves.parse_tasks(text)

        with self.assertRaisesRegex(ValueError, "duplicate Status metadata"):
            task_waves.validate(tasks)

    def test_cannot_start_task_with_incomplete_dependency(self) -> None:
        text = document(
            [
                task_block(
                    "TASK-001",
                    "IN_PROGRESS",
                    owner="worker-1",
                    run_id="RUN-0001",
                ),
                task_block("TASK-002", "BACKLOG", "TASK-001"),
            ],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        _tasks, _snap, waivers, by_id = parse_document(text)

        with self.assertRaisesRegex(ValueError, "incomplete dependencies: TASK-001"):
            task_waves.validate_status_transition(
                by_id["TASK-002"], "READY", by_id, waivers
            )

    def test_done_is_terminal_and_in_progress_cannot_requeue(self) -> None:
        done = task_waves.parse_tasks(task_block("TASK-001", "DONE"))[0]
        running = task_waves.parse_tasks(task_block("TASK-002", "IN_PROGRESS"))[0]
        by_id = {done.task_id: done, running.task_id: running}

        with self.assertRaisesRegex(ValueError, "illegal status transition"):
            task_waves.validate_status_transition(done, "IN_PROGRESS", by_id)
        with self.assertRaisesRegex(ValueError, "illegal status transition"):
            task_waves.validate_status_transition(running, "READY", by_id)

    def test_idempotent_update_does_not_change_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
            )
            path, _state_path = write_task_project(root, original)

            changed = task_waves.update_task_file(
                path, "TASK-001", coordinator="lead", status="READY"
            )

            self.assertFalse(changed)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_failed_atomic_replace_preserves_original_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
            )
            path, _state_path = write_task_project(root, original)

            with mock.patch.object(os, "replace", side_effect=OSError("disk error")):
                with self.assertRaisesRegex(OSError, "disk error"):
                    task_waves.update_task_file(
                        path,
                        "TASK-001",
                        coordinator="lead",
                        status="BLOCKED",
                        blocker="Test failure; inspect output",
                        run_id="RUN-0001",
                    )

            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(list(path.parent.glob(".TASKS.md.*.tmp")), [])

    def test_concurrent_update_fails_instead_of_losing_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "TASKS.md"
            original = document([task_block("TASK-001", "READY")])
            path.write_text(original, encoding="utf-8")

            with task_waves.task_file_lock(path):
                with self.assertRaisesRegex(ValueError, "already being updated"):
                    task_waves.update_task_file(
                        path,
                        "TASK-001",
                        coordinator="lead",
                        issue="https://example/1",
                    )

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_skipped_dependency_requires_matching_waiver(self) -> None:
        without = document(
            [
                task_block("TASK-001", "SKIPPED"),
                task_block("TASK-002", "READY", "TASK-001"),
            ]
        )
        tasks, _snap, waivers, by_id = parse_document(without)
        self.assertEqual(task_waves.ready_tasks(tasks, by_id, waivers), [])

        with_waiver = document(
            [
                task_block("TASK-001", "SKIPPED"),
                task_block(
                    "TASK-002",
                    "READY",
                    "TASK-001",
                    waivers="TASK-001=WAIVER-001",
                ),
            ],
            waiver_rows=[
                "| `WAIVER-001` | `TASK-001` | `TASK-002` | `AUTH-0001 clause 4` | Equivalent evidence EV-0009 preserves acceptance | 2026-07-17T00:00:00+00:00 |"
            ],
        )
        tasks, _snap, waivers, by_id = parse_document(with_waiver)
        self.assertEqual(
            [task.task_id for task in task_waves.ready_tasks(tasks, by_id, waivers)],
            ["TASK-002"],
        )

    def test_claim_is_atomic_and_persists_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
            )
            path, _state_path = write_task_project(root, tasks_text)

            task_waves.claim_task_file(
                path,
                "TASK-001",
                owner="worker-a",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0000",
            )

            task = task_waves.parse_tasks(path.read_text(encoding="utf-8"))[0]
            self.assertEqual(task.status, "IN_PROGRESS")
            self.assertEqual(task.run_id, "RUN-0001")
            self.assertEqual(task.attempts_used, 1)
            self.assertEqual(task_waves.clean(task.metadata["Owner"]), "worker-a")
            self.assertEqual(task_waves.clean(task.metadata["Last checkpoint"]), "CP-0000")
            self.assertEqual(
                task_waves.parse_snapshot(path.read_text(encoding="utf-8")).get(
                    "Last checkpoint"
                ),
                "NONE",
            )

    def test_claim_requires_current_base_without_consuming_checkpoint(self) -> None:
        for checkpoint in ("CP-0004", "CP-0006"):
            with self.subTest(checkpoint=checkpoint), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                tasks_text = document(
                    [task_block("TASK-001", "READY")],
                    snapshot_text=snapshot(
                        run_state="RUNNING",
                        run_id="RUN-0001",
                        coordinator="lead",
                        last_checkpoint="CP-0005",
                    ),
                )
                path, _state_path = write_task_project(root, tasks_text)
                with self.assertRaisesRegex(ValueError, "current base CP-0005"):
                    task_waves.claim_task_file(
                        path,
                        "TASK-001",
                        owner="worker-a",
                        coordinator="lead",
                        run_id="RUN-0001",
                        checkpoint=checkpoint,
                    )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="RUNNING",
                    run_id="RUN-0001",
                    coordinator="lead",
                    last_checkpoint="NONE",
                ),
            )
            path, _state_path = write_task_project(root, tasks_text)
            task_waves.claim_task_file(
                path,
                "TASK-001",
                owner="worker-a",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0000",
            )
            updated = path.read_text(encoding="utf-8")
            self.assertEqual(
                task_waves.parse_snapshot(updated).get("Last checkpoint"), "NONE"
            )
            self.assertEqual(
                task_waves.clean(
                    task_waves.parse_tasks(updated)[0].metadata["Last checkpoint"]
                ),
                "CP-0000",
            )

    def test_exhausted_attempt_budget_fails_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original = document(
                [task_block("TASK-001", "BACKLOG", attempt_budget=1, attempts_used=1)],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
            ).replace("- Status: `BACKLOG`", "- Status: `READY`")
            path, _state_path = write_task_project(root, original)

            with self.assertRaisesRegex(ValueError, "attempt budget exhausted"):
                task_waves.claim_task_file(
                    path,
                    "TASK-001",
                    owner="worker-a",
                    coordinator="lead",
                    run_id="RUN-0001",
                    checkpoint="CP-0000",
                )

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_done_blocked_and_skipped_require_records(self) -> None:
        cases = [
            ("DONE", "Evidence", "NONE"),
            ("BLOCKED", "Blocker", "NONE"),
            ("SKIPPED", "Skip record", "NONE"),
        ]
        for status, field, value in cases:
            with self.subTest(status=status):
                text = task_block("TASK-001", status)
                text = task_waves.META_LINE.sub(
                    lambda match: f"- {field}: `{value}`"
                    if match.group("key") == field
                    else match.group(0),
                    text,
                )
                with self.assertRaisesRegex(ValueError, f"{status} requires"):
                    task_waves.validate(task_waves.parse_tasks(text))

    def test_runnable_tasks_require_objective_sections(self) -> None:
        text = task_block("TASK-001", "READY").replace(
            "#### Outcome\n\nThe task's bounded behavior is implemented and observable.\n\n",
            "",
        )
        with self.assertRaisesRegex(ValueError, "missing required section #### Outcome"):
            task_waves.validate(task_waves.parse_tasks(text))

        done = task_block("TASK-001", "DONE").replace("- [x]", "- [ ]")
        with self.assertRaisesRegex(ValueError, "incomplete acceptance criteria"):
            task_waves.validate(task_waves.parse_tasks(done))

    def test_safe_groups_serialize_overlaps_and_aws_mutations(self) -> None:
        text = document(
            [
                task_block("TASK-001", "READY", write_set="app/**"),
                task_block("TASK-002", "READY", write_set="app/api.py"),
                task_block("TASK-003", "READY", write_set="tests/api.py"),
                task_block(
                    "TASK-004",
                    "READY",
                    write_set="infrastructure/stack.py",
                    external_state="aws:stack/dev",
                    aws_mode="MUTATION",
                ),
            ]
        )
        tasks, _snap, waivers, by_id = parse_document(text)
        waves = task_waves.compute_waves(tasks, by_id)
        ready = task_waves.ready_tasks(tasks, by_id, waivers)

        isolated = task_waves.safe_execution_groups(
            ready, waves, isolated_worktrees=True, maximum_workers=2
        )
        nonisolated = task_waves.safe_execution_groups(
            ready, waves, isolated_worktrees=False
        )

        self.assertEqual(len(nonisolated), 4)
        self.assertFalse(
            any(
                {"TASK-001", "TASK-002"}
                <= {task.task_id for task in group}
                for group in isolated
            )
        )
        self.assertTrue(
            any(
                {"TASK-001", "TASK-003"}
                <= {task.task_id for task in group}
                for group in isolated
            )
        )
        self.assertTrue(all(len(group) <= 2 for group in isolated))
        self.assertTrue(
            all(
                len(group) == 1
                for group in isolated
                if any(task.task_id == "TASK-004" for task in group)
            )
        )

    def test_unsafe_write_boundaries_are_rejected(self) -> None:
        for value in (
            "../secret",
            "/tmp/file",
            ".git/config",
            ".GiT/config",
            "APP/.GIT/config",
            "app/*.py",
            "TODO",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Write set"):
                    task_waves.validate_write_boundary(value, "TASK-001")

    def test_cycle_message_is_deterministic(self) -> None:
        tasks = task_waves.parse_tasks(
            task_block("TASK-001", "BACKLOG", "TASK-002")
            + task_block("TASK-002", "BACKLOG", "TASK-001")
        )
        by_id = task_waves.validate(tasks)

        with self.assertRaisesRegex(
            ValueError,
            "TASK-001 -> TASK-002 -> TASK-001",
        ):
            task_waves.compute_waves(tasks, by_id)

    def test_run_claim_is_exclusive_and_unclean_run_is_not_auto_resumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            tasks_text = document([task_block("TASK-001", "READY")])
            path, _state_path = write_task_project(root, tasks_text)

            task_waves.mutate_run_snapshot(
                path,
                operation="start",
                run_id="RUN-0001",
                coordinator="lead",
            )
            with self.assertRaisesRegex(ValueError, "already exists|reconciliation"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="start",
                    run_id="RUN-0002",
                    coordinator="other",
                )

    def test_run_and_attempt_state_are_mirrored_to_bootstrap_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            path = root / "TASKS.md"
            tasks_text = document([task_block("TASK-001", "READY")])
            path.write_text(tasks_text, encoding="utf-8")
            state_path = write_matching_state(root, tasks_text)

            task_waves.mutate_run_snapshot(
                path,
                operation="start",
                run_id="RUN-0001",
                coordinator="lead",
            )
            task_waves.claim_task_file(
                path,
                "TASK-001",
                owner="worker-a",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0000",
            )

            mirrored = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(mirrored["execution"]["run_id"], "RUN-0001")
            self.assertEqual(mirrored["execution"]["coordinator"], "lead")
            self.assertEqual(mirrored["execution"]["state"], "RUNNING")
            self.assertEqual(mirrored["execution"]["active_tasks"], ["TASK-001"])
            self.assertEqual(mirrored["execution"]["attempts"], {"TASK-001": 1})
            with self.assertRaisesRegex(ValueError, "checkpointed run"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="resume",
                    run_id="RUN-0001",
                    coordinator="lead",
                )

    def test_fenced_examples_do_not_create_tasks_or_metadata(self) -> None:
        fake = """```markdown
### TASK-999 — Fake example

- Status: `READY`
- Attempts used: `99`
```

"""
        real = task_block("TASK-001", "READY").replace(
            "#### Validation\n",
            "#### Validation\n\n```text\n- Status: `DONE`\n```\n\n",
        )
        text = document([real]).replace("## Task definitions\n\n", "## Task definitions\n\n" + fake)

        tasks, _snap, _waivers, _by_id = parse_document(text)

        self.assertEqual([task.task_id for task in tasks], ["TASK-001"])
        self.assertEqual(tasks[0].status, "READY")
        self.assertEqual(tasks[0].attempts_used, 0)

    def test_waiver_requires_exact_authority_timestamp_and_evidence(self) -> None:
        blocks = [
            task_block("TASK-001", "SKIPPED"),
            task_block(
                "TASK-002",
                "READY",
                "TASK-001",
                waivers="TASK-001=WAIVER-001",
            ),
        ]
        cases = [
            (
                "AUTH-00010",
                "Equivalent evidence EV-0009 preserves acceptance",
                "2026-07-17T00:00:00+00:00",
                "exact current authority",
            ),
            (
                "AUTH-0001",
                "Equivalent behavior preserves acceptance",
                "2026-07-17T00:00:00+00:00",
                "preserved evidence",
            ),
            (
                "AUTH-0001",
                "Equivalent evidence EV-0009 preserves acceptance",
                "2026-07-17",
                "UTC offset",
            ),
        ]
        for authority, rationale, recorded_at, message in cases:
            with self.subTest(message=message):
                text = document(
                    blocks,
                    waiver_rows=[
                        f"| `WAIVER-001` | `TASK-001` | `TASK-002` | `{authority}` | {rationale} | {recorded_at} |"
                    ],
                )
                with self.assertRaisesRegex(ValueError, message):
                    parse_document(text)

    def test_external_targets_overlap_hierarchically(self) -> None:
        self.assertTrue(
            task_waves.external_targets_overlap("aws:stack", "AWS:STACK/dev")
        )
        self.assertTrue(
            task_waves.external_targets_overlap("github:repo#issues", "github:repo")
        )
        self.assertFalse(
            task_waves.external_targets_overlap("aws:stack/dev", "aws:stack/prod")
        )

    def test_parallel_claim_requires_isolation_and_disjoint_boundaries(self) -> None:
        base_snapshot = snapshot(
            run_state="RUNNING",
            run_id="RUN-0001",
            coordinator="lead",
            maximum_workers=2,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original = document(
                [
                    task_block(
                        "TASK-001",
                        "IN_PROGRESS",
                        owner="worker-a",
                        write_set="app/one.py",
                        checkpoint="CP-0000",
                    ),
                    task_block("TASK-002", "READY", write_set="tests/two.py"),
                ],
                snapshot_text=base_snapshot,
            )
            path, _state_path = write_task_project(root, original)

            with self.assertRaisesRegex(ValueError, "isolated-worktrees"):
                task_waves.claim_task_file(
                    path,
                    "TASK-002",
                    owner="worker-b",
                    coordinator="lead",
                    run_id="RUN-0001",
                    checkpoint="CP-0000",
                )
            task_waves.claim_task_file(
                path,
                "TASK-002",
                owner="worker-b",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0000",
                isolated_worktrees=True,
            )
            self.assertEqual(
                [
                    task.status
                    for task in task_waves.parse_tasks(path.read_text(encoding="utf-8"))
                ],
                ["IN_PROGRESS", "IN_PROGRESS"],
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original = document(
                [
                    task_block(
                        "TASK-001",
                        "IN_PROGRESS",
                        write_set="app/**",
                        checkpoint="CP-0000",
                    ),
                    task_block("TASK-002", "READY", write_set="APP/api.py"),
                ],
                snapshot_text=base_snapshot,
            )
            path, _state_path = write_task_project(root, original)
            with self.assertRaisesRegex(ValueError, "conflicts with active"):
                task_waves.claim_task_file(
                    path,
                    "TASK-002",
                    owner="worker-b",
                    coordinator="lead",
                    run_id="RUN-0001",
                    checkpoint="CP-0000",
                    isolated_worktrees=True,
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_claim_enforces_worker_cap_protected_paths_and_control_owner(self) -> None:
        cases = [
            (
                snapshot(
                    run_state="RUNNING",
                    run_id="RUN-0001",
                    coordinator="lead",
                    maximum_workers=1,
                ),
                [task_block("TASK-001", "IN_PROGRESS"), task_block("TASK-002", "READY")],
                "worker-b",
                "Maximum workers",
            ),
            (
                snapshot(
                    run_state="RUNNING",
                    run_id="RUN-0001",
                    coordinator="lead",
                    protected_dirty_paths="app/**",
                ),
                [task_block("TASK-002", "READY", write_set="APP/api.py")],
                "worker-b",
                "Protected dirty paths",
            ),
            (
                snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
                [task_block("TASK-002", "READY", write_set="TASKS.md")],
                "worker-b",
                "coordinator ownership",
            ),
        ]
        for snap, blocks, owner, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                original = document(blocks, snapshot_text=snap)
                path, _state_path = write_task_project(root, original)
                with self.assertRaisesRegex(ValueError, message):
                    task_waves.claim_task_file(
                        path,
                        "TASK-002",
                        owner=owner,
                        coordinator="lead",
                        run_id="RUN-0001",
                        checkpoint="CP-0000",
                        isolated_worktrees=True,
                    )
                self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_two_wave_run_advances_only_after_dependency_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks_text = document(
                [
                    task_block("TASK-001", "READY"),
                    task_block("TASK-002", "READY", "TASK-001"),
                ]
            )
            path, _state_path = write_task_project(root, tasks_text)
            task_waves.mutate_run_snapshot(
                path, operation="start", run_id="RUN-0001", coordinator="lead"
            )
            task_waves.claim_task_file(
                path,
                "TASK-001",
                owner="worker-a",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0000",
            )
            with self.assertRaisesRegex(ValueError, "incomplete dependencies"):
                task_waves.claim_task_file(
                    path,
                    "TASK-002",
                    owner="worker-b",
                    coordinator="lead",
                    run_id="RUN-0001",
                    checkpoint="CP-0000",
                    isolated_worktrees=True,
                )
            path.write_text(observed_task_text(path.read_text(encoding="utf-8")), encoding="utf-8")
            path.with_name("VERIFY.md").write_text(
                completion_evidence_document(
                    completion_evidence_row(),
                    completion_evidence_row(
                        evidence_id="EV-0002",
                        durable_source="VERIFY.md#ev-0002",
                    ),
                ),
                encoding="utf-8",
            )
            task_waves.update_task_file(
                path,
                "TASK-001",
                coordinator="lead",
                status="DONE",
                evidence=(
                    "EV-0001, EV-0002, VERIFY.md#ev-0001, "
                    "https://example.test/runs/EV-0001"
                ),
                run_id="RUN-0001",
                checkpoint="CP-0001",
            )
            self.assertEqual(
                task_waves.parse_snapshot(path.read_text(encoding="utf-8")).get(
                    "Current wave"
                ),
                "2",
            )
            task_waves.claim_task_file(
                path,
                "TASK-002",
                owner="worker-b",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0001",
            )
            self.assertEqual(
                task_waves.parse_tasks(path.read_text(encoding="utf-8"))[1].status,
                "IN_PROGRESS",
            )

    def test_single_task_mode_survives_pause_resume_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_git(root)
            protected = "NONE"
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    baseline_commit=commit,
                    last_known_green_commit=commit,
                    protected_dirty_paths=protected,
                ),
            )
            path, state_path = write_task_project(root, tasks_text)
            verify_path = root / "VERIFY.md"
            verify_path.write_text("# Verification\n", encoding="utf-8")

            task_waves.mutate_run_snapshot(
                path,
                operation="start",
                run_id="RUN-0001",
                coordinator="lead",
                run_mode="SINGLE_TASK",
            )
            task_waves.claim_task_file(
                path,
                "TASK-001",
                owner="worker-a",
                coordinator="lead",
                run_id="RUN-0001",
                checkpoint="CP-0000",
            )
            path.write_text(
                observed_task_text(path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
            verify_path.write_text(
                completion_evidence_document(), encoding="utf-8"
            )
            task_waves.update_task_file(
                path,
                "TASK-001",
                coordinator="lead",
                status="DONE",
                evidence="EV-0001",
                run_id="RUN-0001",
                checkpoint="CP-0001",
            )
            path.write_text(
                append_checkpoint(
                    path.read_text(encoding="utf-8"),
                    checkpoint_row(
                        "CP-0002",
                        commit=commit,
                        dirty=protected,
                        next_action="resume run",
                    ),
                ),
                encoding="utf-8",
            )
            with verify_path.open("a", encoding="utf-8") as file:
                file.write("\nCP-0002: pause checkpoint evidence recorded.\n")
            task_waves.mutate_run_snapshot(
                path,
                operation="pause",
                run_id="RUN-0001",
                coordinator="lead",
                checkpoint="CP-0002",
            )
            task_waves.mutate_run_snapshot(
                path,
                operation="resume",
                run_id="RUN-0001",
                coordinator="lead",
            )
            path.write_text(
                append_checkpoint(
                    path.read_text(encoding="utf-8"),
                    checkpoint_row(
                        "CP-0003",
                        commit=commit,
                        dirty=protected,
                        next_action="release decision",
                    ),
                ),
                encoding="utf-8",
            )
            with verify_path.open("a", encoding="utf-8") as file:
                file.write("CP-0003: completion checkpoint evidence recorded.\n")
            task_waves.mutate_run_snapshot(
                path,
                operation="complete",
                run_id="RUN-0001",
                coordinator="lead",
                checkpoint="CP-0003",
            )

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["execution"]["mode"], "SINGLE_TASK")
            self.assertEqual(state["execution"]["state"], "COMPLETE")

    def test_interrupted_state_first_write_blocks_next_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "TASKS.md"
            tasks_text = document([task_block("TASK-001", "READY")])
            path.write_text(tasks_text, encoding="utf-8")
            state_path = write_matching_state(root, tasks_text)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["execution"]["attempts"]["TASK-001"] = 1
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            original = path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "reconcile before mutation"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    issue="https://github.com/example/repo/issues/1",
                )

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_wrong_run_id_and_invalid_evidence_are_rejected(self) -> None:
        text = document(
            [task_block("TASK-001", "IN_PROGRESS")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, text)
            with self.assertRaisesRegex(ValueError, "must match the active run"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001",
                    run_id="RUN-9999",
                    checkpoint="CP-0002",
                )
            with self.assertRaisesRegex(ValueError, "Evidence reference"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="tests passed",
                    run_id="RUN-0001",
                    checkpoint="CP-0002",
                )

    def test_done_requires_checkpoint_advance_and_recorded_local_evidence(self) -> None:
        text = document(
            [task_block("TASK-001", "IN_PROGRESS")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        text = observed_task_text(text)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, text)
            with self.assertRaisesRegex(ValueError, "new --checkpoint"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001",
                    run_id="RUN-0001",
                )
            with self.assertRaisesRegex(ValueError, "checkpoint must advance"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001",
                    run_id="RUN-0001",
                    checkpoint="CP-0001",
                )

            verify_path = path.with_name("VERIFY.md")
            verify_path.write_text(
                completion_evidence_document(
                    completion_evidence_row(
                        evidence_id="EV-0002",
                        durable_source="VERIFY.md#ev-0002",
                    )
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "not recorded in VERIFY.md"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001",
                    run_id="RUN-0001",
                    checkpoint="CP-0002",
                )
            verify_path.write_text(
                completion_evidence_document(),
                encoding="utf-8",
            )
            task_waves.update_task_file(
                path,
                "TASK-001",
                coordinator="lead",
                status="DONE",
                evidence="EV-0001",
                run_id="RUN-0001",
                checkpoint="CP-0002",
            )
            completed = task_waves.parse_tasks(path.read_text(encoding="utf-8"))[0]
            self.assertEqual(completed.status, "DONE")
            self.assertEqual(task_waves.clean(completed.metadata["Last checkpoint"]), "CP-0002")

    def test_done_evidence_requires_exact_unique_structured_task_row(self) -> None:
        base = observed_task_text(
            document(
                [task_block("TASK-001", "IN_PROGRESS")],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
            )
        )
        valid_table = completion_evidence_document()
        fenced_table = (
            "# Verification\n\n```markdown\n"
            + valid_table.split("\n\n", 1)[1]
            + "```\n"
        )
        cases = [
            (
                "stock token",
                "# Verification\n\nEV-0001 | TODO | NOT_STARTED\n",
                "exactly one.*Task completion evidence",
            ),
            ("fenced table", fenced_table, "exactly one.*Task completion evidence"),
            (
                "placeholder row",
                completion_evidence_document(
                    completion_evidence_row(
                        command_or_observation="TODO",
                        result="NOT_STARTED",
                    )
                ),
                "placeholder evidence",
            ),
            (
                "duplicate row",
                completion_evidence_document(
                    completion_evidence_row(), completion_evidence_row()
                ),
                "Evidence IDs must be unique",
            ),
            (
                "wrong task",
                completion_evidence_document(
                    completion_evidence_row(task_id="TASK-0010")
                ),
                "wrong task",
            ),
            (
                "URL-only source",
                completion_evidence_document(
                    completion_evidence_row(
                        durable_source="https://example.test/runs/1"
                    )
                ),
                "Durable source.*durable source",
            ),
        ]
        for name, verify_text, message in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path, state_path = write_task_project(root, base)
                (root / "VERIFY.md").write_text(verify_text, encoding="utf-8")
                original_tasks = path.read_text(encoding="utf-8")
                original_state = state_path.read_text(encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    task_waves.update_task_file(
                        path,
                        "TASK-001",
                        coordinator="lead",
                        status="DONE",
                        evidence="EV-0001",
                        run_id="RUN-0001",
                        checkpoint="CP-0002",
                    )
                self.assertEqual(path.read_text(encoding="utf-8"), original_tasks)
                self.assertEqual(state_path.read_text(encoding="utf-8"), original_state)

    def test_done_rejects_noncanonical_local_evidence_ids(self) -> None:
        base = observed_task_text(
            document(
                [task_block("TASK-001", "IN_PROGRESS")],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
            )
        )
        for evidence in (
            "EV-001",
            "EVIDENCE-0001",
            "EV-0001-SUFFIX",
            "ev-0001",
            "VERIFY.md#ev-0001",
        ):
            with self.subTest(evidence=evidence), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path, _state_path = write_task_project(root, base)
                (root / "VERIFY.md").write_text(
                    completion_evidence_document(), encoding="utf-8"
                )
                with self.assertRaisesRegex(ValueError, "Evidence reference"):
                    task_waves.update_task_file(
                        path,
                        "TASK-001",
                        coordinator="lead",
                        status="DONE",
                        evidence=evidence,
                        run_id="RUN-0001",
                        checkpoint="CP-0002",
                    )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, base)
            (root / "VERIFY.md").write_text(
                completion_evidence_document(), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "duplicate local Evidence"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001, EV-0001",
                    run_id="RUN-0001",
                    checkpoint="CP-0002",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, base)
            (root / "VERIFY.md").write_text(
                completion_evidence_document(), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "not recorded.*EV-0002"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001, EV-0002",
                    run_id="RUN-0001",
                    checkpoint="CP-0002",
                )

    def test_claim_requires_exact_coordinator(self) -> None:
        text = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, text)
            with self.assertRaisesRegex(ValueError, "does not match"):
                task_waves.claim_task_file(
                    path,
                    "TASK-001",
                    owner="worker-a",
                    coordinator="other",
                    run_id="RUN-0001",
                    checkpoint="CP-0000",
                )

    def test_every_shared_mutation_binds_the_active_coordinator(self) -> None:
        running = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, running)
            for action in ("issue", "status"):
                with self.subTest(action=action), self.assertRaisesRegex(
                    ValueError, "does not match"
                ):
                    task_waves.update_task_file(
                        path,
                        "TASK-001",
                        coordinator="other",
                        issue="https://example.test/1" if action == "issue" else None,
                        status="READY" if action == "status" else None,
                    )
            for operation in ("pause", "complete"):
                with self.subTest(operation=operation), self.assertRaisesRegex(
                    ValueError, "does not match"
                ):
                    task_waves.mutate_run_snapshot(
                        path,
                        operation=operation,
                        run_id="RUN-0001",
                        coordinator="other",
                        checkpoint="CP-0001",
                    )

        paused = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                run_state="PAUSED",
                run_id="RUN-0001",
                coordinator="lead",
                last_checkpoint="CP-0001",
            ),
            checkpoint_rows=[
                checkpoint_row(
                    "CP-0001",
                    outcomes="TASK-001 READY attempts=0/2",
                    evidence="NONE",
                )
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, paused)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "does not match"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="resume",
                    run_id="RUN-0001",
                    coordinator="other",
                )

    def test_mutation_requires_bootstrap_state_file(self) -> None:
        text = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TASKS.md"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "bootstrap.yaml is required"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    issue="https://example.test/1",
                )

    def test_uninitialized_and_stale_plans_are_readable_but_not_mutable(self) -> None:
        stale = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                task_plan_state="STALE",
                run_state="RUNNING",
                run_id="RUN-0001",
                coordinator="lead",
            ),
        )
        tasks, snap, _waivers, _by_id = parse_document(stale)
        self.assertEqual(snap.get("Task-plan state"), "STALE")
        self.assertEqual(len(tasks), 1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, stale)
            with self.assertRaisesRegex(ValueError, "Task-plan state CURRENT"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    issue="https://example.test/1",
                )
            with self.assertRaisesRegex(ValueError, "Task-plan state CURRENT"):
                task_waves.claim_task_file(
                    path,
                    "TASK-001",
                    owner="worker-a",
                    coordinator="lead",
                    run_id="RUN-0001",
                    checkpoint="CP-0000",
                )
            with self.assertRaisesRegex(ValueError, "Task-plan state CURRENT"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        uninitialized = document(
            [],
            snapshot_text=snapshot(
                task_plan="UNINITIALIZED",
                task_plan_state="UNINITIALIZED",
                current_wave="NONE",
                last_checkpoint="NONE",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, uninitialized)
            with self.assertRaisesRegex(ValueError, "Task-plan state CURRENT"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="start",
                    run_id="RUN-0001",
                    coordinator="lead",
                )

    def test_plan_state_mirror_drift_blocks_mutation(self) -> None:
        text = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, state_path = write_task_project(root, text)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["execution"]["plan_state"] = "STALE"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "plan_state"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    issue="https://example.test/1",
                )

    def test_resume_fails_closed_when_git_is_unavailable_or_dirty_set_drifts(self) -> None:
        paused = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=snapshot(
                run_state="PAUSED",
                run_id="RUN-0001",
                coordinator="lead",
                last_checkpoint="CP-0001",
            ),
            checkpoint_rows=[
                checkpoint_row(
                    "CP-0001",
                    outcomes="TASK-001 READY attempts=0/2",
                    evidence="NONE",
                )
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, paused)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            original = path.read_text(encoding="utf-8")
            with mock.patch.object(
                task_waves.subprocess, "run", side_effect=FileNotFoundError("git")
            ):
                with self.assertRaisesRegex(ValueError, "Git reconciliation unavailable"):
                    task_waves.mutate_run_snapshot(
                        path,
                        operation="resume",
                        run_id="RUN-0001",
                        coordinator="lead",
                    )
            self.assertEqual(path.read_text(encoding="utf-8"), original)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_git(root)
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="PAUSED",
                    run_id="RUN-0001",
                    coordinator="lead",
                    baseline_commit=commit,
                    last_known_green_commit=commit,
                    protected_dirty_paths="NONE",
                    last_checkpoint="CP-0001",
                ),
                checkpoint_rows=[
                    checkpoint_row(
                        "CP-0001",
                        commit=commit,
                        outcomes="TASK-001 READY attempts=0/2",
                        evidence="NONE",
                    )
                ],
            )
            path, _state_path = write_task_project(root, tasks_text)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            (root / "unexpected.txt").write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unrecorded dirty paths=unexpected.txt"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="resume",
                    run_id="RUN-0001",
                    coordinator="lead",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_git(root)
            missing_receipt = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="PAUSED",
                    run_id="RUN-0001",
                    coordinator="lead",
                    baseline_commit=commit,
                    last_known_green_commit=commit,
                    protected_dirty_paths="NONE",
                    last_checkpoint="CP-0001",
                ),
            )
            path, state_path = write_task_project(root, missing_receipt)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            original_tasks = path.read_text(encoding="utf-8")
            original_state = state_path.read_text(encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "existing checkpoint row"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="resume",
                    run_id="RUN-0001",
                    coordinator="lead",
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original_tasks)
            self.assertEqual(state_path.read_text(encoding="utf-8"), original_state)

    def test_pause_requires_complete_unique_checkpoint_receipt(self) -> None:
        running_snapshot = snapshot(
            run_state="RUNNING",
            run_id="RUN-0001",
            coordinator="lead",
        )
        base = document(
            [task_block("TASK-001", "READY")], snapshot_text=running_snapshot
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _state_path = write_task_project(root, base)
            (root / "VERIFY.md").write_text("# Verification\n\nCP-0001\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "existing checkpoint row"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        valid_row = checkpoint_row(
            "CP-0001",
            outcomes="TASK-001 READY attempts=0/2",
            evidence="NONE",
            next_action="resume task selection",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=running_snapshot,
                checkpoint_rows=[valid_row],
            )
            path, _state_path = write_task_project(root, tasks_text)
            (root / "VERIFY.md").write_text(
                "# Verification\n\n```text\nCP-0001\n```\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "not referenced in VERIFY.md"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incomplete_row = valid_row.replace(
                "Blockers: NONE; Next: resume task selection", "NONE"
            )
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=running_snapshot,
                checkpoint_rows=[incomplete_row],
            )
            path, _state_path = write_task_project(root, tasks_text)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "blockers and next safe action"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reused_snapshot = snapshot(
                run_state="RUNNING",
                run_id="RUN-0001",
                coordinator="lead",
                last_checkpoint="CP-0001",
            )
            tasks_text = document(
                [task_block("TASK-001", "READY")],
                snapshot_text=reused_snapshot,
                checkpoint_rows=[valid_row],
            )
            path, _state_path = write_task_project(root, tasks_text)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "advance and may not be reused"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        duplicate = document(
            [task_block("TASK-001", "READY")],
            snapshot_text=running_snapshot,
            checkpoint_rows=[valid_row, valid_row],
        )
        with self.assertRaisesRegex(ValueError, "may not be reused"):
            task_waves.parse_checkpoint_rows(duplicate)

    def test_checkpoint_receipt_uses_exact_task_and_evidence_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks_text = document(
                [
                    task_block("TASK-001", "READY"),
                    task_block("TASK-0010", "READY"),
                ],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
                checkpoint_rows=[
                    checkpoint_row(
                        "CP-0001",
                        outcomes="TASK-0010 READY attempts=0/2",
                        evidence="NONE",
                    )
                ],
            )
            path, _state_path = write_task_project(root, tasks_text)
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            tasks = task_waves.parse_tasks(tasks_text)
            snap = task_waves.parse_snapshot(tasks_text)
            with self.assertRaisesRegex(ValueError, "missing outcome for TASK-001"):
                task_waves.validate_checkpoint_receipt(
                    path, tasks_text, "CP-0001", "RUN-0001", tasks, snap
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks_text = document(
                [task_block("TASK-001", "DONE", evidence="EV-0001")],
                snapshot_text=snapshot(
                    run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                ),
                checkpoint_rows=[
                    checkpoint_row(
                        "CP-0001",
                        outcomes="TASK-001 DONE attempts=0/2",
                        evidence="EV-00010",
                    )
                ],
            )
            path, _state_path = write_task_project(root, tasks_text)
            (root / "VERIFY.md").write_text(
                completion_evidence_document() + "\nCP-0001\n", encoding="utf-8"
            )
            tasks = task_waves.parse_tasks(tasks_text)
            snap = task_waves.parse_snapshot(tasks_text)
            with self.assertRaisesRegex(ValueError, "evidence for TASK-001 is incomplete"):
                task_waves.validate_checkpoint_receipt(
                    path, tasks_text, "CP-0001", "RUN-0001", tasks, snap
                )

    def test_checkpoint_receipt_requires_exact_attempt_fraction(self) -> None:
        for attempts in ("attempts=0/99", "attempts=0"):
            with self.subTest(attempts=attempts), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                tasks_text = document(
                    [task_block("TASK-001", "READY", attempt_budget=3)],
                    snapshot_text=snapshot(
                        run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
                    ),
                    checkpoint_rows=[
                        checkpoint_row(
                            "CP-0001",
                            outcomes=f"TASK-001 READY {attempts}",
                            evidence="NONE",
                        )
                    ],
                )
                path, _state_path = write_task_project(root, tasks_text)
                (root / "VERIFY.md").write_text(
                    "# Verification\n\nCP-0001\n", encoding="utf-8"
                )
                tasks = task_waves.parse_tasks(tasks_text)
                snap = task_waves.parse_snapshot(tasks_text)
                with self.assertRaisesRegex(
                    ValueError, "attempts for TASK-001 are not explicit"
                ):
                    task_waves.validate_checkpoint_receipt(
                        path, tasks_text, "CP-0001", "RUN-0001", tasks, snap
                    )

    def test_pause_git_reconciliation_fails_closed_and_round_trips_ledgers(self) -> None:
        def running_receipt(commit: str, *, baseline: str | None = None) -> str:
            return document(
                [task_block("TASK-001", "READY")],
                snapshot_text=snapshot(
                    run_state="RUNNING",
                    run_id="RUN-0001",
                    coordinator="lead",
                    baseline_commit=baseline or commit,
                    last_known_green_commit=commit,
                    protected_dirty_paths="NONE",
                ),
                checkpoint_rows=[
                    checkpoint_row(
                        "CP-0001",
                        commit=commit,
                        outcomes="TASK-001 READY attempts=0/2",
                        evidence="NONE",
                    )
                ],
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, state_path = write_task_project(root, running_receipt("abc1234"))
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            original_tasks = path.read_text(encoding="utf-8")
            original_state = state_path.read_text(encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not a regular Git worktree"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original_tasks)
            self.assertEqual(state_path.read_text(encoding="utf-8"), original_state)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = initialize_git(root)
            path, _state_path = write_task_project(
                root, running_receipt("deadbee", baseline=baseline)
            )
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "commits are not resolvable"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_git(root)
            path, _state_path = write_task_project(root, running_receipt(commit))
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            (root / "unexpected.txt").write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unrecorded dirty paths=unexpected.txt"):
                task_waves.mutate_run_snapshot(
                    path,
                    operation="pause",
                    run_id="RUN-0001",
                    coordinator="lead",
                    checkpoint="CP-0001",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_git(root)
            path, state_path = write_task_project(root, running_receipt(commit))
            (root / "VERIFY.md").write_text(
                "# Verification\n\nCP-0001\n", encoding="utf-8"
            )
            task_waves.mutate_run_snapshot(
                path,
                operation="pause",
                run_id="RUN-0001",
                coordinator="lead",
                checkpoint="CP-0001",
            )
            self.assertEqual(
                task_waves.parse_snapshot(path.read_text(encoding="utf-8")).get(
                    "Run state"
                ),
                "PAUSED",
            )
            task_waves.mutate_run_snapshot(
                path,
                operation="resume",
                run_id="RUN-0001",
                coordinator="lead",
            )
            self.assertEqual(
                task_waves.parse_snapshot(path.read_text(encoding="utf-8")).get(
                    "Run state"
                ),
                "RUNNING",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["execution"]["state"], "RUNNING")

    def test_done_rejects_url_only_evidence_and_placeholder_execution_log(self) -> None:
        base = document(
            [task_block("TASK-001", "IN_PROGRESS")],
            snapshot_text=snapshot(
                run_state="RUNNING", run_id="RUN-0001", coordinator="lead"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            url_text = observed_task_text(base)
            path, _state_path = write_task_project(root, url_text)
            with self.assertRaisesRegex(ValueError, "local Evidence reference"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="https://example.test/run/1",
                    run_id="RUN-0001",
                    checkpoint="CP-0002",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unchecked_only = base.replace("- [ ]", "- [x]", 1)
            path, _state_path = write_task_project(root, unchecked_only)
            (root / "VERIFY.md").write_text(
                completion_evidence_document(), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "observed Execution log"):
                task_waves.update_task_file(
                    path,
                    "TASK-001",
                    coordinator="lead",
                    status="DONE",
                    evidence="EV-0001",
                    run_id="RUN-0001",
                    checkpoint="CP-0002",
                )

    def test_cli_allows_only_one_mutation_and_rejects_ignored_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TASKS.md"
            original = document([task_block("TASK-001", "READY")])
            path.write_text(original, encoding="utf-8")
            cases = [
                (
                    [
                        "task_waves.py",
                        str(path),
                        "--start-run",
                        "RUN-0001",
                        "--coordinator",
                        "lead",
                        "--claim",
                        "TASK-001",
                        "--owner",
                        "worker-a",
                        "--run-id",
                        "RUN-0001",
                        "--checkpoint",
                        "CP-0001",
                    ],
                    "one mutating action",
                ),
                (
                    ["task_waves.py", str(path), "--ready", "--owner", "worker-a"],
                    "not valid for this action",
                ),
                (
                    [
                        "task_waves.py",
                        str(path),
                        "--set-issue",
                        "TASK-001",
                        "https://example.test/1",
                    ],
                    "--set-issue requires --coordinator",
                ),
                (
                    [
                        "task_waves.py",
                        str(path),
                        "--pause-run",
                        "RUN-0001",
                        "--checkpoint",
                        "CP-0001",
                    ],
                    "--pause-run requires --coordinator and --checkpoint",
                ),
            ]
            for argv, message in cases:
                with self.subTest(message=message), mock.patch.object(sys, "argv", argv):
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        result = task_waves.main()
                    self.assertEqual(result, 1)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
