#!/usr/bin/env python3
"""Render Fastlane's short, instruction-only first-run guidance.

BOOT-00 never installs software, changes Codex plugin state, trusts hooks,
reads credentials, or accesses AWS. AWS Core is helpful during AWS design, but
its absence never blocks project intake.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


OFFICIAL_AWS_MARKETPLACE = "aws/agent-toolkit-for-aws"
OFFICIAL_AWS_MARKETPLACE_NAME = "agent-toolkit-for-aws"
OFFICIAL_AWS_CORE_IDENTITY = "aws-core@agent-toolkit-for-aws"

CODEX_GUIDE = "https://learn.chatgpt.com/docs/codex/cli#getting-started"
CODEX_PLUGIN_GUIDE = "https://learn.chatgpt.com/docs/plugins"
UV_GUIDE = "https://docs.astral.sh/uv/getting-started/installation/"
PYTHON_GUIDE = "https://www.python.org/downloads/"
GIT_GUIDE = "https://git-scm.com/downloads"
AWS_PLUGIN_GUIDE = (
    "https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html"
)

MARKETPLACE_COMMAND = "codex plugin marketplace add aws/agent-toolkit-for-aws"

SETUP_STATES = ("LOCAL_PREREQUISITES_REQUIRED", "READY_FOR_INTAKE")
SUPPORTED_PLUGIN_SURFACES = {
    "CODEX_CLI",
    "CHATGPT_DESKTOP_CODEX",
    "CHATGPT_DESKTOP_WORK",
    "CHATGPT_WEB_WORK",
}

BOOLEAN_OR_NULL_EVIDENCE_FIELDS = frozenset(
    {
        "dependencies_ready",
        "doctor_passed",
        "official_marketplace_registered",
        "official_plugin_installed",
        "official_plugin_enabled",
        "official_plugin_loaded_in_session",
        "official_plugin_source_verified",
    }
)
STRING_OR_NULL_EVIDENCE_FIELDS = frozenset(
    {
        "gate_a_state",
        "gate_b_state",
        "lifecycle_stage",
        "observed_marketplace_repository",
        "observed_plugin_source",
        "observed_plugin_identity",
    }
)
STRING_LIST_EVIDENCE_FIELDS = frozenset({"unknown_plugin_sources"})
SESSION_EVIDENCE_FIELDS = frozenset(
    BOOLEAN_OR_NULL_EVIDENCE_FIELDS
    | STRING_OR_NULL_EVIDENCE_FIELDS
    | STRING_LIST_EVIDENCE_FIELDS
)

Which = Callable[[str], str | None]
MAX_EVIDENCE_BYTES = 1_000_000


class SetupError(RuntimeError):
    """Raised when setup input is missing, malformed, or unsafe."""


def read_session_evidence(stream: Any) -> dict[str, Any]:
    """Read allowlisted, non-sensitive observations without persisting them."""

    payload = stream.read(MAX_EVIDENCE_BYTES + 1)
    if not isinstance(payload, str) or not payload.strip():
        raise SetupError("--evidence-stdin requires one JSON object on stdin")
    if len(payload.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        raise SetupError("stdin evidence exceeds the 1 MB limit")
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SetupError("stdin evidence is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise SetupError("stdin evidence must be a JSON object")
    unknown = sorted(set(parsed) - SESSION_EVIDENCE_FIELDS)
    if unknown:
        raise SetupError(
            "stdin evidence contains unknown field(s): " + ", ".join(unknown)
        )
    for key, value in parsed.items():
        if key in BOOLEAN_OR_NULL_EVIDENCE_FIELDS:
            valid = value is None or isinstance(value, bool)
        elif key in STRING_OR_NULL_EVIDENCE_FIELDS:
            valid = value is None or isinstance(value, str)
        else:
            valid = (
                isinstance(value, list)
                and all(isinstance(item, str) and bool(item.strip()) for item in value)
            )
        if not valid:
            raise SetupError(f"stdin evidence field {key!r} has an invalid value")
        if key == "lifecycle_stage" and value is not None:
            if not re.fullmatch(r"(?:[A-Z]+-[0-9]+|STOP)", value):
                raise SetupError("lifecycle_stage must be a canonical prompt ID or STOP")
        if key in {"gate_a_state", "gate_b_state"} and value is not None:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", value):
                raise SetupError(f"stdin evidence field {key!r} is not a state token")
    return dict(parsed)


def canonical_root(root: Path) -> Path:
    """Resolve a repository root with a safe Fastlane manifest."""

    try:
        resolved = root.expanduser().resolve(strict=True)
    except OSError as exc:
        raise SetupError("Repository root does not exist") from exc
    if not resolved.is_dir():
        raise SetupError("Repository root must be a directory")
    manifest = resolved / "bootstrap.manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise SetupError("bootstrap.manifest.json is missing or unsafe")
    try:
        parsed = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SetupError("bootstrap.manifest.json is unreadable or invalid") from exc
    if not isinstance(parsed, dict):
        raise SetupError("bootstrap.manifest.json must contain an object")
    return resolved


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
    """Detect an external PATH command without executing or exposing its path."""

    candidate = which(name)
    if not candidate:
        return False
    try:
        resolved = Path(candidate).expanduser().resolve(strict=True)
    except OSError:
        return False
    return resolved.is_file() and not is_within(resolved, root)


def inspect_local_prerequisites(
    root: Path,
    *,
    which: Which = shutil.which,
    python_version: Sequence[int] | None = None,
    system: str | None = None,
    surface: str | None = None,
) -> dict[str, Any]:
    """Return safe local observations without running external commands."""

    checked_root = canonical_root(root)
    version = tuple(python_version or sys.version_info[:3])
    system_name = (system or platform.system()).upper()
    normalized_surface = surface.strip().upper() if surface else "UNKNOWN"
    python_on_path = external_executable_detected("python", checked_root, which=which)
    python3_on_path = external_executable_detected("python3", checked_root, which=which)
    fastlane_python_command = (
        "python"
        if system_name.startswith("WINDOWS") or python_on_path
        else "python3"
    )
    return {
        "repository_ready": True,
        "dependencies_ready": None,
        "doctor_passed": None,
        "git_available": external_executable_detected("git", checked_root, which=which),
        "python_available": True,
        "python_version_supported": version >= (3, 11),
        "fastlane_python_command": fastlane_python_command,
        "system": system_name,
        "surface": normalized_surface,
        "plugin_management_available": (
            normalized_surface in SUPPORTED_PLUGIN_SURFACES
            if normalized_surface != "UNKNOWN"
            else None
        ),
        "official_marketplace_registered": None,
        "official_plugin_installed": None,
        "official_plugin_enabled": None,
        "official_plugin_loaded_in_session": None,
    }


def _report(
    state: str,
    *,
    observed: str,
    owner_action: str,
    owner_command: str | None,
    verification: str,
    aws_core_status: str,
    stage: str = "BOOT-00",
    gate_a_state: str = "BLOCKED",
    gate_b_state: str = "BLOCKED",
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if state not in SETUP_STATES:
        raise ValueError(f"Unknown setup state: {state}")
    report: dict[str, Any] = {
        "schema_version": 3,
        "mode": "INSTRUCTIONS_ONLY",
        "state": state,
        "stage": stage,
        "gate_a_state": gate_a_state,
        "gate_b_state": gate_b_state,
        "progress_step": (
            "Project setup complete"
            if state == "READY_FOR_INTAKE"
            else "Project setup"
        ),
        "observed": observed,
        "owner_action_id": (
            "BEGIN_INTAKE_NOW"
            if state == "READY_FOR_INTAKE" and stage == "INTAKE-10"
            else "RESUME_DERIVED_STAGE"
            if state == "READY_FOR_INTAKE"
            else "FIX_LOCAL_PREREQUISITE"
        ),
        "owner_action": owner_action,
        "owner_command": owner_command,
        "verification": verification,
        "resume_with": (
            "IN_CURRENT_RESPONSE"
            if state == "READY_FOR_INTAKE"
            else "init template"
        ),
        "aws_core_status": aws_core_status,
        "aws_credentials": "NOT_CONFIGURED_OR_CHECKED",
        "aws_access": "NOT_USED",
        "aws_authorization": "NOT_GRANTED_BY_SETUP",
        "executed_external_commands": False,
        "repository_writes": "NONE",
        "user_state_persisted_in_repository": False,
    }
    if details:
        report["details"] = dict(details)
    return report


def _local_block(evidence: Mapping[str, Any]) -> dict[str, Any] | None:
    checks = (
        (
            "repository_ready",
            "The Fastlane repository or manifest is incomplete.",
            "Open a complete Fastlane repository and try again.",
            None,
            "bootstrap.manifest.json is present and readable.",
        ),
        (
            "git_available",
            "Git was not detected.",
            f"Install Git from {GIT_GUIDE}.",
            None,
            "Run git --version.",
        ),
        (
            "python_available",
            "Python was not detected.",
            f"Install Python 3.11 or newer from {PYTHON_GUIDE}.",
            None,
            "Run python --version or python3 --version.",
        ),
        (
            "python_version_supported",
            "Fastlane is running with Python older than 3.11.",
            f"Install Python 3.11 or newer from {PYTHON_GUIDE}.",
            None,
            "The Fastlane Python reports version 3.11 or newer.",
        ),
        (
            "dependencies_ready",
            "The repository dependency check has not passed.",
            "Run the read-only dependency check.",
            "python scripts/bootstrap_dependencies.py --root . --json",
            "The dependency report status is READY.",
        ),
        (
            "doctor_passed",
            "The initialized project doctor has not passed.",
            "Run the read-only project doctor.",
            "python scripts/bootstrap_doctor.py --root . --json",
            "The project doctor status is PASS.",
        ),
    )
    for key, observed, action, command, verification in checks:
        if evidence.get(key) is not True:
            return _report(
                "LOCAL_PREREQUISITES_REQUIRED",
                observed=observed,
                owner_action=action,
                owner_command=command,
                verification=verification,
                aws_core_status="NOT_CHECKED",
            )
    return None


def _aws_core_summary(evidence: Mapping[str, Any]) -> tuple[str, str, dict[str, Any]]:
    official_ready = all(
        evidence.get(key) is True
        for key in (
            "official_plugin_enabled",
            "official_plugin_loaded_in_session",
            "official_plugin_source_verified",
        )
    ) and (
        evidence.get("observed_marketplace_repository") == OFFICIAL_AWS_MARKETPLACE
        and evidence.get("observed_plugin_source") == OFFICIAL_AWS_MARKETPLACE_NAME
        and evidence.get("observed_plugin_identity") == OFFICIAL_AWS_CORE_IDENTITY
    )
    unknown = evidence.get("unknown_plugin_sources")
    unknown_sources = (
        sorted({item for item in unknown if isinstance(item, str) and item.strip()})
        if isinstance(unknown, list)
        else []
    )
    if official_ready and not unknown_sources:
        return (
            "AVAILABLE",
            "Official AWS Core is available for later AWS design work.",
            {"plugin_identity": OFFICIAL_AWS_CORE_IDENTITY},
        )
    if unknown_sources:
        return (
            "DEFERRED_UNTIL_DESIGN",
            (
                "AWS Core is present from an unverified source. Intake can continue; "
                "the official source will be required before AWS design."
            ),
            {"unknown_plugin_sources": unknown_sources},
        )
    return (
        "DEFERRED_UNTIL_DESIGN",
        (
            "Official AWS Core is not available in this session. Intake can continue; "
            "Fastlane will give one setup step before AWS design."
        ),
        {
            "official_marketplace": OFFICIAL_AWS_MARKETPLACE,
            "marketplace_command": MARKETPLACE_COMMAND,
        },
    )


def reduce_setup(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Return the first local blocker, otherwise route directly to intake."""

    local = _local_block(evidence)
    if local is not None:
        return local
    aws_core_status, observed, details = _aws_core_summary(evidence)
    stage = str(evidence.get("lifecycle_stage") or "INTAKE-10")
    gate_a_state = str(evidence.get("gate_a_state") or "PENDING")
    gate_b_state = str(evidence.get("gate_b_state") or "BLOCKED_BY_GATE_A")
    next_action = (
        "Answer the guided intake questions below."
        if stage == "INTAKE-10"
        else f"Continue {stage} now."
    )
    return _report(
        "READY_FOR_INTAKE",
        observed=observed,
        owner_action=next_action,
        owner_command=None,
        verification=f"The doctor routes to {stage}.",
        aws_core_status=aws_core_status,
        stage=stage,
        gate_a_state=gate_a_state,
        gate_b_state=gate_b_state,
        details=details,
    )


def opening_greeting() -> str:
    return """Welcome to AWS Codex Fastlane.

Fastlane turns your idea into owner-approved requirements and an AWS-informed
technical design. You approve requirements at Gate A and the technical PRD and
build boundary at Gate B. Setup does not inspect credentials or access AWS.
AWS Core can be connected later if current AWS guidance is needed.

Reply once with:
- Project name:
- Preferred AWS Region: (or "recommend one")
- Development budget: (a currency cap, or "minimize cost; no hard cap")"""


def render_routine_status(report: Mapping[str, Any]) -> str:
    """Render the exact concise status used for setup and resume."""

    command = report.get("owner_command")
    next_action = str(report["owner_action"])
    if command:
        next_action = f"Run `{command}`, then send `init template`."
    return "\n".join(
        [
            "FASTLANE STATUS",
            f"Stage: {report['stage']}",
            f"Gate A: {report['gate_a_state']}",
            f"Gate B: {report['gate_b_state']}",
            f"AWS Core: {report['aws_core_status']}",
            f"AWS access: {str(report['aws_access']).replace('_', ' ')}",
            f"Next action: {next_action}",
        ]
    )


def render_setup_response(report: Mapping[str, Any]) -> str:
    """Render a compact owner-facing setup result."""

    return render_routine_status(report)


def build_guide(root: Path, *, system: str | None = None) -> dict[str, Any]:
    """Build optional owner-run guidance for AWS Core design support."""

    canonical_root(root)
    system_name = (system or platform.system()).upper()
    if system_name.startswith("WINDOWS"):
        uv_install = "winget install --id astral-sh.uv --exact --source winget"
    elif system_name == "DARWIN":
        uv_install = "brew install uv"
    else:
        uv_install = "pipx install uv"
    steps: list[dict[str, Any]] = [
        {
            "name": "Codex CLI",
            "guide": CODEX_GUIDE,
            "verify": "codex --version",
        }
    ]
    if not system_name.startswith("WINDOWS") and system_name != "DARWIN":
        steps.append(
            {
                "name": "Codex Linux sandbox",
                "owner_commands": [
                    "sudo apt update",
                    "sudo apt install bubblewrap",
                    "command -v bwrap",
                    "bwrap --version",
                ],
                "verify": "command -v bwrap && bwrap --version",
            }
        )
    steps.extend(
        [
            {
                "name": "Codex login",
                "owner_action": "codex login",
                "verify": "codex login status",
            },
            {
                "name": "Astral uv",
                "guide": UV_GUIDE,
                "owner_install": uv_install,
                "verify": "uvx --version",
            },
            {
                "name": "Official AWS Agent Toolkit",
                "guide": AWS_PLUGIN_GUIDE,
                "owner_action": MARKETPLACE_COMMAND,
                "verify": (
                    "Open /plugins and enable AWS Core only under Agent Toolkit for AWS"
                ),
            },
            {
                "name": "Resume",
                "owner_action": "Restart Codex after plugin changes.",
                "verify": "Return to the project and continue AWS design",
            },
        ]
    )
    return {
        "schema_version": 2,
        "mode": "INSTRUCTIONS_ONLY",
        "system": system_name,
        "executed_external_commands": False,
        "repository_writes": "NONE",
        "user_state_persisted_in_repository": False,
        "aws_credentials": "NOT_CONFIGURED_OR_CHECKED",
        "aws_access": "NOT_USED",
        "steps": steps,
    }


def render_guide(guide: Mapping[str, Any]) -> str:
    lines = [
        "Optional AWS Core setup",
        "",
        "Use this before AWS-specific design. Project intake does not wait for it.",
        "",
    ]
    for index, step in enumerate(guide["steps"], start=1):
        lines.append(f"{index}. {step['name']}")
        if step.get("owner_install"):
            lines.append(f"   Install: {step['owner_install']}")
        if step.get("owner_action"):
            lines.append(f"   Action: {step['owner_action']}")
        for command in step.get("owner_commands", []):
            lines.append(f"   Run: {command}")
        if step.get("guide"):
            lines.append(f"   Official guide: {step['guide']}")
        lines.append(f"   Verify: {step['verify']}")
        lines.append("")
    lines.append(
        "These are owner-run instructions. Fastlane changed no plugin, login, hook, "
        "credential, or AWS state."
    )
    return "\n".join(lines)


def _error_report(message: str) -> dict[str, Any]:
    return _report(
        "LOCAL_PREREQUISITES_REQUIRED",
        observed=message,
        owner_action="Open a complete Fastlane repository and try again.",
        owner_command=None,
        verification="bootstrap.manifest.json is present and readable.",
        aws_core_status="NOT_CHECKED",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("welcome", help="Print the exact Fastlane welcome")

    status = subparsers.add_parser("status", help="Inspect safe local setup state")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--surface")
    status.add_argument("--json", action="store_true")
    status.add_argument("--evidence-stdin", action="store_true")

    guide = subparsers.add_parser("guide", help="Print optional AWS Core guidance")
    guide.add_argument("--root", type=Path, default=Path.cwd())

    args = parser.parse_args(argv)
    if args.command == "welcome":
        print(opening_greeting())
        return 0
    try:
        if args.command == "guide":
            print(render_guide(build_guide(args.root)))
            return 0
        evidence = inspect_local_prerequisites(args.root, surface=args.surface)
        if args.evidence_stdin:
            evidence.update(read_session_evidence(sys.stdin))
        report = reduce_setup(evidence)
        report["local_checks"] = {
            key: evidence[key]
            for key in (
                "git_available",
                "python_available",
                "python_version_supported",
                "plugin_management_available",
            )
        }
    except SetupError as exc:
        report = _error_report(str(exc))
        if getattr(args, "json", False):
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(render_setup_response(report), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_setup_response(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
