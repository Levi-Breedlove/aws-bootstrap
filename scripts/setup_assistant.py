#!/usr/bin/env python3
"""Render safe, owner-run Fastlane setup guidance and reduce session evidence.

This module deliberately does not execute external commands.  Local command
discovery uses ``shutil.which`` only, and Codex/plugin/hook observations must be
provided by the active supported Codex session.  Nothing discovered here is
persisted to the repository.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


OFFICIAL_AWS_MARKETPLACE = "aws/agent-toolkit-for-aws"
OFFICIAL_AWS_MARKETPLACE_NAME = "agent-toolkit-for-aws"
OFFICIAL_AWS_CORE_PLUGIN = "aws-core"
OFFICIAL_AWS_CORE_IDENTITY = "aws-core@agent-toolkit-for-aws"
LAST_TESTED_AWS_CORE_VERSION = "1.1.0"
LEGACY_FASTLANE_AWS_CORE_IDENTITY = (
    "aws-core@aws-codex-fastlane-dependencies"
)

CODEX_GUIDE = "https://learn.chatgpt.com/docs/codex/cli"
CODEX_PLUGIN_GUIDE = "https://learn.chatgpt.com/docs/plugins"
UV_GUIDE = "https://docs.astral.sh/uv/getting-started/installation/"
PYTHON_GUIDE = "https://www.python.org/downloads/"
GIT_GUIDE = "https://git-scm.com/downloads"
BUBBLEWRAP_GUIDE = "https://github.com/containers/bubblewrap"
AWS_PLUGIN_GUIDE = (
    "https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html"
)

MARKETPLACE_COMMAND = "codex plugin marketplace add aws/agent-toolkit-for-aws"
DENY_PROBE = (
    "python3 -c \"if False: client.get_secret_value("
    "SecretId='FASTLANE_SYNTHETIC_DO_NOT_USE')\""
)
ALLOW_PROBE = "python3 -c \"print('FASTLANE_HOOK_ALLOW_PROBE')\""
HANDSHAKE_COMMAND = "@AWS Core\nVERIFY AWS CORE AND CONTINUE FASTLANE"
LIVE_TOOL_OBSERVER = "CODEX_LIVE_TOOL_CALL"
EXPECTED_SKILL_REQUEST = "aws-serverless"
EXPECTED_DOCUMENTATION_QUERY = (
    "AWS Lambda security best practices for serverless applications, including "
    "least-privilege IAM and input validation"
)
OFFICIAL_AWS_REFERENCE_PREFIXES = (
    "https://docs.aws.amazon.com/",
    "https://aws.amazon.com/",
)

SETUP_STATES = (
    "LOCAL_PREREQUISITES_REQUIRED",
    "CODEX_LOGIN_VERIFICATION_REQUIRED",
    "OFFICIAL_MARKETPLACE_REQUIRED",
    "AWS_CORE_INSTALLATION_REQUIRED",
    "AWS_CORE_ENABLE_REQUIRED",
    "AWS_CORE_SESSION_RESTART_REQUIRED",
    "AWS_CORE_DUPLICATE_BLOCKED",
    "AWS_CORE_SOURCE_UNVERIFIED",
    "HOOK_RUNTIME_REQUIRED",
    "HOOK_REVIEW_REQUIRED",
    "HOOK_TRUST_ATTESTATION_REQUIRED",
    "HOOK_PROBES_REQUIRED",
    "AWS_CORE_HANDSHAKE_REQUIRED",
    "AWS_CORE_VERIFICATION_BLOCKED",
    "READY_FOR_INTAKE",
)

SUPPORTED_SURFACES = {
    "CODEX_CLI",
    "CHATGPT_DESKTOP_CODEX",
    "CHATGPT_DESKTOP_WORK",
    "CHATGPT_WEB_WORK",
}

DEFAULT_OWNER_ACTION_IDS = {
    "LOCAL_PREREQUISITES_REQUIRED": "SATISFY_LOCAL_PREREQUISITE",
    "CODEX_LOGIN_VERIFICATION_REQUIRED": "VERIFY_CODEX_LOGIN",
    "OFFICIAL_MARKETPLACE_REQUIRED": "REGISTER_OFFICIAL_MARKETPLACE",
    "AWS_CORE_INSTALLATION_REQUIRED": "INSTALL_OFFICIAL_AWS_CORE",
    "AWS_CORE_ENABLE_REQUIRED": "ENABLE_OFFICIAL_AWS_CORE",
    "AWS_CORE_SESSION_RESTART_REQUIRED": "START_NEW_CODEX_SESSION",
    "AWS_CORE_DUPLICATE_BLOCKED": "DISABLE_LEGACY_AWS_CORE",
    "AWS_CORE_SOURCE_UNVERIFIED": "RESOLVE_AWS_CORE_SOURCE",
    "HOOK_RUNTIME_REQUIRED": "SATISFY_HOOK_RUNTIME",
    "HOOK_REVIEW_REQUIRED": "REVIEW_OFFICIAL_AWS_CORE_HOOK",
    "HOOK_TRUST_ATTESTATION_REQUIRED": "ATTEST_OFFICIAL_HOOK_TRUST",
    "HOOK_PROBES_REQUIRED": "RUN_SAFE_HOOK_PROBES",
    "AWS_CORE_HANDSHAKE_REQUIRED": "RUN_AWS_CORE_HANDSHAKE",
    "AWS_CORE_VERIFICATION_BLOCKED": "RESOLVE_AWS_CORE_VERIFICATION",
    "READY_FOR_INTAKE": "START_GUIDED_INTAKE",
}

BOOLEAN_OR_NULL_EVIDENCE_FIELDS = frozenset(
    {
        "dependencies_ready",
        "doctor_passed",
        "codex_logged_in",
        "official_marketplace_registered",
        "official_plugin_installed",
        "official_plugin_enabled",
        "official_plugin_loaded_in_session",
        "official_plugin_source_verified",
        "legacy_plugin_enabled",
        "hook_visible",
        "hook_source_official",
        "matching_hooks_inventoried",
        "hook_reviewed",
        "hook_trust_attested_by_owner",
        "deny_probe_passed",
        "deny_probe_blocked_before_execution",
        "allow_probe_passed",
        "retrieve_skill_passed",
        "search_documentation_passed",
        "credentials_inspected",
        "aws_account_accessed",
    }
)
STRING_OR_NULL_EVIDENCE_FIELDS = frozenset(
    {
        "official_plugin_version",
        "observer",
        "observed_plugin_identity",
        "python3_version",
        "observed_marketplace_repository",
        "observed_plugin_source",
        "hook_plugin_identity",
        "allow_probe_output",
        "invoked_plugin_identity",
        "retrieve_skill_plugin_identity",
        "search_documentation_plugin_identity",
        "retrieved_skill",
        "requested_skill",
        "documentation_query",
    }
)
STRING_LIST_EVIDENCE_FIELDS = frozenset(
    {"unknown_plugin_sources", "conflicting_hooks", "documentation_sources"}
)
SESSION_EVIDENCE_FIELDS = frozenset(
    BOOLEAN_OR_NULL_EVIDENCE_FIELDS
    | STRING_OR_NULL_EVIDENCE_FIELDS
    | STRING_LIST_EVIDENCE_FIELDS
)

Which = Callable[[str], str | None]
MAX_EVIDENCE_BYTES = 1_000_000


class SetupError(RuntimeError):
    """Raised when the repository root is missing or unsafe."""


def read_session_evidence(stream: Any) -> dict[str, Any]:
    """Read strictly allowlisted, non-sensitive session evidence from stdin."""

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
            raise SetupError(f"stdin evidence field {key!r} has an invalid type or value")
    if "python3_version" in parsed:
        python3_version = parsed["python3_version"]
        if not isinstance(python3_version, str):
            raise SetupError("stdin evidence field 'python3_version' must be X.Y or X.Y.Z")
        parts = python3_version.strip().split(".")
        if (
            len(parts) not in {2, 3}
            or any(not part or not part.isascii() or not part.isdigit() for part in parts)
        ):
            raise SetupError("stdin evidence field 'python3_version' must be X.Y or X.Y.Z")
        parsed["python3_version"] = ".".join(parts)
        parsed["python3_version_supported"] = tuple(map(int, parts[:2])) >= (3, 11)
    return dict(parsed)


def canonical_root(root: Path) -> Path:
    """Resolve a repository root whose manifest is a regular local file."""

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
    """Detect a PATH command without executing it or returning its local path."""

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
    """Return non-sensitive local observations without executing a command."""

    checked_root = canonical_root(root)
    version = tuple(python_version or sys.version_info[:3])
    system_name = (system or platform.system()).upper()
    normalized_surface = surface.strip().upper() if surface else "UNKNOWN"
    supported_surface: bool | None
    if normalized_surface == "UNKNOWN":
        supported_surface = None
    else:
        supported_surface = normalized_surface in SUPPORTED_SURFACES
    python_on_path = external_executable_detected("python", checked_root, which=which)
    python3_on_path = external_executable_detected("python3", checked_root, which=which)
    fastlane_python_command: str | None = None
    if python_on_path:
        fastlane_python_command = "python"
    elif not system_name.startswith("WINDOWS") and python3_on_path:
        fastlane_python_command = "python3"
    return {
        "repository_ready": True,
        # BOOT-00 supplies these after running the repository-owned checks.
        # This assistant never executes either script or infers PASS from files.
        "dependencies_ready": None,
        "doctor_passed": None,
        "git_available": external_executable_detected("git", checked_root, which=which),
        "python_available": fastlane_python_command is not None,
        "fastlane_python_command": fastlane_python_command,
        "python_version_supported": version >= (3, 11),
        "python3_available": python3_on_path,
        # PATH presence does not prove the external command's version. The owner
        # supplies the visibly observed version through --evidence-stdin.
        "python3_version_supported": None,
        "bwrap_available": external_executable_detected(
            "bwrap", checked_root, which=which
        ),
        "uvx_available": external_executable_detected("uvx", checked_root, which=which),
        "codex_available": external_executable_detected(
            "codex", checked_root, which=which
        ),
        "system": system_name,
        "surface": normalized_surface,
        "supported_surface": supported_surface,
        # These properties cannot be inferred safely from the repository or PATH.
        "codex_logged_in": None,
        "official_marketplace_registered": None,
        "official_plugin_installed": None,
        "official_plugin_enabled": None,
    }


def _progress(step: int, *, complete: bool = False) -> str:
    return "4 of 4 complete" if complete else f"Step {step} of 4"


def _version_context(evidence: Mapping[str, Any]) -> dict[str, Any]:
    observed = evidence.get("official_plugin_version")
    observed_version = (
        observed.strip() if isinstance(observed, str) and observed.strip() else None
    )
    return {
        "dependency_policy": "OFFICIAL_CURRENT",
        "marketplace": OFFICIAL_AWS_MARKETPLACE_NAME,
        "plugin": OFFICIAL_AWS_CORE_PLUGIN,
        "identity": OFFICIAL_AWS_CORE_IDENTITY,
        "last_tested_version": LAST_TESTED_AWS_CORE_VERSION,
        "observed_version": observed_version,
        "version_differs_from_last_tested": (
            observed_version is not None
            and observed_version != LAST_TESTED_AWS_CORE_VERSION
        ),
    }


def _report(
    state: str,
    evidence: Mapping[str, Any],
    *,
    step: int,
    observed: str,
    explanation: str,
    owner_action: str,
    owner_command: str | None,
    verification: str,
    resume_with: str,
    owner_action_id: str | None = None,
    complete: bool = False,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if state not in SETUP_STATES:
        raise ValueError(f"Unknown setup state: {state}")
    action_id = owner_action_id or DEFAULT_OWNER_ACTION_IDS[state]
    result: dict[str, Any] = {
        "schema_version": 2,
        "mode": "INSTRUCTIONS_ONLY",
        "state": state,
        "progress_step": _progress(step, complete=complete),
        "observed": observed,
        "explanation": explanation,
        "owner_action_id": action_id,
        "owner_action": owner_action,
        "owner_command": owner_command,
        "verification": verification,
        "resume_with": resume_with,
        "aws_credentials": "NOT_CONFIGURED_OR_CHECKED",
        "aws_access": "NOT_USED",
        "aws_authorization": "NOT_GRANTED_BY_SETUP",
        "executed_external_commands": False,
        "repository_writes": "NONE",
        "user_state_persisted_in_repository": False,
        "aws_core": _version_context(evidence),
    }
    if details:
        result["details"] = dict(details)
    return result


def _handshake_details(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Return the non-sensitive, attributable capability receipt fields."""

    def status(value: Any) -> str:
        if value is True:
            return "PASS"
        if value is False:
            return "FAIL"
        return "NOT_OBSERVED"

    sources = evidence.get("documentation_sources")
    return {
        "observer": evidence.get("observer"),
        "observed_marketplace_repository": evidence.get(
            "observed_marketplace_repository"
        ),
        "observed_plugin_identity": evidence.get("observed_plugin_identity"),
        "plugin_source": evidence.get("observed_plugin_source"),
        "observed_plugin_version": evidence.get("official_plugin_version"),
        "invoked_plugin_identity": evidence.get("invoked_plugin_identity"),
        "retrieve_skill": status(evidence.get("retrieve_skill_passed")),
        "retrieve_skill_plugin_identity": evidence.get(
            "retrieve_skill_plugin_identity"
        ),
        "requested_skill": evidence.get("requested_skill"),
        "retrieved_skill": evidence.get("retrieved_skill"),
        "search_documentation": status(
            evidence.get("search_documentation_passed")
        ),
        "search_documentation_plugin_identity": evidence.get(
            "search_documentation_plugin_identity"
        ),
        "documentation_query": evidence.get("documentation_query"),
        "documentation_sources": list(sources) if isinstance(sources, list) else [],
        "credentials_inspected": evidence.get("credentials_inspected"),
        "aws_account_accessed": evidence.get("aws_account_accessed"),
    }


def _official_aws_reference(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value == value.strip()
        and any(value.startswith(prefix) for prefix in OFFICIAL_AWS_REFERENCE_PREFIXES)
    )


def _local_block(evidence: Mapping[str, Any]) -> dict[str, Any] | None:
    if evidence.get("repository_ready") is not True:
        return _report(
            "LOCAL_PREREQUISITES_REQUIRED",
            evidence,
            step=1,
            observed="The Fastlane repository or its manifest was not verified.",
            explanation="Setup starts only from a complete, readable template repository.",
            owner_action="Restore or reopen the complete Fastlane repository.",
            owner_command=None,
            verification="Run the setup status command again from the repository root.",
            resume_with="continue setup",
        )
    if evidence.get("supported_surface") is False:
        surface = str(evidence.get("surface") or "this client")
        return _report(
            "LOCAL_PREREQUISITES_REQUIRED",
            evidence,
            step=1,
            observed=f"{surface} is not a supported plugin-management surface.",
            explanation=(
                "AWS Core setup requires interactive Codex CLI or ChatGPT Work/Codex "
                "on web or desktop; the Codex IDE extension cannot manage plugins."
            ),
            owner_action="Open this repository in a supported Codex surface.",
            owner_command=None,
            verification="Confirm that /plugins is available in the new session.",
            resume_with="continue setup",
        )
    fastlane_python = evidence.get("fastlane_python_command")
    if fastlane_python not in {"python", "python3"}:
        fastlane_python = "python"
    local_requirements = (
        (
            "git_available",
            "Git was not detected on PATH.",
            f"Install Git using its official platform instructions: {GIT_GUIDE}",
            None,
            "git --version",
        ),
        (
            "python_available",
            "The `python` command used by Fastlane was not detected on PATH.",
            f"Install Python 3.11 or newer using the official guide: {PYTHON_GUIDE}",
            None,
            f"{fastlane_python} --version",
        ),
        (
            "python_version_supported",
            "Fastlane is running with Python older than 3.11.",
            f"Install Python 3.11 or newer using the official guide: {PYTHON_GUIDE}",
            None,
            f"{fastlane_python} --version",
        ),
        (
            "uvx_available",
            "Astral `uvx` was not detected on PATH.",
            f"Install Astral uv using its official platform instructions: {UV_GUIDE}",
            None,
            "uvx --version",
        ),
        (
            "codex_available",
            "Codex CLI was not detected on PATH.",
            f"Install Codex CLI using the official guide: {CODEX_GUIDE}",
            None,
            "codex --version",
        ),
    )
    for key, observed, action, command, verification in local_requirements:
        if (
            key == "codex_available"
            and evidence.get("supported_surface") is True
            and evidence.get("surface") != "CODEX_CLI"
            and any(
                evidence.get(field) is True
                for field in (
                    "official_marketplace_registered",
                    "official_plugin_installed",
                    "official_plugin_enabled",
                )
            )
        ):
            continue
        if evidence.get(key) is not True:
            return _report(
                "LOCAL_PREREQUISITES_REQUIRED",
                evidence,
                step=1,
                observed=observed,
                explanation="This owner-managed local prerequisite is required before plugin setup.",
                owner_action=action,
                owner_command=command,
                verification=f"Run `{verification}` visibly, then resume setup.",
                resume_with="continue setup",
            )
    if evidence.get("dependencies_ready") is not True:
        return _report(
            "LOCAL_PREREQUISITES_REQUIRED",
            evidence,
            step=1,
            observed="The Fastlane dependency checker has not supplied a current READY result.",
            explanation="Repository files and dependency contracts must pass before runtime setup.",
            owner_action="Run the read-only Fastlane dependency checker from the repository root.",
            owner_command="python scripts/bootstrap_dependencies.py --root . --json",
            verification="The current dependency-checker result reports READY.",
            resume_with="continue setup",
        )
    if evidence.get("doctor_passed") is not True:
        return _report(
            "LOCAL_PREREQUISITES_REQUIRED",
            evidence,
            step=1,
            observed="The initialized project doctor has not supplied a current PASS result.",
            explanation="Template initialization and repository coherence must be proven before plugin setup.",
            owner_action="Run the read-only project doctor after template initialization completes.",
            owner_command="python scripts/bootstrap_doctor.py --root . --json",
            verification="The current project-doctor result reports PASS.",
            resume_with="continue setup",
        )
    return None


def _plugin_sources(
    evidence: Mapping[str, Any],
) -> tuple[bool, bool, list[str], bool]:
    official = evidence.get("official_plugin_enabled") is True
    raw_legacy = evidence.get("legacy_plugin_enabled")
    legacy = raw_legacy is True
    raw_unknown = evidence.get("unknown_plugin_sources")
    unknown = (
        sorted({item for item in raw_unknown if isinstance(item, str) and item})
        if isinstance(raw_unknown, list)
        else []
    )
    inventory_observed = (
        isinstance(raw_legacy, bool)
        and isinstance(raw_unknown, list)
        and all(isinstance(item, str) and bool(item.strip()) for item in raw_unknown)
    )
    return official, legacy, unknown, inventory_observed


def reduce_setup(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Purely reduce current session evidence to the first unresolved state.

    Callers must supply live Codex/plugin/hook observations.  Repeated calls
    with the same mapping return the same report and never persist state.
    """

    local = _local_block(evidence)
    if local is not None:
        return local

    if evidence.get("codex_logged_in") is not True:
        cli_login = evidence.get("surface") in {None, "UNKNOWN", "CODEX_CLI"}
        return _report(
            "CODEX_LOGIN_VERIFICATION_REQUIRED",
            evidence,
            step=1,
            observed="The current Codex login was not verified.",
            explanation="Codex authentication is separate from AWS credentials and AWS access.",
            owner_action=(
                "Sign in to Codex using the owner-managed login flow."
                if cli_login
                else "Sign in to ChatGPT in the current plugin-capable Work/Codex surface."
            ),
            owner_command="codex login" if cli_login else None,
            verification=(
                "Run `codex login status` visibly."
                if cli_login
                else "The current Work/Codex session is visibly signed in and `/plugins` is available."
            ),
            resume_with="continue setup",
        )

    (
        official_enabled,
        legacy_enabled,
        unknown_sources,
        plugin_inventory_observed,
    ) = _plugin_sources(evidence)
    if official_enabled and legacy_enabled:
        return _report(
            "AWS_CORE_DUPLICATE_BLOCKED",
            evidence,
            step=2,
            observed=(
                f"Both `{OFFICIAL_AWS_CORE_IDENTITY}` and "
                f"`{LEGACY_FASTLANE_AWS_CORE_IDENTITY}` are enabled."
            ),
            explanation="Duplicate AWS Core installations can load overlapping tools and hooks.",
            owner_action="Disable the legacy Fastlane AWS Core entry in `/plugins`.",
            owner_command="/plugins",
            verification=f"Only `{OFFICIAL_AWS_CORE_IDENTITY}` remains enabled.",
            resume_with="continue setup",
            details={
                "enabled_sources": [
                    OFFICIAL_AWS_CORE_IDENTITY,
                    LEGACY_FASTLANE_AWS_CORE_IDENTITY,
                ]
            },
        )
    if unknown_sources:
        return _report(
            "AWS_CORE_SOURCE_UNVERIFIED",
            evidence,
            step=2,
            observed=(
                "AWS Core is enabled from unverified source(s): "
                + ", ".join(unknown_sources)
                + "."
            ),
            explanation="Fastlane uses AWS Core exclusively from the official AWS Agent Toolkit.",
            owner_action="Disable the unverified AWS Core source in `/plugins`.",
            owner_command="/plugins",
            verification=f"Only `{OFFICIAL_AWS_CORE_IDENTITY}` may be enabled.",
            resume_with="continue setup",
            details={"unverified_sources": unknown_sources},
        )
    if legacy_enabled and not official_enabled:
        return _report(
            "AWS_CORE_SOURCE_UNVERIFIED",
            evidence,
            step=2,
            observed=(
                "Only the legacy Fastlane-pinned entry "
                f"`{LEGACY_FASTLANE_AWS_CORE_IDENTITY}` is enabled."
            ),
            explanation="The dependency policy now follows the official current AWS Agent Toolkit.",
            owner_action="Disable the legacy entry in `/plugins`.",
            owner_command="/plugins",
            verification=f"The legacy source is disabled before `{OFFICIAL_AWS_CORE_IDENTITY}` is used.",
            resume_with="continue setup",
            details={"legacy_source": LEGACY_FASTLANE_AWS_CORE_IDENTITY},
        )

    installed = evidence.get("official_plugin_installed") is True or official_enabled
    marketplace = evidence.get("official_marketplace_registered") is True or installed
    if not marketplace:
        return _report(
            "OFFICIAL_MARKETPLACE_REQUIRED",
            evidence,
            step=2,
            observed="The official AWS Agent Toolkit marketplace was not verified.",
            explanation="The marketplace supplies the official current AWS Core plugin.",
            owner_action="Register the official marketplace in a visible terminal.",
            owner_command=MARKETPLACE_COMMAND,
            verification="Open `/plugins` and confirm the AWS Agent Toolkit marketplace appears.",
            resume_with="continue setup",
        )
    if not installed:
        return _report(
            "AWS_CORE_INSTALLATION_REQUIRED",
            evidence,
            step=2,
            observed="The official marketplace is available, but AWS Core was not verified as installed.",
            explanation="AWS Core provides the AWS skills, documentation tools, and safety hook used by Fastlane.",
            owner_action="Open `/plugins` and install AWS Core from AWS Agent Toolkit.",
            owner_command="/plugins",
            verification=f"Confirm `{OFFICIAL_AWS_CORE_IDENTITY}` is installed.",
            resume_with="continue setup",
        )
    if not official_enabled:
        return _report(
            "AWS_CORE_ENABLE_REQUIRED",
            evidence,
            step=2,
            observed="Official AWS Core is installed but not verified as enabled in this session.",
            explanation="An installed but disabled plugin cannot provide live AWS Core capabilities.",
            owner_action="Enable official AWS Core in `/plugins`.",
            owner_command="/plugins",
            verification=f"Confirm `{OFFICIAL_AWS_CORE_IDENTITY}` is enabled.",
            resume_with="continue setup",
        )
    observed_version = evidence.get("official_plugin_version")
    if (
        not plugin_inventory_observed
        or not isinstance(observed_version, str)
        or not observed_version.strip()
    ):
        return _report(
            "AWS_CORE_SOURCE_UNVERIFIED",
            evidence,
            step=2,
            observed=(
                "The enabled AWS Core inventory or observed version is incomplete."
            ),
            explanation=(
                "Fastlane must explicitly observe legacy and unknown-source inventory "
                "and the current official plugin version before assessing its source."
            ),
            owner_action=(
                "Inspect the enabled AWS Core entry and all AWS Core sources in `/plugins`."
            ),
            owner_command="/plugins",
            verification=(
                "Record the observed version, whether the legacy source is enabled, "
                "and the complete unknown-source list."
            ),
            resume_with="continue setup",
        )
    source_verified = (
        evidence.get("official_plugin_source_verified") is True
        and evidence.get("observed_marketplace_repository")
        == OFFICIAL_AWS_MARKETPLACE
        and evidence.get("observed_plugin_source")
        == OFFICIAL_AWS_MARKETPLACE_NAME
        and evidence.get("observed_plugin_identity") == OFFICIAL_AWS_CORE_IDENTITY
    )
    if not source_verified:
        return _report(
            "AWS_CORE_SOURCE_UNVERIFIED",
            evidence,
            step=2,
            observed="The enabled AWS Core source was not verified as the official marketplace.",
            explanation="Installation metadata alone is not accepted as source proof.",
            owner_action="Inspect the enabled AWS Core entry in `/plugins` and verify its marketplace.",
            owner_command="/plugins",
            verification=f"The observed identity is exactly `{OFFICIAL_AWS_CORE_IDENTITY}`.",
            resume_with="continue setup",
        )

    if evidence.get("official_plugin_loaded_in_session") is not True:
        return _report(
            "AWS_CORE_SESSION_RESTART_REQUIRED",
            evidence,
            step=2,
            observed="Official AWS Core is enabled but was not loaded in this session.",
            explanation="Plugin state changes become available only in a new Codex session.",
            owner_action="Start a new Codex session in this repository.",
            owner_command=None,
            verification=f"The new session exposes `{OFFICIAL_AWS_CORE_IDENTITY}`.",
            resume_with="continue setup",
        )

    if (
        evidence.get("python3_available") is not True
        or evidence.get("python3_version_supported") is not True
    ):
        windows = str(evidence.get("system", "")).upper().startswith("WINDOWS")
        explanation = "The current official AWS Core hook invokes the exact `python3` command."
        if windows:
            explanation += " Native Windows may not provide it; WSL2 is the supported fallback."
        return _report(
            "HOOK_RUNTIME_REQUIRED",
            evidence,
            step=3,
            observed=(
                "A Python 3.11-or-newer `python3` hook runtime was not visibly verified."
            ),
            explanation=explanation,
            owner_action=(
                "Verify `python3` in a visible terminal; use WSL2 if it is unavailable on native Windows."
            ),
            owner_command="python3 --version",
            verification="Python 3.11 or newer responds to the exact `python3` command.",
            resume_with="continue setup",
        )

    if (
        str(evidence.get("system", "")).upper() == "LINUX"
        and evidence.get("bwrap_available") is not True
    ):
        return _report(
            "HOOK_RUNTIME_REQUIRED",
            evidence,
            step=3,
            observed="Bubblewrap was not detected for the Linux or WSL Codex sandbox.",
            explanation="Linux and WSL use Bubblewrap to preserve the expected sandbox boundary.",
            owner_action=(
                "Install Bubblewrap with the approved package source for this Linux distribution."
            ),
            owner_command=None,
            verification="Run `bwrap --version` visibly.",
            resume_with="continue setup",
            owner_action_id="INSTALL_BUBBLEWRAP",
        )

    conflicts = evidence.get("conflicting_hooks", [])
    conflict_names = (
        sorted({item for item in conflicts if isinstance(item, str) and item})
        if isinstance(conflicts, (list, tuple, set))
        else []
    )
    if conflict_names:
        return _report(
            "AWS_CORE_VERIFICATION_BLOCKED",
            evidence,
            step=3,
            observed="Unknown or conflicting hooks match the AWS Core execution surfaces.",
            explanation="Fastlane cannot safely infer which matching hooks will run.",
            owner_action="Review the matching hooks and disable or resolve every unknown conflict.",
            owner_command="/hooks",
            verification="Only reviewed, expected matching hooks remain.",
            resume_with="continue setup",
            details={"conflicting_hooks": conflict_names},
        )
    if evidence.get("hook_visible") is True and (
        evidence.get("hook_source_official") is False
        or evidence.get("hook_plugin_identity") != OFFICIAL_AWS_CORE_IDENTITY
    ):
        return _report(
            "AWS_CORE_SOURCE_UNVERIFIED",
            evidence,
            step=3,
            observed="The visible AWS Core hook was not attributed to the official plugin source.",
            explanation="Fastlane cannot trust a hook merely because its command looks familiar.",
            owner_action="Inspect `/hooks` and resolve the unverified hook source.",
            owner_command="/hooks",
            verification=f"The hook source is `{OFFICIAL_AWS_CORE_IDENTITY}`.",
            resume_with="continue setup",
        )
    hook_definition_reviewed = all(
        evidence.get(key) is True
        for key in (
            "hook_visible",
            "hook_source_official",
            "matching_hooks_inventoried",
            "hook_reviewed",
        )
    ) and evidence.get("hook_plugin_identity") == OFFICIAL_AWS_CORE_IDENTITY
    if not hook_definition_reviewed:
        return _report(
            "HOOK_REVIEW_REQUIRED",
            evidence,
            step=3,
            observed="The current official AWS Core hook review and trust were not fully verified.",
            explanation=(
                "The owner must inspect the current definition and every matching hook; "
                "Fastlane never trusts hooks automatically."
            ),
            owner_action="Review the current official AWS Core hook in `/hooks`.",
            owner_command="/hooks",
            verification=(
                "The displayed hook identity, definition, and complete matching-hook "
                "inventory are reviewed."
            ),
            resume_with="continue setup",
        )
    if evidence.get("hook_trust_attested_by_owner") is not True:
        return _report(
            "HOOK_TRUST_ATTESTATION_REQUIRED",
            evidence,
            step=3,
            observed=(
                "The official AWS Core hook was reviewed, but owner trust attestation "
                "was not supplied."
            ),
            explanation=(
                "Only the owner can trust the currently displayed hook definition; "
                "Fastlane cannot observe or infer a private trust record."
            ),
            owner_action=(
                "Personally trust the reviewed hook, then provide the exact owner "
                "attestation below."
            ),
            owner_command=(
                "I REVIEWED AND TRUST THE CURRENT OFFICIAL AWS CORE HOOK"
            ),
            verification=(
                "The owner attests to the displayed official plugin identity and "
                "matching-hook inventory."
            ),
            resume_with="continue setup",
        )

    deny = evidence.get("deny_probe_passed")
    deny_blocked = evidence.get("deny_probe_blocked_before_execution")
    allow = evidence.get("allow_probe_passed")
    allow_output = evidence.get("allow_probe_output")
    deny_failed = deny is False or deny_blocked is False
    allow_failed = allow is False or (
        isinstance(allow_output, str)
        and allow_output != "FASTLANE_HOOK_ALLOW_PROBE"
    )
    if deny_failed or allow_failed:
        failed = []
        if deny_failed:
            failed.append("deny probe")
        if allow_failed:
            failed.append("allow probe")
        return _report(
            "AWS_CORE_VERIFICATION_BLOCKED",
            evidence,
            step=3,
            observed=f"AWS Core hook verification failed: {', '.join(failed)}.",
            explanation="Both the inert denial and harmless allowance behavior are required.",
            owner_action="Review the hook result and resolve the failed probe before retrying.",
            owner_command="/hooks",
            verification="The deny probe is blocked before execution and the allow probe prints the exact marker.",
            resume_with="continue setup",
            details={
                "deny_probe": deny,
                "deny_blocked_before_execution": deny_blocked,
                "allow_probe": allow,
                "allow_probe_output": allow_output,
            },
        )
    if (
        deny is not True
        or deny_blocked is not True
        or allow is not True
        or allow_output != "FASTLANE_HOOK_ALLOW_PROBE"
    ):
        return _report(
            "HOOK_PROBES_REQUIRED",
            evidence,
            step=3,
            observed="The AWS Core hook probes have not both been observed passing.",
            explanation="The probes test hook behavior locally without calling AWS.",
            owner_action="Ask Fastlane to run both safe local hook probes through the normal Codex tool path.",
            owner_command="continue setup",
            verification=(
                "Deny probe is blocked before execution; allow probe prints "
                "`FASTLANE_HOOK_ALLOW_PROBE`."
            ),
            resume_with="continue setup",
            details={"deny_probe_command": DENY_PROBE, "allow_probe_command": ALLOW_PROBE},
        )

    retrieve = evidence.get("retrieve_skill_passed")
    search = evidence.get("search_documentation_passed")
    if (
        evidence.get("credentials_inspected") is True
        or evidence.get("aws_account_accessed") is True
    ):
        return _report(
            "AWS_CORE_VERIFICATION_BLOCKED",
            evidence,
            step=4,
            observed=(
                "The setup handshake inspected credentials or accessed an AWS account."
            ),
            explanation=(
                "BOOT-00 verification is documentation-only and must not use credentials "
                "or AWS account access."
            ),
            owner_action=(
                "Stop and repeat the handshake using only unauthenticated AWS Core "
                "skill retrieval and documentation search."
            ),
            owner_command=HANDSHAKE_COMMAND,
            verification=(
                "Both capabilities pass with credentials_inspected=false and "
                "aws_account_accessed=false."
            ),
            resume_with=HANDSHAKE_COMMAND,
            details=_handshake_details(evidence),
        )
    if retrieve is False or search is False:
        failed = []
        if retrieve is False:
            failed.append("retrieve_skill")
        if search is False:
            failed.append("search_documentation")
        return _report(
            "AWS_CORE_VERIFICATION_BLOCKED",
            evidence,
            step=4,
            observed=f"The live AWS Core handshake failed: {', '.join(failed)}.",
            explanation="Both live official AWS Core capabilities are required as proof of use.",
            owner_action="Resolve the AWS Core tool failure and retry the explicit handshake.",
            owner_command=HANDSHAKE_COMMAND,
            verification="Both required calls return live, attributable evidence.",
            resume_with=HANDSHAKE_COMMAND,
            details=_handshake_details(evidence),
        )
    if retrieve is not True or search is not True:
        return _report(
            "AWS_CORE_HANDSHAKE_REQUIRED",
            evidence,
            step=4,
            observed="Live use of both required official AWS Core capabilities was not verified.",
            explanation="Plugin installation is not proof that Codex invoked AWS Core.",
            owner_action="Explicitly invoke AWS Core for the unauthenticated setup handshake.",
            owner_command=HANDSHAKE_COMMAND,
            verification="Observe successful `retrieve_skill` and `search_documentation` calls.",
            resume_with=HANDSHAKE_COMMAND,
        )

    invoked_identity = evidence.get("invoked_plugin_identity")
    retrieve_identity = evidence.get("retrieve_skill_plugin_identity")
    search_identity = evidence.get("search_documentation_plugin_identity")
    if any(
        identity != OFFICIAL_AWS_CORE_IDENTITY
        for identity in (invoked_identity, retrieve_identity, search_identity)
    ):
        return _report(
            "AWS_CORE_VERIFICATION_BLOCKED",
            evidence,
            step=4,
            observed="The live capability calls were not attributable to the official AWS Core identity.",
            explanation="Both required calls must visibly run through the explicitly invoked official plugin.",
            owner_action="Repeat the explicit handshake with official AWS Core selected.",
            owner_command=HANDSHAKE_COMMAND,
            verification=f"Invocation and both capability calls report `{OFFICIAL_AWS_CORE_IDENTITY}`.",
            resume_with=HANDSHAKE_COMMAND,
            details=_handshake_details(evidence),
        )
    retrieved_skill = evidence.get("retrieved_skill")
    requested_skill = evidence.get("requested_skill")
    documentation_query = evidence.get("documentation_query")
    documentation_sources = evidence.get("documentation_sources")
    complete_metadata = (
        evidence.get("observer") == LIVE_TOOL_OBSERVER
        and evidence.get("observed_marketplace_repository")
        == OFFICIAL_AWS_MARKETPLACE
        and evidence.get("observed_plugin_identity") == OFFICIAL_AWS_CORE_IDENTITY
        and evidence.get("observed_plugin_source") == OFFICIAL_AWS_MARKETPLACE_NAME
        and isinstance(evidence.get("official_plugin_version"), str)
        and bool(str(evidence.get("official_plugin_version")).strip())
        and requested_skill == EXPECTED_SKILL_REQUEST
        and isinstance(retrieved_skill, str)
        and bool(retrieved_skill.strip())
        and documentation_query == EXPECTED_DOCUMENTATION_QUERY
        and isinstance(documentation_sources, list)
        and bool(documentation_sources)
        and all(_official_aws_reference(item) for item in documentation_sources)
        and evidence.get("credentials_inspected") is False
        and evidence.get("aws_account_accessed") is False
    )
    if not complete_metadata:
        return _report(
            "AWS_CORE_VERIFICATION_BLOCKED",
            evidence,
            step=4,
            observed=(
                "AWS Core calls passed, but their attributable setup evidence is "
                "incomplete or outside the approved handshake."
            ),
            explanation=(
                "The live observer, official plugin provenance, requested skill, "
                "canonical result, exact query, official AWS references, and explicit "
                "no-credentials/no-account-access confirmations are all required."
            ),
            owner_action="Repeat the explicit handshake and include the required non-sensitive evidence.",
            owner_command=HANDSHAKE_COMMAND,
            verification="The result names the skill, query, sources, plugin identity, and PASS status for both calls.",
            resume_with=HANDSHAKE_COMMAND,
            details=_handshake_details(evidence),
        )

    return _report(
        "READY_FOR_INTAKE",
        evidence,
        step=4,
        complete=True,
        observed="Fastlane setup and live official AWS Core verification are complete.",
        explanation="The repository, official plugin, hook, probes, and required knowledge tools all passed.",
        owner_action="Start the guided project intake.",
        owner_command="START GUIDED INTAKE",
        verification=(
            "Repository and doctor checks passed; official AWS Core enabled; hook reviewed; "
            "deny and allow probes passed; retrieve_skill and search_documentation passed."
        ),
        resume_with="START GUIDED INTAKE",
        details={
            **_handshake_details(evidence),
            "deny_probe": "PASS",
            "deny_probe_blocked_before_execution": True,
            "allow_probe": "PASS",
            "allow_probe_output": allow_output,
        },
    )


def render_setup_response(report: Mapping[str, Any]) -> str:
    """Render a short, friendly response with the technical state last."""

    if report.get("state") == "READY_FOR_INTAKE":
        details = report.get("details")
        details = details if isinstance(details, Mapping) else {}
        sources = details.get("documentation_sources", [])
        rendered_sources = (
            ", ".join(str(item) for item in sources)
            if isinstance(sources, list)
            else str(sources)
        )
        return "\n".join(
            [
                "Fastlane setup is complete",
                "",
                f"Progress: {report['progress_step']}",
                "",
                "Verified:",
                "",
                "✓ Repository and doctor checks passed",
                "✓ Official AWS Core is enabled",
                "✓ AWS Core hook review completed",
                "✓ Secret-retrieval deny probe passed",
                "✓ Harmless allow probe passed",
                "✓ retrieve_skill passed",
                "✓ search_documentation passed",
                "",
                "AWS Core verification evidence:",
                f"Observed plugin source: {details.get('observed_marketplace_repository')}",
                f"Invoked plugin identity: {details.get('invoked_plugin_identity')}",
                f"Retrieved skill: {details.get('retrieved_skill')} — PASS",
                f"Documentation query: {details.get('documentation_query')} — PASS",
                f"Documentation sources: {rendered_sources}",
                "",
                "AWS credentials were not configured or checked. No AWS account was accessed, "
                "and setup did not authorize AWS operations.",
                "",
                "Next action: START GUIDED INTAKE",
                "",
                "Technical status: READY_FOR_INTAKE",
            ]
        )

    step_labels = {
        "Step 1 of 4": "Checking the Fastlane repository and local tools.",
        "Step 2 of 4": "Verifying the official AWS Core plugin.",
        "Step 3 of 4": "Reviewing and testing the AWS Core safety hook.",
        "Step 4 of 4": "Confirming AWS skills and documentation are available.",
    }
    progress = str(report["progress_step"])
    lines = [
        "AWS Codex Fastlane — Setup",
        "",
        f"Current step: {step_labels.get(progress, progress)}",
        "",
        f"What I found: {report['observed']}",
        f"Why it matters: {report['explanation']}",
        "",
        f"What you need to do: {report['owner_action']}",
    ]
    command = report.get("owner_command")
    if command:
        lines.extend(["", "Owner-run command:", str(command)])
    if (
        report.get("state") == "AWS_CORE_VERIFICATION_BLOCKED"
        and progress == "Step 4 of 4"
    ):
        details = report.get("details")
        details = details if isinstance(details, Mapping) else {}
        sources = details.get("documentation_sources", [])
        rendered_sources = (
            ", ".join(str(item) for item in sources)
            if isinstance(sources, list) and sources
            else "NOT_OBSERVED"
        )

        def displayed(value: Any) -> str:
            return str(value) if value not in (None, "", []) else "NOT_OBSERVED"

        lines.extend(
            [
                "",
                "AWS Core verification evidence:",
                "Observed plugin source: "
                f"{displayed(details.get('observed_marketplace_repository'))}",
                "Invoked plugin identity: "
                f"{displayed(details.get('invoked_plugin_identity'))}",
                "retrieve_skill: "
                f"{displayed(details.get('retrieve_skill'))}",
                "Retrieved skill: "
                f"{displayed(details.get('retrieved_skill'))}",
                "search_documentation: "
                f"{displayed(details.get('search_documentation'))}",
                "Documentation query: "
                f"{displayed(details.get('documentation_query'))}",
                f"Documentation sources: {rendered_sources}",
            ]
        )
    lines.extend(
        [
            "",
            f"How I’ll verify it: {report['verification']}",
            "",
            "AWS credentials were not configured or checked. No AWS account was accessed, "
            "and setup did not authorize AWS operations.",
            "",
            f"Progress: {progress}",
            "",
            f"Technical status: {report['state']}",
        ]
    )
    return "\n".join(lines)


def opening_greeting() -> str:
    return """Welcome to AWS Codex Fastlane.

I’ll help you turn your AWS project idea into clear requirements, an
AWS-reviewed technical design, and an organized build plan. You stay in
control: I will pause for your approval before design and again before
construction begins.

First, I’ll complete four short setup checks:

1. Verify this template and its local tools.
2. Verify the official AWS Core plugin.
3. Review and test its safety hook.
4. Confirm AWS skills and documentation are available.

Setup will not configure AWS credentials, access your AWS account, or create
cloud resources.

You can answer “I’m not sure—recommend one” whenever you want guidance.

Current step: Checking the Fastlane repository."""


def build_guide(root: Path, *, system: str | None = None) -> dict[str, Any]:
    """Build chronological owner-run instructions without changing the machine."""

    canonical_root(root)
    system_name = (system or platform.system()).upper()
    if system_name.startswith("WINDOWS"):
        platform_note = (
            "Verify both `python` and `python3`. If native Windows lacks `python3`, "
            "use WSL2; do not create an alias, shim, wrapper, or modified plugin copy."
        )
        uv_install = "winget install --id astral-sh.uv --exact --source winget"
    elif system_name == "DARWIN":
        platform_note = "Homebrew may install the prerequisites; verify every command afterward."
        uv_install = "brew install uv"
    else:
        platform_note = "Use your platform's official installation instructions."
        uv_install = None
    return {
        "schema_version": 1,
        "mode": "INSTRUCTIONS_ONLY",
        "system": system_name,
        "executed_external_commands": False,
        "repository_writes": "NONE",
        "user_state_persisted_in_repository": False,
        "aws_credentials": "NOT_CONFIGURED_OR_CHECKED",
        "aws_access": "NOT_USED",
        "aws_authorization": "NOT_GRANTED_BY_SETUP",
        "platform_note": platform_note,
        "steps": [
            {"name": "Git", "guide": GIT_GUIDE, "verify": "git --version"},
            {
                "name": "Python 3.11+",
                "guide": PYTHON_GUIDE,
                "verify": ["python --version", "python3 --version"],
            },
            *(
                [
                    {
                        "name": "WSL2/Linux Codex sandbox",
                        "guide": BUBBLEWRAP_GUIDE,
                        "owner_action": (
                            "In WSL2 or Linux run sudo apt update, then "
                            "sudo apt install bubblewrap."
                        ),
                        "verify": ["command -v bwrap", "bwrap --version"],
                    }
                ]
                if system_name.startswith("WINDOWS") or system_name == "LINUX"
                else []
            ),
            {
                "name": "Astral uv",
                "guide": UV_GUIDE,
                "owner_install": uv_install,
                "verify": "uvx --version",
            },
            {
                "name": "Codex CLI",
                "guide": CODEX_GUIDE,
                "verify": "codex --version",
            },
            {
                "name": "Codex login",
                "owner_action": "codex login",
                "verify": "codex login status",
            },
            {
                "name": "Supported surface",
                "guide": CODEX_PLUGIN_GUIDE,
                "owner_action": (
                    "Use interactive Codex CLI or ChatGPT Work/Codex on web or desktop; "
                    "do not use the Codex IDE extension for plugin management."
                ),
                "verify": "/plugins is available",
            },
            {
                "name": "Official AWS Agent Toolkit marketplace",
                "guide": AWS_PLUGIN_GUIDE,
                "owner_action": (
                    "If AWS Agent Toolkit is absent from /plugins, run `"
                    f"{MARKETPLACE_COMMAND}`; otherwise reuse the existing registration."
                ),
                "verify": f"Enable only {OFFICIAL_AWS_CORE_IDENTITY} in /plugins",
            },
            {
                "name": "Resume Fastlane",
                "owner_action": "Start a new Codex session after plugin changes.",
                "verify": "Send `continue setup`",
            },
        ],
    }


def render_guide(guide: Mapping[str, Any]) -> str:
    lines = [opening_greeting(), "", "Owner-run setup guide", ""]
    for index, step in enumerate(guide["steps"], start=1):
        lines.append(f"{index}. {step['name']}")
        if step.get("owner_install"):
            lines.append(f"   Install: {step['owner_install']}")
        if step.get("owner_action"):
            lines.append(f"   Action: {step['owner_action']}")
        if step.get("guide"):
            lines.append(f"   Official guide: {step['guide']}")
        verify = step.get("verify")
        if isinstance(verify, list):
            lines.append(f"   Verify: {', '.join(verify)}")
        elif verify:
            lines.append(f"   Verify: {verify}")
        lines.append("")
    lines.extend(
        [
            str(guide["platform_note"]),
            "",
            "These are instructions only. Fastlane executed nothing, changed no plugin or "
            "trust state, and did not inspect credentials.",
        ]
    )
    return "\n".join(lines)


def _error_report(message: str) -> dict[str, Any]:
    return _report(
        "LOCAL_PREREQUISITES_REQUIRED",
        {},
        step=1,
        observed=message,
        explanation="The requested repository input is missing, malformed, or unsafe.",
        owner_action="Open a complete Fastlane repository and retry from its root.",
        owner_command=None,
        verification="bootstrap.manifest.json is a readable regular file.",
        resume_with="continue setup",
        details={"input_error": True},
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Inspect safe local prerequisites")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--surface")
    status.add_argument("--json", action="store_true")
    status.add_argument(
        "--evidence-stdin",
        action="store_true",
        help="Merge strictly allowlisted current-session evidence from stdin",
    )

    guide = subparsers.add_parser("guide", help="Print chronological owner-run guidance")
    guide.add_argument("--root", type=Path, default=Path.cwd())

    args = parser.parse_args(argv)
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
                "python3_available",
                "python3_version_supported",
                "bwrap_available",
                "uvx_available",
                "codex_available",
                "supported_surface",
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
    # Actionable setup states are guidance, not CI readiness failures.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
