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
    def test_repository_dependencies_use_official_current_aws_core(self) -> None:
        report = dependencies.inspect_repository(REPOSITORY_ROOT)
        self.assertEqual(report["status"], "READY", report["diagnostics"])
        toolkit = report["aws_agent_toolkit"]
        self.assertEqual(toolkit["dependency_policy"], "OFFICIAL_CURRENT")
        self.assertEqual(toolkit["marketplace"], "agent-toolkit-for-aws")
        self.assertEqual(toolkit["marketplace_slug"], "aws/agent-toolkit-for-aws")
        self.assertEqual(toolkit["plugin_identity"], "aws-core@agent-toolkit-for-aws")
        self.assertEqual(toolkit["plugin"], "aws-core")
        self.assertEqual(toolkit["last_tested_version"], "1.1.0")
        self.assertEqual(toolkit["legacy_repository_marketplace"], "ABSENT")
        self.assertEqual(toolkit["installation_policy"], "OWNER_MANAGED")
        self.assertEqual(toolkit["setup_mode"], "INSTRUCTIONS_ONLY")
        self.assertEqual(
            toolkit["marketplace_registration_command"],
            ["codex", "plugin", "marketplace", "add", "aws/agent-toolkit-for-aws"],
        )
        runtime = toolkit["runtime_verification"]
        self.assertEqual(runtime["expected_plugin_identity"], "aws-core@agent-toolkit-for-aws")
        self.assertEqual(runtime["required_capabilities"], ["retrieve_skill", "search_documentation"])
        self.assertEqual(
            runtime["supported_surfaces"],
            [
                "CODEX_CLI",
                "CHATGPT_DESKTOP_CODEX",
                "CHATGPT_DESKTOP_WORK",
                "CHATGPT_WEB_WORK",
            ],
        )
        self.assertEqual(runtime["status"], "NOT_CHECKED")
        setup = toolkit["setup_assistant"]
        self.assertEqual(setup["script"], "scripts/setup_assistant.py")
        self.assertIn("AWS_CORE_DUPLICATE_BLOCKED", setup["states"])
        self.assertIn("READY_FOR_INTAKE", setup["states"])
        hook = toolkit["hook_review"]
        self.assertEqual(hook["review_policy"], "REVIEW_CURRENT_OFFICIAL_DEFINITION")
        self.assertFalse(hook["raw_file_hash_required"])
        self.assertNotIn("expected_hooks_sha256", hook)
        self.assertNotIn("expected_script_sha256", hook)
        self.assertEqual(report["fastlane_skills"]["status"], "READY")
        self.assertEqual(report["project_agents"]["status"], "READY")

    def test_repository_local_aws_core_marketplace_is_absent(self) -> None:
        self.assertFalse((REPOSITORY_ROOT / dependencies.LEGACY_MARKETPLACE_PATH).exists())

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

    def test_legacy_repository_marketplace_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            path = project / dependencies.LEGACY_MARKETPLACE_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"name":"legacy"}', encoding="utf-8")
            report = dependencies.inspect_repository(project)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "LEGACY_PINNED_MARKETPLACE_PRESENT",
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
