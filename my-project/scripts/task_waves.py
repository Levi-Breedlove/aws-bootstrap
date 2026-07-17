#!/usr/bin/env python3
"""Validate TASKS.md dependencies, sort tasks into waves, and update task metadata."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

TASK_HEADER = re.compile(r"^###\s+(TASK-\d+)\s+[—-]\s+(.+?)\s*$", re.MULTILINE)
META_LINE = re.compile(
    r"^- (?P<key>Status|Depends on|Wave|GitHub issue|Parent issue|Owner|"
    r"Affected pillars|Write set|AWS mutation|Last updated):\s*(?P<value>.+?)\s*$",
    re.MULTILINE,
)
ALLOWED_STATUSES = {
    "BACKLOG",
    "READY",
    "IN_PROGRESS",
    "BLOCKED",
    "DONE",
    "SKIPPED",
}
ALLOWED_TRANSITIONS = {
    "BACKLOG": {"READY", "BLOCKED", "SKIPPED"},
    "READY": {"BACKLOG", "IN_PROGRESS", "BLOCKED", "SKIPPED"},
    "IN_PROGRESS": {"READY", "BLOCKED", "DONE"},
    "BLOCKED": {"BACKLOG", "READY", "SKIPPED"},
    "DONE": set(),
    "SKIPPED": {"BACKLOG", "READY"},
}


@dataclass
class Task:
    task_id: str
    title: str
    start: int
    end: int
    block: str
    metadata: dict[str, str]

    @property
    def status(self) -> str:
        return clean(self.metadata.get("Status", "")).upper()

    @property
    def dependencies(self) -> list[str]:
        raw = clean(self.metadata.get("Depends on", "NONE"))
        if raw.upper() in {"NONE", "-", ""}:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]

    @property
    def issue(self) -> str:
        return clean(self.metadata.get("GitHub issue", "PENDING_SYNC"))


def clean(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        return value[1:-1]
    return value


def parse_tasks(text: str) -> list[Task]:
    matches = list(TASK_HEADER.finditer(text))
    tasks: list[Task] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        metadata = {m.group("key"): m.group("value") for m in META_LINE.finditer(block)}
        tasks.append(
            Task(
                task_id=match.group(1),
                title=match.group(2).strip(),
                start=start,
                end=end,
                block=block,
                metadata=metadata,
            )
        )
    return tasks


def validate(tasks: list[Task]) -> dict[str, Task]:
    by_id: dict[str, Task] = {}
    errors: list[str] = []

    for task in tasks:
        if task.task_id in by_id:
            errors.append(f"Duplicate task ID: {task.task_id}")
        by_id[task.task_id] = task
        if "Status" not in task.metadata:
            errors.append(f"{task.task_id}: missing Status metadata")
        if "Depends on" not in task.metadata:
            errors.append(f"{task.task_id}: missing Depends on metadata")
        if task.status not in ALLOWED_STATUSES:
            errors.append(
                f"{task.task_id}: invalid status {task.status!r}; "
                f"allowed={sorted(ALLOWED_STATUSES)}"
            )

    for task in tasks:
        for dependency in task.dependencies:
            if dependency not in by_id:
                errors.append(f"{task.task_id}: missing dependency {dependency}")
            if dependency == task.task_id:
                errors.append(f"{task.task_id}: cannot depend on itself")

    if errors:
        raise ValueError("\n".join(errors))
    return by_id


def compute_waves(tasks: list[Task], by_id: dict[str, Task]) -> dict[str, int]:
    waves: dict[str, int] = {}
    visiting: set[str] = set()

    def assign(task_id: str) -> int:
        if task_id in waves:
            return waves[task_id]
        if task_id in visiting:
            cycle = " -> ".join([*visiting, task_id])
            raise ValueError(f"Dependency cycle detected: {cycle}")

        visiting.add(task_id)
        dependencies = by_id[task_id].dependencies
        wave = 1 if not dependencies else 1 + max(assign(dep) for dep in dependencies)
        visiting.remove(task_id)
        waves[task_id] = wave
        return wave

    for task in tasks:
        assign(task.task_id)
    return waves


def ready_tasks(tasks: list[Task], by_id: dict[str, Task]) -> list[Task]:
    ready: list[Task] = []
    for task in tasks:
        if task.status != "READY":
            continue
        if all(by_id[dep].status in {"DONE", "SKIPPED"} for dep in task.dependencies):
            ready.append(task)
    return ready


def replace_metadata(text: str, task: Task, key: str, value: str) -> str:
    block = text[task.start:task.end]
    pattern = re.compile(rf"^- {re.escape(key)}:\s*.+?$", re.MULTILINE)
    replacement = f"- {key}: `{value}`"
    if pattern.search(block):
        new_block = pattern.sub(lambda _match: replacement, block, count=1)
    else:
        header_end = block.find("\n")
        if header_end == -1:
            raise ValueError(f"Malformed task block for {task.task_id}")
        new_block = block[: header_end + 1] + "\n" + replacement + block[header_end + 1 :]
    return text[:task.start] + new_block + text[task.end:]


def validate_status_transition(
    task: Task,
    new_status: str,
    by_id: dict[str, Task],
) -> None:
    if new_status == task.status:
        return
    if new_status not in ALLOWED_TRANSITIONS[task.status]:
        raise ValueError(
            f"{task.task_id}: illegal status transition "
            f"{task.status} -> {new_status}"
        )
    if new_status in {"READY", "IN_PROGRESS", "DONE"}:
        incomplete = [
            dependency
            for dependency in task.dependencies
            if by_id[dependency].status not in {"DONE", "SKIPPED"}
        ]
        if incomplete:
            raise ValueError(
                f"{task.task_id}: cannot become {new_status}; incomplete "
                f"dependencies: {', '.join(incomplete)}"
            )


def atomic_write_text(path: Path, text: str) -> None:
    """Replace a task file atomically while preserving its permission bits."""

    original_mode = stat.S_IMODE(path.stat().st_mode)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def update_task_file(
    path: Path,
    task_id: str,
    *,
    status: str | None = None,
    issue: str | None = None,
) -> bool:
    text = path.read_text(encoding="utf-8")
    tasks = parse_tasks(text)
    by_id = validate(tasks)
    if task_id not in by_id:
        raise ValueError(f"Unknown task ID: {task_id}")

    task = by_id[task_id]
    changed = False
    if status is not None:
        status = status.upper()
        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid status {status!r}; allowed={sorted(ALLOWED_STATUSES)}"
            )
        validate_status_transition(task, status, by_id)
        if status != task.status:
            text = replace_metadata(text, task, "Status", status)
            tasks = parse_tasks(text)
            by_id = validate(tasks)
            task = by_id[task_id]
            changed = True

    if issue is not None:
        issue = issue.strip()
        if not issue or "\n" in issue or "\r" in issue:
            raise ValueError("GitHub issue must be a non-empty single-line value")
        if issue != task.issue:
            text = replace_metadata(text, task, "GitHub issue", issue)
            tasks = parse_tasks(text)
            by_id = validate(tasks)
            task = by_id[task_id]
            changed = True

    if not changed:
        return False

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = replace_metadata(text, task, "Last updated", timestamp)
    final_tasks = parse_tasks(text)
    final_by_id = validate(final_tasks)
    compute_waves(final_tasks, final_by_id)
    atomic_write_text(path, text)
    return True


def task_to_dict(task: Task, wave: int) -> dict[str, object]:
    return {
        "id": task.task_id,
        "title": task.title,
        "status": task.status,
        "dependencies": task.dependencies,
        "wave": wave,
        "github_issue": task.issue,
    }


def print_waves(tasks: list[Task], waves: dict[str, int]) -> None:
    grouped: dict[int, list[Task]] = {}
    for task in tasks:
        grouped.setdefault(waves[task.task_id], []).append(task)

    for wave in sorted(grouped):
        print(f"Wave {wave}")
        for task in grouped[wave]:
            deps = ", ".join(task.dependencies) or "NONE"
            print(
                f"  {task.task_id} [{task.status}] {task.title} "
                f"(depends on: {deps})"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate TASKS.md, sort tasks into execution waves, and update metadata."
    )
    parser.add_argument("tasks_file", type=Path)
    parser.add_argument("--ready", action="store_true", help="Show runtime-ready tasks")
    parser.add_argument("--task", help="Show one task block")
    parser.add_argument(
        "--set-status",
        nargs=2,
        metavar=("TASK_ID", "STATUS"),
        help="Update one task status",
    )
    parser.add_argument(
        "--set-issue",
        nargs=2,
        metavar=("TASK_ID", "ISSUE_URL"),
        help="Link a GitHub Issue",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    path: Path = args.tasks_file
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    try:
        if args.set_status:
            update_task_file(
                path,
                args.set_status[0],
                status=args.set_status[1],
            )
        if args.set_issue:
            update_task_file(
                path,
                args.set_issue[0],
                issue=args.set_issue[1],
            )

        text = path.read_text(encoding="utf-8")
        tasks = parse_tasks(text)
        if not tasks:
            raise ValueError("No task blocks found; expected headings like TASK-001")
        by_id = validate(tasks)
        waves = compute_waves(tasks, by_id)

        if args.task:
            if args.task not in by_id:
                raise ValueError(f"Unknown task ID: {args.task}")
            print(by_id[args.task].block.rstrip())
            return 0

        selected = ready_tasks(tasks, by_id) if args.ready else tasks
        if args.json:
            print(
                json.dumps(
                    [task_to_dict(task, waves[task.task_id]) for task in selected],
                    indent=2,
                )
            )
        elif args.ready:
            if not selected:
                print("No runtime-ready tasks.")
            else:
                print("Runtime-ready tasks")
                for task in selected:
                    print(
                        f"  {task.task_id} [Wave {waves[task.task_id]}] "
                        f"{task.title}"
                    )
        else:
            print_waves(tasks, waves)
        return 0

    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
