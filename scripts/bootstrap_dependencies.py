#!/usr/bin/env python3
"""Validate repository-scoped Fastlane skills, agents, and AWS Core pin."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


AWS_TOOLKIT_REPOSITORY = "https://github.com/aws/agent-toolkit-for-aws.git"
AWS_TOOLKIT_COMMIT = "36f16570de2015c0f0ce94ba9e391bd703c9ffb7"
AWS_CORE_VERSION = "1.1.0"
MARKETPLACE_PATH = ".agents/plugins/marketplace.json"

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


def inspect_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    diagnostics: list[dict[str, str]] = []

    marketplace_file = root / MARKETPLACE_PATH
    marketplace_status = "READY"
    if not marketplace_file.is_file() or marketplace_file.is_symlink():
        marketplace_status = "BLOCKED"
        diagnostics.append(
            diagnostic(
                "AWS_MARKETPLACE_MISSING",
                "The pinned Fastlane AWS plugin marketplace is missing or unsafe.",
                MARKETPLACE_PATH,
            )
        )
    else:
        try:
            marketplace = load_object(marketplace_file)
            plugins = marketplace.get("plugins")
            if not isinstance(plugins, list) or len(plugins) != 1:
                raise ValueError("plugins must contain exactly the aws-core entry")
            plugin = plugins[0]
            source = plugin.get("source") if isinstance(plugin, dict) else None
            policy = plugin.get("policy") if isinstance(plugin, dict) else None
            expected_source = {
                "source": "git-subdir",
                "url": AWS_TOOLKIT_REPOSITORY,
                "path": "./plugins/aws-core",
                "sha": AWS_TOOLKIT_COMMIT,
            }
            expected_policy = {
                "installation": "INSTALLED_BY_DEFAULT",
                "authentication": "ON_INSTALL",
            }
            if (
                not isinstance(plugin, dict)
                or plugin.get("name") != "aws-core"
                or source != expected_source
                or policy != expected_policy
                or plugin.get("category") != "Cloud"
            ):
                raise ValueError("aws-core source or install policy differs from the approved pin")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            marketplace_status = "BLOCKED"
            diagnostics.append(
                diagnostic("AWS_MARKETPLACE_INVALID", str(exc), MARKETPLACE_PATH)
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
        "schema_version": 1,
        "status": "READY" if ready else "BLOCKED",
        "aws_agent_toolkit": {
            "repository": AWS_TOOLKIT_REPOSITORY,
            "commit": AWS_TOOLKIT_COMMIT,
            "aws_core_version": AWS_CORE_VERSION,
            "marketplace": marketplace_status,
            "installation_policy": "INSTALLED_BY_DEFAULT",
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
    print(f"AWS Toolkit marketplace: {toolkit['marketplace']}")
    print(f"AWS Core pin: {toolkit['aws_core_version']} @ {toolkit['commit']}")
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
