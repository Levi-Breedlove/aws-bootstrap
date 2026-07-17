#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

PLACEHOLDERS = {
    "My AWS Project": "AWS Codex Project",
    "{{AWS_REGION}}": "us-west-2",
    "{{MONTHLY_BUDGET}}": "$50/month",
}

SKIP_NAMES = {".git", "__pycache__"}
SKIP_SUFFIXES = {".zip", ".pyc"}


@dataclass
class CopyReport:
    """Summary of a template copy operation."""

    written: int = 0
    unchanged: int = 0
    collisions: int = 0


def is_text_file(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def render_text(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(key, value)
    return text


def validate_non_overlapping_paths(source: Path, target: Path) -> None:
    """Reject overlapping source and target trees before creating anything."""

    source = source.resolve()
    target = target.resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError(
            "Source and target directories must not overlap: "
            f"source={source}, target={target}"
        )
    if target.exists() and not target.is_dir():
        raise ValueError(f"Target exists and is not a directory: {target}")


def rendered_bytes(path: Path, values: dict[str, str]) -> bytes:
    if is_text_file(path):
        content = path.read_text(encoding="utf-8")
        return render_text(content, values).encode("utf-8")
    return path.read_bytes()


def has_unsafe_parent(target: Path, destination: Path) -> bool:
    """Return true when an existing parent could redirect or block a write."""

    current = target
    for part in destination.relative_to(target).parts[:-1]:
        current = current / part
        if current.is_symlink():
            return True
        if current.exists() and not current.is_dir():
            return True
    return False


def atomic_write_bytes(destination: Path, content: bytes, source: Path) -> None:
    """Write one generated file atomically in its destination directory."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        shutil.copymode(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def copy_template(
    source: Path,
    target: Path,
    values: dict[str, str],
    force: bool,
    *,
    dry_run: bool = False,
) -> CopyReport:
    source = source.resolve()
    target = target.resolve()
    validate_non_overlapping_paths(source, target)

    # Snapshot the source before any target write. This is a second line of
    # defense against a changing traversal and makes the operation predictable.
    items = sorted(source.rglob("*"), key=lambda path: path.relative_to(source).parts)
    report = CopyReport()

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for item in items:
        relative = item.relative_to(source)

        if any(part in SKIP_NAMES for part in relative.parts):
            continue
        if item.suffix in SKIP_SUFFIXES:
            continue

        destination = target / relative

        if item.is_dir():
            if destination.is_symlink() or (
                destination.exists() and not destination.is_dir()
            ):
                print(f"COLLISION {destination}")
                report.collisions += 1
            elif not dry_run:
                destination.mkdir(parents=True, exist_ok=True)
            continue

        if has_unsafe_parent(target, destination):
            print(f"COLLISION {destination}")
            report.collisions += 1
            continue

        content = rendered_bytes(item, values)
        if destination.is_symlink() or (
            destination.exists() and not destination.is_file()
        ):
            print(f"COLLISION {destination}")
            report.collisions += 1
            continue

        if destination.exists():
            try:
                unchanged = destination.read_bytes() == content
            except OSError:
                unchanged = False
            if unchanged:
                print(f"UNCHANGED {destination}")
                report.unchanged += 1
                continue
            if not force:
                print(f"COLLISION {destination}")
                report.collisions += 1
                continue

        action = "OVERWRITE" if destination.exists() else "WRITE"
        if not dry_run:
            atomic_write_bytes(destination, content, item)
        print(f"{action} {destination}")
        report.written += 1

    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a lightweight AWS Well-Architected Codex project."
    )
    parser.add_argument("--target", required=True, help="Target project directory")
    parser.add_argument("--project-name", required=True, help="Human-readable project name")
    parser.add_argument("--region", default="us-west-2", help="Primary AWS Region")
    parser.add_argument(
        "--budget",
        default="$50/month",
        help='Monthly cost ceiling, for example "$50/month"',
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing bootstrap files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview writes and collisions without changing the target",
    )
    args = parser.parse_args(argv)

    source = Path(__file__).resolve().parent
    target = Path(args.target).expanduser().resolve()

    values = dict(PLACEHOLDERS)
    values["My AWS Project"] = args.project_name
    values["{{AWS_REGION}}"] = args.region
    values["{{MONTHLY_BUDGET}}"] = args.budget

    try:
        report = copy_template(
            source,
            target,
            values,
            args.force,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError) as exc:
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 2

    print()
    if args.dry_run:
        print("Dry run complete. No files were changed.")
    elif report.collisions:
        print("Bootstrap stopped with preserved file collisions.")
    else:
        print("Bootstrap complete.")
    print(f"Project root: {target}")
    print(
        f"Summary: {report.written} write(s), {report.unchanged} unchanged, "
        f"{report.collisions} collision(s)"
    )

    if report.collisions:
        print("Re-run with --force only after reviewing every collision.")
        return 1

    if args.dry_run:
        return 0

    print()
    print("Next steps:")
    print("1. Complete PRD.md.")
    print("2. Replace TODO commands in RUNBOOK.md.")
    print("3. Delete irrelevant VERIFY.md rows.")
    print("4. Create a GitHub Project and vertical-slice issues.")
    print("5. Ask Codex to inspect before changing code or AWS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
