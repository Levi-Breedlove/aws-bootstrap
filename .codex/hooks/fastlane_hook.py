#!/usr/bin/env python3
"""Optional Fastlane lifecycle guardrails for native Codex hooks.

This module is intentionally standard-library-only. It reads one bounded JSON
event from stdin, emits only Codex hook JSON, and never writes project or client
state. Fastlane's doctor and project contracts remain authoritative.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


MAX_EVENT_BYTES = 1_048_576
MAX_CONTEXT_CHARS = 280
EVENT_NAMES = {
    "session-start": "SessionStart",
    "pre-tool-use": "PreToolUse",
    "permission-request": "PermissionRequest",
    "post-tool-use": "PostToolUse",
    "stop": "Stop",
}

AWS_DOCUMENTATION_MARKERS = (
    "retrieve_skill",
    "search_documentation",
    "read_documentation",
)
AWS_EXTERNAL_TOOL_MARKERS = (
    "call_aws",
    "run_script",
    "use_aws",
    "execute_aws",
    "aws_api",
)
AWS_MUTATION_COMMANDS = (
    "cdk deploy",
    "cdk destroy",
    "sam deploy",
    "sam delete",
    "serverless deploy",
    "serverless remove",
    "terraform apply",
    "terraform destroy",
    "cloudformation deploy",
    "cloudformation execute-change-set",
    "cloudformation delete-stack",
)
AWS_READ_PREFIXES = (
    "batch_get",
    "describe",
    "detect",
    "get",
    "head",
    "list",
    "lookup",
    "preview",
    "search",
    "validate",
)
GITHUB_TOOL_MARKERS = (
    "add_issue_comment",
    "create_branch",
    "create_commit",
    "create_issue",
    "create_or_update_file",
    "create_pull_request",
    "create_ref",
    "create_release",
    "delete_ref",
    "merge_pull_request",
    "push_files",
    "request_review",
    "update_issue",
    "update_ref",
    "upload_release",
)
PATH_KEYS = {
    "cwd",
    "directory",
    "file",
    "file_path",
    "path",
    "root",
    "target",
    "target_file",
    "workdir",
}
PATCH_PATH = re.compile(r"^\*\*\* (?:Add|Delete|Update) File: (.+)$", re.MULTILINE)
GITHUB_BOUNDARIES = {"NONE", "READ_ONLY", "ISSUES", "BRANCH_AND_PR", "MERGE_WHEN_GREEN"}
AWS_BOUNDARIES = {"NONE", "DOCS_ONLY", "READ_ONLY", "MUTATE_LISTED_RESOURCES"}


class HookInputError(ValueError):
    """Raised when a native hook event is malformed or too large."""


def read_event(stream: Any) -> dict[str, Any]:
    """Read one bounded UTF-8 JSON object without retaining its raw bytes."""

    raw = stream.buffer.read(MAX_EVENT_BYTES + 1) if hasattr(stream, "buffer") else stream.read(MAX_EVENT_BYTES + 1)
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if len(raw) > MAX_EVENT_BYTES:
        raise HookInputError("event exceeds the Fastlane hook size limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HookInputError("event is not a valid UTF-8 JSON object") from exc
    if not isinstance(payload, dict):
        raise HookInputError("event must be a JSON object")
    return payload


def resolve_repository_root(cwd: str | os.PathLike[str]) -> Path:
    """Resolve the Fastlane root without trusting the current subdirectory."""

    start = Path(cwd).resolve()
    if start.is_file():
        start = start.parent
    for candidate in (start, *start.parents):
        if (
            (candidate / "bootstrap.manifest.json").is_file()
            and (candidate / "scripts" / "bootstrap_doctor.py").is_file()
        ):
            return candidate
    raise HookInputError("Fastlane repository root could not be resolved")


def _bounded_text(value: object, limit: int = MAX_CONTEXT_CHARS) -> str:
    text = " ".join(str(value).split())
    return text[:limit]


def _doctor_command(root: Path) -> list[str]:
    return [
        sys.executable,
        str(root / "scripts" / "bootstrap_doctor.py"),
        "--root",
        str(root),
        "--json",
    ]


def run_doctor(root: Path) -> dict[str, Any]:
    """Run the existing doctor read-only and return only its JSON report."""

    completed = subprocess.run(
        _doctor_command(root),
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise HookInputError("Fastlane doctor did not return JSON") from exc
    if not isinstance(report, dict):
        raise HookInputError("Fastlane doctor returned an invalid report")
    return report


def load_construction_envelope(root: Path) -> dict[str, str]:
    """Reuse the doctor's canonical PRD table parser instead of defining one."""

    scripts = str(root / "scripts")
    inserted = scripts not in sys.path
    if inserted:
        sys.path.insert(0, scripts)
    try:
        import bootstrap_doctor  # type: ignore[import-not-found]

        text = (root / "docs" / "project" / "PRD.md").read_text(encoding="utf-8")
        envelope = bootstrap_doctor.table_after_heading(
            text, "## 28. Construction envelope"
        )
    finally:
        if inserted:
            sys.path.remove(scripts)
    return envelope if isinstance(envelope, dict) else {}


def _event_tool(payload: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(name, str) or not name.strip():
        raise HookInputError("tool event is missing tool_name")
    if not isinstance(tool_input, Mapping):
        raise HookInputError("tool event is missing a JSON tool_input object")
    return name, tool_input


def _tool_command(tool_input: Mapping[str, Any]) -> str:
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _candidate_paths(tool_input: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key, value in tool_input.items():
        if key.casefold() in PATH_KEYS and isinstance(value, str):
            values.append(value)
    command = _tool_command(tool_input)
    values.extend(match.strip() for match in PATCH_PATH.findall(command))
    return values


def _outside_write_boundary(
    tool_name: str,
    tool_input: Mapping[str, Any],
    root: Path,
    cwd: Path,
) -> bool:
    if tool_name.casefold() not in {"apply_patch", "edit", "write"}:
        return False
    for raw in _candidate_paths(tool_input):
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = cwd / candidate
        try:
            resolved = candidate.resolve(strict=False)
        except OSError:
            return True
        if not _is_within(resolved, root):
            return True
    return False


def _is_aws_documentation_tool(tool_name: str) -> bool:
    lowered = tool_name.casefold()
    return any(marker in lowered for marker in AWS_DOCUMENTATION_MARKERS)


def _aws_request_kind(tool_name: str, tool_input: Mapping[str, Any]) -> str | None:
    """Return READ, MUTATE, or None for attributable AWS operations."""

    if _is_aws_documentation_tool(tool_name):
        return None
    lowered_name = tool_name.casefold()
    command = _tool_command(tool_input).casefold()
    if any(marker in command for marker in AWS_MUTATION_COMMANDS):
        return "MUTATE"
    if any(marker in lowered_name for marker in AWS_EXTERNAL_TOOL_MARKERS):
        operation = ""
        for key in ("operation", "operation_name", "api", "action"):
            value = tool_input.get(key)
            if isinstance(value, str):
                operation = value.casefold().replace("-", "_")
                break
        if operation and operation.startswith(AWS_READ_PREFIXES):
            return "READ"
        return "MUTATE"
    if re.search(r"(?:^|[;&|]\s*)aws(?:\.exe)?\s+", command):
        tokens = re.findall(r"[a-z0-9_-]+", command)
        operation = tokens[2] if len(tokens) > 2 else ""
        return "READ" if operation.startswith(AWS_READ_PREFIXES) else "MUTATE"
    return None


def _github_request_kind(tool_name: str, tool_input: Mapping[str, Any]) -> str | None:
    lowered_name = tool_name.casefold()
    command = _tool_command(tool_input).casefold()
    marker = next((item for item in GITHUB_TOOL_MARKERS if item in lowered_name), None)
    if marker:
        if "merge" in marker or "release" in marker or "delete_ref" in marker:
            return "MERGE"
        if "issue" in marker or "comment" in marker:
            return "ISSUE"
        return "BRANCH_PR"
    if re.search(r"(?:^|[;&|]\s*)git\s+push(?:\s|$)", command):
        return "BRANCH_PR"
    if re.search(r"(?:^|[;&|]\s*)gh\s+(?:pr\s+merge|release\s+)", command):
        return "MERGE"
    if re.search(r"(?:^|[;&|]\s*)gh\s+issue\s+", command):
        return "ISSUE"
    if re.search(r"(?:^|[;&|]\s*)gh\s+pr\s+create(?:\s|$)", command):
        return "BRANCH_PR"
    if re.search(r"(?:^|[;&|]\s*)gh\s+api(?:\s|$)", command):
        mutating_method = re.search(
            r"(?:--method|-X)(?:=|\s+)(?:POST|PUT|PATCH|DELETE)(?:\s|$)",
            command,
            re.IGNORECASE,
        )
        form_field = re.search(r"(?:^|\s)(?:-f|-F|--field|--raw-field)(?:=|\s)", command)
        if mutating_method or form_field:
            return "BRANCH_PR"
    return None


def _authority_denial(
    tool_name: str,
    tool_input: Mapping[str, Any],
    report: Mapping[str, Any],
    envelope: Mapping[str, str],
    root: Path,
    cwd: Path,
) -> str | None:
    if _outside_write_boundary(tool_name, tool_input, root, cwd):
        return "Fastlane blocked a write outside the current repository boundary."

    authorizations = report.get("authorizations")
    if not isinstance(authorizations, Mapping):
        authorizations = {}
    aws_authorization = str(authorizations.get("aws", "NONE"))
    construction_authorization = str(authorizations.get("construction", "NONE"))
    aws_boundary = str(envelope.get("AWS boundary", "NONE"))
    github_boundary = str(envelope.get("GitHub boundary", "NONE"))
    if aws_boundary not in AWS_BOUNDARIES:
        aws_boundary = "NONE"
    if github_boundary not in GITHUB_BOUNDARIES:
        github_boundary = "NONE"

    aws_kind = _aws_request_kind(tool_name, tool_input)
    if aws_kind == "READ" and (
        aws_authorization == "NONE"
        or aws_boundary not in {"READ_ONLY", "MUTATE_LISTED_RESOURCES"}
    ):
        return "Fastlane blocked AWS account access because current AWS authority is absent."
    if aws_kind == "MUTATE" and (
        aws_authorization == "NONE" or aws_boundary != "MUTATE_LISTED_RESOURCES"
    ):
        return "Fastlane blocked AWS mutation or teardown because exact current AWS authority is absent."

    github_kind = _github_request_kind(tool_name, tool_input)
    if github_kind is not None and construction_authorization == "NONE":
        return "Fastlane blocked GitHub publication because current construction authority is absent."
    allowed_github = {
        "ISSUE": {"ISSUES", "BRANCH_AND_PR", "MERGE_WHEN_GREEN"},
        "BRANCH_PR": {"BRANCH_AND_PR", "MERGE_WHEN_GREEN"},
        "MERGE": {"MERGE_WHEN_GREEN"},
    }
    if github_kind is not None and github_boundary not in allowed_github[github_kind]:
        return "Fastlane blocked GitHub publication because it exceeds the current GitHub boundary."
    return None


def _broad_escalation(payload: Mapping[str, Any], tool_input: Mapping[str, Any]) -> bool:
    if str(payload.get("permission_mode", "")).casefold() == "bypasspermissions":
        return True
    description = tool_input.get("description")
    if not isinstance(description, str):
        return False
    lowered = description.casefold()
    return any(
        marker in lowered
        for marker in (
            "bypass approvals",
            "disable sandbox",
            "full disk access",
            "unrestricted access",
        )
    )


def pre_tool_denial(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": _bounded_text(reason),
        }
    }


def permission_denial(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "deny",
                "message": _bounded_text(reason),
            },
        }
    }


def _session_context(report: Mapping[str, Any]) -> str:
    gates = report.get("gates") if isinstance(report.get("gates"), Mapping) else {}
    interaction = (
        report.get("interaction")
        if isinstance(report.get("interaction"), Mapping)
        else {}
    )
    authorizations = (
        report.get("authorizations")
        if isinstance(report.get("authorizations"), Mapping)
        else {}
    )
    return _bounded_text(
        "Fastlane optional guardrail context: "
        f"stage={interaction.get('owner_stage', 'UNKNOWN')}; "
        f"Gate A={gates.get('gate_a', 'UNKNOWN')}; "
        f"Gate B={gates.get('gate_b', 'UNKNOWN')}; "
        f"AWS authority={authorizations.get('aws', 'NONE')}; "
        f"owner action={interaction.get('owner_action_kind', 'UNKNOWN')}. "
        "Hooks are defense in depth and grant no authority."
    )


def _run_validation(root: Path, command: Sequence[str]) -> bool:
    completed = subprocess.run(
        list(command),
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60,
        check=False,
    )
    return completed.returncode == 0


def _post_validation(
    tool_name: str,
    tool_input: Mapping[str, Any],
    root: Path,
    runner: Callable[[Path, Sequence[str]], bool],
) -> str | None:
    command = _tool_command(tool_input)
    lowered_name = tool_name.casefold()
    if lowered_name in {"apply_patch", "edit", "write"}:
        if not runner(root, ["git", "diff", "--check"]):
            return "Fastlane validation found a diff-format problem. Run git diff --check."
    if "update_manifest.py" in command and "--write" in command:
        check = [
            sys.executable,
            str(root / "scripts" / "update_manifest.py"),
            "--check",
        ]
        if not runner(root, check):
            return "Fastlane manifest validation did not pass. Run the manifest check before continuing."
    return None


def handle_event(
    event_key: str,
    payload: Mapping[str, Any],
    *,
    root: Path | None = None,
    doctor_report: Mapping[str, Any] | None = None,
    envelope: Mapping[str, str] | None = None,
    validation_runner: Callable[[Path, Sequence[str]], bool] = _run_validation,
) -> dict[str, Any] | None:
    expected = EVENT_NAMES.get(event_key)
    if expected is None:
        raise HookInputError("unknown Fastlane hook event")
    if payload.get("hook_event_name") != expected:
        raise HookInputError("hook_event_name does not match the configured handler")
    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value:
        raise HookInputError("hook event is missing cwd")
    cwd = Path(cwd_value).resolve()
    root = root.resolve() if root is not None else resolve_repository_root(cwd)

    if event_key == "session-start":
        report = doctor_report or run_doctor(root)
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": _session_context(report),
            }
        }

    if event_key in {"pre-tool-use", "permission-request"}:
        tool_name, tool_input = _event_tool(payload)
        report = doctor_report or run_doctor(root)
        authority_envelope = envelope or load_construction_envelope(root)
        reason = _authority_denial(
            tool_name, tool_input, report, authority_envelope, root, cwd
        )
        if event_key == "permission-request" and reason is None and _broad_escalation(payload, tool_input):
            reason = "Fastlane blocked a broad escalation that exceeds the current project boundary."
        if reason is None:
            return None
        return pre_tool_denial(reason) if event_key == "pre-tool-use" else permission_denial(reason)

    if event_key == "post-tool-use":
        tool_name, tool_input = _event_tool(payload)
        message = _post_validation(tool_name, tool_input, root, validation_runner)
        return {"systemMessage": message} if message else None

    if bool(payload.get("stop_hook_active")):
        return None
    report = doctor_report or run_doctor(root)
    interaction = report.get("interaction")
    if not isinstance(interaction, Mapping):
        return None
    should_continue = (
        interaction.get("automatic_continuation_allowed") is True
        and interaction.get("owner_action_required") is False
        and interaction.get("formal_receipt_required") is False
    )
    if not should_continue:
        return None
    return {
        "decision": "block",
        "reason": (
            "Fastlane doctor permits automatic continuation. Continue the current "
            "lifecycle phase, run its required validation, checkpoint, and rerun the doctor."
        ),
    }


def malformed_response(event_key: str) -> dict[str, Any]:
    reason = "Fastlane hook received malformed event data and could not verify the requested boundary."
    if event_key == "pre-tool-use":
        return pre_tool_denial(reason)
    if event_key == "permission-request":
        return permission_denial(reason)
    return {
        "continue": False,
        "stopReason": reason,
        "systemMessage": reason,
    }


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    event_key = arguments[0] if len(arguments) == 1 else ""
    try:
        payload = read_event(sys.stdin)
        response = handle_event(event_key, payload)
    except (HookInputError, OSError, subprocess.SubprocessError, ValueError):
        response = malformed_response(event_key)
    if response is not None:
        json.dump(response, sys.stdout, separators=(",", ":"), sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
