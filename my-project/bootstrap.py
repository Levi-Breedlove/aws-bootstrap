#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PLACEHOLDERS = {
    "My AWS Project": "AWS Codex Project",
    "{{AWS_REGION}}": "us-west-2",
    "{{MONTHLY_BUDGET}}": "$50/month",
}

SKIP_NAMES = {".git", "__pycache__"}
SKIP_SUFFIXES = {".zip", ".pyc"}


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


def copy_template(source: Path, target: Path, values: dict[str, str], force: bool) -> None:
    for item in source.rglob("*"):
        relative = item.relative_to(source)

        if any(part in SKIP_NAMES for part in relative.parts):
            continue
        if item.suffix in SKIP_SUFFIXES:
            continue

        destination = target / relative

        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and not force:
            print(f"SKIP  {destination}")
            continue

        if is_text_file(item):
            content = item.read_text(encoding="utf-8")
            destination.write_text(render_text(content, values), encoding="utf-8")
        else:
            shutil.copy2(item, destination)

        print(f"WRITE {destination}")


def main() -> None:
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
    args = parser.parse_args()

    source = Path(__file__).resolve().parent
    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    values = dict(PLACEHOLDERS)
    values["My AWS Project"] = args.project_name
    values["{{AWS_REGION}}"] = args.region
    values["{{MONTHLY_BUDGET}}"] = args.budget

    copy_template(source, target, values, args.force)

    print()
    print("Bootstrap complete.")
    print(f"Project root: {target}")
    print()
    print("Next steps:")
    print("1. Complete PRD.md.")
    print("2. Replace TODO commands in RUNBOOK.md.")
    print("3. Delete irrelevant VERIFY.md rows.")
    print("4. Create a GitHub Project and vertical-slice issues.")
    print("5. Ask Codex to inspect before changing code or AWS.")


if __name__ == "__main__":
    main()
