from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
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
    REPOSITORY_ROOT / "my-project" / "scripts" / "task_waves.py",
)


def task_block(
    task_id: str,
    status: str,
    dependencies: str = "NONE",
    *,
    issue: str = "PENDING_SYNC",
) -> str:
    return f"""### {task_id} — Test task

- Status: `{status}`
- Depends on: `{dependencies}`
- GitHub issue: `{issue}`
- Last updated: `TODO`

"""


class TaskWaveSafetyTests(unittest.TestCase):
    def test_ready_selects_only_explicit_ready_tasks(self) -> None:
        text = "".join(
            [
                task_block("TASK-001", "BACKLOG"),
                task_block("TASK-002", "READY"),
                task_block("TASK-003", "DONE"),
                task_block("TASK-004", "READY", "TASK-001"),
            ]
        )
        tasks = task_waves.parse_tasks(text)
        by_id = task_waves.validate(tasks)

        selected = task_waves.ready_tasks(tasks, by_id)

        self.assertEqual([task.task_id for task in selected], ["TASK-002"])

    def test_missing_status_metadata_is_invalid(self) -> None:
        text = """### TASK-001 — Missing status

- Depends on: `NONE`
"""
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
        text = "".join(
            [
                task_block("TASK-001", "IN_PROGRESS"),
                task_block("TASK-002", "BACKLOG", "TASK-001"),
            ]
        )
        tasks = task_waves.parse_tasks(text)
        by_id = task_waves.validate(tasks)

        with self.assertRaisesRegex(ValueError, "incomplete dependencies: TASK-001"):
            task_waves.validate_status_transition(
                by_id["TASK-002"], "READY", by_id
            )

    def test_done_is_terminal(self) -> None:
        tasks = task_waves.parse_tasks(task_block("TASK-001", "DONE"))
        by_id = task_waves.validate(tasks)

        with self.assertRaisesRegex(ValueError, "illegal status transition"):
            task_waves.validate_status_transition(
                by_id["TASK-001"], "IN_PROGRESS", by_id
            )

    def test_idempotent_update_does_not_change_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "TASKS.md"
            original = task_block("TASK-001", "READY")
            path.write_text(original, encoding="utf-8")

            changed = task_waves.update_task_file(
                path, "TASK-001", status="READY"
            )

            self.assertFalse(changed)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_failed_atomic_replace_preserves_original_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "TASKS.md"
            original = task_block("TASK-001", "READY")
            path.write_text(original, encoding="utf-8")

            with mock.patch.object(os, "replace", side_effect=OSError("disk error")):
                with self.assertRaisesRegex(OSError, "disk error"):
                    task_waves.update_task_file(
                        path, "TASK-001", status="IN_PROGRESS"
                    )

            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(list(path.parent.glob(".TASKS.md.*.tmp")), [])

    def test_concurrent_update_fails_instead_of_losing_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "TASKS.md"
            original = task_block("TASK-001", "READY")
            path.write_text(original, encoding="utf-8")

            with task_waves.task_file_lock(path):
                with self.assertRaisesRegex(ValueError, "already being updated"):
                    task_waves.update_task_file(
                        path,
                        "TASK-001",
                        status="IN_PROGRESS",
                    )

            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
