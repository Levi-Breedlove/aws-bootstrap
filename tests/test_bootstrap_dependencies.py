from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "bootstrap_dependencies.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_dependencies", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
dependencies = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dependencies)


class BootstrapDependencyTests(unittest.TestCase):
    def test_repository_dependencies_are_ready_and_pinned(self) -> None:
        report = dependencies.inspect_repository(REPOSITORY_ROOT)
        self.assertEqual(report["status"], "READY", report["diagnostics"])
        toolkit = report["aws_agent_toolkit"]
        self.assertEqual(toolkit["marketplace"], "DECLARED_AND_PINNED")
        self.assertEqual(toolkit["installation_policy"], "INSTALLED_BY_DEFAULT")
        self.assertEqual(toolkit["aws_core_version"], "1.1.0")
        self.assertEqual(
            toolkit["commit"],
            "36f16570de2015c0f0ce94ba9e391bd703c9ffb7",
        )
        self.assertEqual(
            toolkit["runtime_verification"],
            {
                "status": "NOT_CHECKED",
                "management_command": "/plugins",
                "plugin_invocation": "@AWS Core",
                "required_capabilities": ["retrieve_skill", "search_documentation"],
                "supported_surfaces": ["CHATGPT_DESKTOP_CODEX", "CODEX_CLI"],
                "unsupported_surfaces": ["CODEX_IDE_EXTENSION"],
                "automatic_client_installation": False,
                "required_runtime_command": "uvx",
                "runtime_package": "uv",
                "automatic_runtime_installation": False,
            },
        )
        self.assertEqual(
            toolkit["hook_review"],
            {
                "status": "NOT_CHECKED",
                "approval_required": True,
                "management_command": "/hooks",
                "trust_scope": "CURRENT_DEFINITION_HASH",
                "expected_event": "PreToolUse",
                "expected_matchers": [
                    "Bash",
                    "use_aws|mcp__aws.*|mcp__plugin_.*aws-mcp.*",
                ],
                "expected_command": (
                    'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/secret-safety.py"'
                ),
                "expected_hooks_sha256": (
                    "b1e46a5d755ca3d13e2cc0e5cc21f8bf26e6f4446424b82773ee2e0e90dfcd4b"
                ),
                "expected_script_sha256": (
                    "01d517c5d45f09c010328114f970147848ac264179d96ed5a84aa51981e1341b"
                ),
                "required_runtime_command": "python3",
                "purpose": "BLOCK_DIRECT_SECRETS_MANAGER_VALUE_FETCH",
                "repository_hook_sources": [],
                "repository_hook_status": "NONE_DECLARED",
                "hooks_feature": "ENABLED_OR_DEFAULT",
                "external_hook_inventory": "REQUIRED_AT_RUNTIME",
                "automatic_hook_trust": False,
                "dangerous_trust_bypass_allowed": False,
            },
        )
        self.assertEqual(report["fastlane_skills"]["status"], "READY")
        self.assertEqual(report["project_agents"]["status"], "READY")

    def test_marketplace_uses_only_the_official_pinned_aws_core_plugin(self) -> None:
        marketplace = json.loads(
            (REPOSITORY_ROOT / ".agents/plugins/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(marketplace["plugins"]), 1)
        plugin = marketplace["plugins"][0]
        self.assertEqual(plugin["name"], "aws-core")
        self.assertEqual(plugin["source"]["source"], "git-subdir")
        self.assertEqual(
            plugin["source"]["url"],
            "https://github.com/aws/agent-toolkit-for-aws.git",
        )
        self.assertEqual(plugin["source"]["path"], "./plugins/aws-core")
        self.assertEqual(plugin["source"]["sha"], dependencies.AWS_TOOLKIT_COMMIT)
        self.assertEqual(plugin["policy"]["installation"], "INSTALLED_BY_DEFAULT")

    def test_project_agents_are_read_only_and_do_not_override_model_or_mcp(self) -> None:
        for name in dependencies.REQUIRED_AGENTS:
            content = (
                REPOSITORY_ROOT / ".codex" / "agents" / f"{name}.toml"
            ).read_text(encoding="utf-8")
            self.assertIn('sandbox_mode = "read-only"', content)
            for forbidden in (
                "approval_policy",
                "model =",
                "model_reasoning_effort",
                "mcp_servers",
            ):
                self.assertNotIn(forbidden, content)
            self.assertIn("Never", content)

    def test_missing_marketplace_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            (project / ".agents/plugins/marketplace.json").unlink()
            report = dependencies.inspect_repository(project)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "AWS_MARKETPLACE_MISSING",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_mutated_aws_pin_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            path = project / ".agents/plugins/marketplace.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["plugins"][0]["source"]["sha"] = "0" * 40
            path.write_text(json.dumps(value), encoding="utf-8")
            report = dependencies.inspect_repository(project)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "AWS_MARKETPLACE_INVALID",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_launch_skill_must_keep_plain_language_init_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            path = project / ".agents/skills/launch-fastlane/agents/openai.yaml"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "init template", "begin setup"
                ),
                encoding="utf-8",
            )
            report = dependencies.inspect_repository(project)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "FASTLANE_SKILL_INVALID",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_project_hook_sources_are_reported_for_runtime_conflict_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            path = project / ".codex" / "hooks.json"
            path.write_text(
                json.dumps({"hooks": {"PreToolUse": []}}), encoding="utf-8"
            )
            report = dependencies.inspect_repository(project)
        hook_review = report["aws_agent_toolkit"]["hook_review"]
        self.assertEqual(report["status"], "READY", report["diagnostics"])
        self.assertEqual(hook_review["repository_hook_sources"], [".codex/hooks.json"])
        self.assertEqual(
            hook_review["repository_hook_status"], "ACTIVE_HOOK_REVIEW_REQUIRED"
        )

    def test_project_config_cannot_disable_required_hook_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            path = project / ".codex" / "config.toml"
            path.write_text("[features]\nhooks = false\n", encoding="utf-8")
            report = dependencies.inspect_repository(project)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "FASTLANE_HOOKS_DISABLED",
            {item["code"] for item in report["diagnostics"]},
        )


if __name__ == "__main__":
    unittest.main()
