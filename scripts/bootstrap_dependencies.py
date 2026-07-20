#!/usr/bin/env python3
"""Validate Fastlane repository assets and its official AWS Core contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


AWS_TOOLKIT_REPOSITORY = "https://github.com/aws/agent-toolkit-for-aws"
AWS_TOOLKIT_MARKETPLACE = "aws/agent-toolkit-for-aws"
AWS_CORE_PLUGIN_ID = "aws-core@agent-toolkit-for-aws"
AWS_CORE_LAST_TESTED_VERSION = "1.1.0"
LEGACY_MARKETPLACE_PATH = ".agents/plugins/marketplace.json"
AWS_CORE_MANAGEMENT_COMMAND = "/plugins"
AWS_CORE_INVOCATION = "@AWS Core"
AWS_CORE_RUNTIME_COMMAND = "uvx"
AWS_CORE_RUNTIME_PACKAGE = "uv"
AWS_CORE_REQUIRED_CAPABILITIES = ("retrieve_skill", "search_documentation")
AWS_CORE_SUPPORTED_SURFACES = (
    "CODEX_CLI",
    "CHATGPT_DESKTOP_CODEX",
    "CHATGPT_DESKTOP_WORK",
    "CHATGPT_WEB_WORK",
)
AWS_CORE_UNSUPPORTED_SURFACES = ("CODEX_IDE_EXTENSION",)
AWS_CORE_HOOK_MANAGEMENT_COMMAND = "/hooks"
AWS_CORE_HOOK_EVENT = "PreToolUse"
AWS_CORE_HOOK_MATCHERS = (
    "Bash",
    "use_aws|mcp__aws.*|mcp__plugin_.*aws-mcp.*",
)
AWS_CORE_HOOK_COMMAND = 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/secret-safety.py"'
AWS_CORE_HOOK_RUNTIME_COMMAND = "python3"
SETUP_ASSISTANT_SCRIPT = "scripts/setup_assistant.py"
SETUP_STATES = (
    "LOCAL_PREREQUISITES_REQUIRED",
    "CODEX_LOGIN_VERIFICATION_REQUIRED",
    "OFFICIAL_MARKETPLACE_REQUIRED",
    "AWS_CORE_INSTALLATION_REQUIRED",
    "AWS_CORE_ENABLE_REQUIRED",
    "AWS_CORE_DUPLICATE_BLOCKED",
    "AWS_CORE_SOURCE_UNVERIFIED",
    "HOOK_RUNTIME_REQUIRED",
    "HOOK_REVIEW_REQUIRED",
    "HOOK_PROBES_REQUIRED",
    "AWS_CORE_HANDSHAKE_REQUIRED",
    "AWS_CORE_VERIFICATION_BLOCKED",
    "READY_FOR_INTAKE",
)

REQUIRED_SKILLS = (
    "build-fastlane",
    "launch-fastlane",
    "operate-fastlane-aws",
    "plan-fastlane",
)
SKILL_IMPLICIT_POLICY = {
    "build-fastlane": "true",
    "launch-fastlane": "true",
    "operate-fastlane-aws": "false",
    "plan-fastlane": "true",
}
REQUIRED_AGENTS = (
    "fastlane-aws-advisor",
    "fastlane-evidence-reviewer",
    "fastlane-requirements-reviewer",
)
FORBIDDEN_AGENT_KEYS = {
    "approval_policy",
    "model",
    "model_reasoning_effort",
    "mcp_servers",
}


def diagnostic(code: str, message: str, path: str | None = None) -> dict[str, str]:
    item = {"code": code, "message": message}
    if path is not None:
        item["path"] = path
    return item


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected one JSON object")
    return value


def inspect_repository_hook_sources(
    root: Path, diagnostics: list[dict[str, str]]
) -> tuple[list[str], str]:
    """Find project hook sources without treating their presence as a conflict."""

    sources: list[str] = []
    hooks_path = root / ".codex" / "hooks.json"
    if hooks_path.exists():
        relative = ".codex/hooks.json"
        if not hooks_path.is_file() or hooks_path.is_symlink():
            diagnostics.append(
                diagnostic(
                    "FASTLANE_PROJECT_HOOK_UNSAFE",
                    "The project hook file must be a regular file inside the repository.",
                    relative,
                )
            )
        else:
            try:
                value = load_object(hooks_path)
                if not isinstance(value.get("hooks"), dict):
                    raise ValueError("hooks.json must contain a hooks object")
                sources.append(relative)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                diagnostics.append(
                    diagnostic("FASTLANE_PROJECT_HOOK_INVALID", str(exc), relative)
                )

    config_path = root / ".codex" / "config.toml"
    feature_state = "ENABLED_OR_DEFAULT"
    if config_path.exists():
        relative = ".codex/config.toml"
        if not config_path.is_file() or config_path.is_symlink():
            diagnostics.append(
                diagnostic(
                    "FASTLANE_PROJECT_CONFIG_UNSAFE",
                    "The project Codex config must be a regular file inside the repository.",
                    relative,
                )
            )
        else:
            try:
                value = tomllib.loads(config_path.read_text(encoding="utf-8"))
                hooks = value.get("hooks")
                if hooks is not None:
                    if not isinstance(hooks, dict):
                        raise ValueError("config.toml hooks must be a table")
                    sources.append(relative)
                features = value.get("features")
                if isinstance(features, dict) and features.get("hooks") is False:
                    feature_state = "DISABLED"
                    diagnostics.append(
                        diagnostic(
                            "FASTLANE_HOOKS_DISABLED",
                            "Project configuration disables hooks required for AWS Core review.",
                            relative,
                        )
                    )
            except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
                diagnostics.append(
                    diagnostic("FASTLANE_PROJECT_CONFIG_INVALID", str(exc), relative)
                )

    return sources, feature_state


def inspect_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    diagnostics: list[dict[str, str]] = []
    setup_assistant_path = root / SETUP_ASSISTANT_SCRIPT
    if not setup_assistant_path.is_file() or setup_assistant_path.is_symlink():
        diagnostics.append(
            diagnostic(
                "FASTLANE_SETUP_ASSISTANT_MISSING",
                "The instruction-only setup assistant is missing or unsafe.",
                SETUP_ASSISTANT_SCRIPT,
            )
        )
    repository_hook_sources, hooks_feature_state = inspect_repository_hook_sources(
        root, diagnostics
    )

    legacy_marketplace = root / LEGACY_MARKETPLACE_PATH
    legacy_marketplace_status = "ABSENT"
    if legacy_marketplace.exists():
        legacy_marketplace_status = "PRESENT"
        diagnostics.append(
            diagnostic(
                "LEGACY_PINNED_MARKETPLACE_PRESENT",
                "Remove the repository-local AWS Core marketplace; Fastlane uses the official AWS Agent Toolkit marketplace.",
                LEGACY_MARKETPLACE_PATH,
            )
        )

    skill_states: dict[str, str] = {}
    skill_descriptions: dict[str, str] = {}
    for name in REQUIRED_SKILLS:
        skill_root = root / ".agents" / "skills" / name
        required = (skill_root / "SKILL.md", skill_root / "agents" / "openai.yaml")
        state = "READY"
        for path in required:
            if not path.is_file() or path.is_symlink():
                state = "BLOCKED"
                diagnostics.append(
                    diagnostic(
                        "FASTLANE_SKILL_MISSING",
                        f"Required repo skill asset is missing or unsafe for {name}.",
                        path.relative_to(root).as_posix(),
                    )
                )
        if state == "READY":
            relative_skill = f".agents/skills/{name}/SKILL.md"
            try:
                skill_text = required[0].read_text(encoding="utf-8")
                yaml_text = required[1].read_text(encoding="utf-8")
                if not skill_text.startswith("---\n") or "\n---\n" not in skill_text[4:]:
                    raise ValueError("SKILL.md must begin with complete YAML frontmatter")
                frontmatter = skill_text.split("---", 2)[1]
                name_match = re.search(r"^name:\s*([^\r\n]+)$", frontmatter, re.MULTILINE)
                description_match = re.search(
                    r"^description:\s*([^\r\n]+)$", frontmatter, re.MULTILINE
                )
                if name_match is None or name_match.group(1).strip() != name:
                    raise ValueError("SKILL.md frontmatter name must match its directory")
                if description_match is None or not description_match.group(1).strip():
                    raise ValueError("SKILL.md requires a non-empty trigger description")
                skill_descriptions[name] = description_match.group(1).strip()
                for field in ("display_name", "short_description", "default_prompt"):
                    if re.search(rf"^\s*{field}:\s*.+$", yaml_text, re.MULTILINE) is None:
                        raise ValueError(f"openai.yaml is missing {field}")
                policy = SKILL_IMPLICIT_POLICY[name]
                if (
                    re.search(
                        rf"^\s*allow_implicit_invocation:\s*{policy}\s*$",
                        yaml_text,
                        re.MULTILINE,
                    )
                    is None
                ):
                    raise ValueError(
                        f"openai.yaml allow_implicit_invocation must be {policy}"
                    )
                if name == "launch-fastlane" and "init template" not in yaml_text:
                    raise ValueError("launch-fastlane default prompt must expose init template")
            except (OSError, ValueError) as exc:
                state = "BLOCKED"
                diagnostics.append(
                    diagnostic("FASTLANE_SKILL_INVALID", str(exc), relative_skill)
                )
        skill_states[name] = state

    if len(set(skill_descriptions.values())) != len(skill_descriptions):
        diagnostics.append(
            diagnostic(
                "FASTLANE_SKILL_TRIGGER_COLLISION",
                "Repo skill trigger descriptions must be distinct.",
                ".agents/skills",
            )
        )

    agent_states: dict[str, str] = {}
    for name in REQUIRED_AGENTS:
        relative = f".codex/agents/{name}.toml"
        path = root / relative
        state = "READY"
        if not path.is_file() or path.is_symlink():
            state = "BLOCKED"
            diagnostics.append(
                diagnostic(
                    "FASTLANE_AGENT_MISSING",
                    f"Required project agent is missing or unsafe: {name}.",
                    relative,
                )
            )
        else:
            try:
                value = tomllib.loads(path.read_text(encoding="utf-8"))
                for field in ("name", "description", "developer_instructions"):
                    if not isinstance(value.get(field), str) or not value[field].strip():
                        raise ValueError(f"{field} must be a non-empty string")
                if value["name"] != name:
                    raise ValueError("name must match the project-agent filename")
                if value.get("sandbox_mode") != "read-only":
                    raise ValueError("project advisory agents must be read-only")
                forbidden = sorted(FORBIDDEN_AGENT_KEYS.intersection(value))
                if forbidden:
                    raise ValueError("forbidden overrides: " + ", ".join(forbidden))
            except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
                state = "BLOCKED"
                diagnostics.append(diagnostic("FASTLANE_AGENT_INVALID", str(exc), relative))
        agent_states[name] = state

    ready = not diagnostics
    return {
        "schema_version": 2,
        "status": "READY" if ready else "BLOCKED",
        "aws_agent_toolkit": {
            "repository": AWS_TOOLKIT_REPOSITORY,
            "dependency_policy": "OFFICIAL_CURRENT",
            "marketplace": "agent-toolkit-for-aws",
            "marketplace_slug": AWS_TOOLKIT_MARKETPLACE,
            "marketplace_registration_command": [
                "codex",
                "plugin",
                "marketplace",
                "add",
                AWS_TOOLKIT_MARKETPLACE,
            ],
            "plugin_identity": AWS_CORE_PLUGIN_ID,
            "plugin": "aws-core",
            "last_tested_version": AWS_CORE_LAST_TESTED_VERSION,
            "legacy_repository_marketplace": legacy_marketplace_status,
            "installation_policy": "OWNER_MANAGED",
            "setup_mode": "INSTRUCTIONS_ONLY",
            "setup_assistant": {
                "status": "SETUP_ASSISTANCE_AVAILABLE",
                "mode": "INSTRUCTIONS_ONLY",
                "script": SETUP_ASSISTANT_SCRIPT,
                "states": list(SETUP_STATES),
                "automatic_runtime_installation": False,
                "package_manager_execution": False,
                "runtime_probe_execution": False,
                "user_state_persisted_in_repository": False,
            },
            "runtime_verification": {
                "status": "NOT_CHECKED",
                "management_command": AWS_CORE_MANAGEMENT_COMMAND,
                "plugin_invocation": AWS_CORE_INVOCATION,
                "expected_plugin_identity": AWS_CORE_PLUGIN_ID,
                "required_capabilities": list(AWS_CORE_REQUIRED_CAPABILITIES),
                "supported_surfaces": list(AWS_CORE_SUPPORTED_SURFACES),
                "unsupported_surfaces": list(AWS_CORE_UNSUPPORTED_SURFACES),
                "automatic_client_installation": False,
                "approval_bound_client_installation": False,
                "automatic_marketplace_registration": False,
                "automatic_session_launch": False,
                "required_runtime_command": AWS_CORE_RUNTIME_COMMAND,
                "runtime_package": AWS_CORE_RUNTIME_PACKAGE,
                "automatic_runtime_installation": False,
                "approval_bound_runtime_installation": False,
            },
            "hook_review": {
                "status": "NOT_CHECKED",
                "approval_required": True,
                "management_command": AWS_CORE_HOOK_MANAGEMENT_COMMAND,
                "trust_scope": "CURRENT_DEFINITION_HASH",
                "review_policy": "REVIEW_CURRENT_OFFICIAL_DEFINITION",
                "last_tested_event": AWS_CORE_HOOK_EVENT,
                "last_tested_matchers": list(AWS_CORE_HOOK_MATCHERS),
                "last_tested_command": AWS_CORE_HOOK_COMMAND,
                "raw_file_hash_required": False,
                "required_runtime_command": AWS_CORE_HOOK_RUNTIME_COMMAND,
                "purpose": "BLOCK_DIRECT_SECRETS_MANAGER_VALUE_FETCH",
                "repository_hook_sources": repository_hook_sources,
                "repository_hook_status": (
                    "NONE_DECLARED"
                    if not repository_hook_sources
                    else "ACTIVE_HOOK_REVIEW_REQUIRED"
                ),
                "hooks_feature": hooks_feature_state,
                "external_hook_inventory": "REQUIRED_AT_RUNTIME",
                "automatic_hook_trust": False,
                "dangerous_trust_bypass_allowed": False,
            },
        },
        "fastlane_skills": {
            "status": "READY" if all(state == "READY" for state in skill_states.values()) else "BLOCKED",
            "items": skill_states,
        },
        "project_agents": {
            "status": "READY" if all(state == "READY" for state in agent_states.values()) else "BLOCKED",
            "items": agent_states,
        },
        "diagnostics": diagnostics,
    }


def print_human(report: dict[str, Any]) -> None:
    toolkit = report["aws_agent_toolkit"]
    print(f"Bootstrap dependencies: {report['status']}")
    print(f"Fastlane skills: {report['fastlane_skills']['status']}")
    print(f"Project agents: {report['project_agents']['status']}")
    print(
        "AWS Core dependency: OFFICIAL_CURRENT from "
        f"{toolkit['marketplace_slug']} (last tested {toolkit['last_tested_version']})"
    )
    runtime = toolkit["runtime_verification"]
    print(
        "AWS Core runtime: NOT CHECKED; manage with "
        f"{runtime['management_command']}, require {runtime['required_runtime_command']}, "
        f"then invoke {runtime['plugin_invocation']}"
    )
    hook_review = toolkit["hook_review"]
    print(
        "AWS Core hooks: NOT CHECKED; review exact definitions with "
        f"{hook_review['management_command']}; automatic trust is disabled"
    )
    for item in report["diagnostics"]:
        location = f" ({item['path']})" if "path" in item else ""
        print(f"- {item['code']}: {item['message']}{location}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = inspect_repository(args.root)
    except OSError as exc:
        print(f"Dependency check failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
