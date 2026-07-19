#!/usr/bin/env python3
"""Produce owner-run Astral uv setup instructions without executing commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


OFFICIAL_GUIDE = "https://docs.astral.sh/uv/getting-started/installation/"
UV_WINGET_ID = "astral-sh.uv"

Which = Callable[[str], str | None]


class SetupError(RuntimeError):
    """Raised when safe uv setup instructions cannot be produced."""


def canonical_root(root: Path) -> Path:
    resolved = root.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise SetupError("Repository root must be a directory")
    manifest = resolved / "bootstrap.manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise SetupError("bootstrap.manifest.json is missing or unsafe")
    return resolved


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def external_executable_detected(
    name: str,
    root: Path,
    *,
    which: Which = shutil.which,
) -> bool:
    """Detect an external command without executing or exposing its local path."""

    candidate = which(name)
    if not candidate:
        return False
    unresolved = Path(candidate).expanduser()
    try:
        resolved = unresolved.resolve(strict=True)
    except OSError:
        return False
    return resolved.is_file() and not is_within(resolved, root)


def template_tree_sha256(root: Path) -> str:
    manifest = json.loads((root / "bootstrap.manifest.json").read_text(encoding="utf-8"))
    required = manifest.get("required_files")
    if (
        not isinstance(required, list)
        or len(required) != len(set(required))
        or not all(isinstance(item, str) and item for item in required)
    ):
        raise SetupError("Manifest required_files is invalid")
    digest = hashlib.sha256()
    for relative in sorted(required):
        candidate = (root / relative).resolve()
        if not is_within(candidate, root):
            raise SetupError("Manifest path escapes the repository")
        if not candidate.is_file() or candidate.is_symlink():
            raise SetupError(f"Manifest file is missing or unsafe: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(candidate.read_bytes())
    return digest.hexdigest()


def repository_binding(root: Path) -> dict[str, str]:
    """Return non-personal integrity data for the current template tree."""

    return {
        "manifest_sha256": sha256_file(root / "bootstrap.manifest.json"),
        "template_tree_sha256": template_tree_sha256(root),
    }


def owner_install_instruction(
    root: Path,
    *,
    system: str | None = None,
    which: Which = shutil.which,
) -> dict[str, Any]:
    """Choose one precise owner-run command without invoking a package manager."""

    system_name = (system or platform.system()).casefold()
    if system_name == "windows":
        return {
            "method": "WINGET",
            "command": [
                "winget",
                "install",
                "--id",
                UV_WINGET_ID,
                "--exact",
                "--source",
                "winget",
            ],
            "package_manager_detected": external_executable_detected(
                "winget", root, which=which
            ),
        }
    if system_name == "darwin":
        return {
            "method": "HOMEBREW",
            "command": ["brew", "install", "uv"],
            "package_manager_detected": external_executable_detected(
                "brew", root, which=which
            ),
        }
    if external_executable_detected("pipx", root, which=which):
        return {
            "method": "PIPX",
            "command": ["pipx", "install", "uv"],
            "package_manager_detected": True,
        }
    return {
        "method": "OFFICIAL_GUIDE",
        "command": None,
        "package_manager_detected": False,
    }


def build_plan(
    root: Path,
    *,
    which: Which = shutil.which,
    system: str | None = None,
) -> dict[str, Any]:
    root = canonical_root(root)
    common: dict[str, Any] = {
        "schema_version": 1,
        "mode": "INSTRUCTIONS_ONLY",
        "repository": repository_binding(root),
        "official_guide": OFFICIAL_GUIDE,
        "executed": False,
        "repository_writes": "NONE",
        "user_state_persisted_in_repository": False,
        "aws_credentials": "NOT_READ",
        "aws_access": "NOT_USED",
    }
    if external_executable_detected("uvx", root, which=which):
        return {
            **common,
            "state": "UV_DETECTED_OWNER_VERIFICATION_REQUIRED",
            "verification_command": ["uvx", "--version"],
        }

    return {
        **common,
        "state": "UV_INSTALL_INSTRUCTIONS_REQUIRED",
        "owner_install": owner_install_instruction(
            root,
            system=system,
            which=which,
        ),
        "verification_command": ["uvx", "--version"],
        "restart_required_after_owner_install": True,
    }


def print_human(report: Mapping[str, Any]) -> None:
    state = report.get("state", "UNKNOWN")
    if state == "UV_DETECTED_OWNER_VERIFICATION_REQUIRED":
        print("AWS CODEX FASTLANE - UV OWNER VERIFICATION REQUIRED")
        print("Run visibly: uvx --version")
        print("Fastlane did not execute uvx or inspect its local installation.")
        return
    if state == "UV_INSTALL_INSTRUCTIONS_REQUIRED":
        print("AWS CODEX FASTLANE - UV OWNER INSTALLATION REQUIRED")
        instruction = report["owner_install"]
        command = instruction.get("command")
        if command:
            print("Run this command yourself in a visible terminal:")
            print(json.dumps(command, ensure_ascii=False))
        else:
            print("Use the official Astral installation guide for this platform.")
        print(f"Official guide: {report['official_guide']}")
        print("No command, installer, package manager, or verification probe was executed.")
        return
    print(json.dumps(report, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--root", type=Path, default=Path.cwd())
    plan.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_plan(args.root)
    except (SetupError, OSError, json.JSONDecodeError) as exc:
        report = {"schema_version": 1, "state": "BLOCKED", "message": str(exc)}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"Fastlane uv setup blocked: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
