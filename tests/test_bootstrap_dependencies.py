from __future__ import annotations

import importlib.util
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
    def test_repository_declares_official_current_aws_core_without_pin(self) -> None:
        report = dependencies.inspect_repository(REPOSITORY_ROOT)
        self.assertEqual(report["status"], "READY", report["diagnostics"])
        toolkit = report["aws_agent_toolkit"]
        self.assertEqual(toolkit["dependency_policy"], "OFFICIAL_CURRENT")
        self.assertEqual(toolkit["marketplace_slug"], "aws/agent-toolkit-for-aws")
        self.assertEqual(toolkit["plugin_identity"], "aws-core@agent-toolkit-for-aws")
        self.assertEqual(toolkit["version_policy"], "OFFICIAL_CURRENT_NO_TEMPLATE_PIN")
        self.assertEqual(toolkit["availability_policy"], "DEFERRED_UNTIL_AWS_DESIGN")
        self.assertNotIn("last_tested_version", toolkit)
        self.assertEqual(toolkit["installation_policy"], "OWNER_MANAGED")
        self.assertEqual(toolkit["setup_mode"], "INSTRUCTIONS_ONLY")
        self.assertEqual(
            toolkit["marketplace_registration_command"],
            ["codex", "plugin", "marketplace", "add", "aws/agent-toolkit-for-aws"],
        )

        setup = toolkit["setup_assistant"]
        self.assertEqual(
            setup["states"],
            ["LOCAL_PREREQUISITES_REQUIRED", "READY_FOR_INTAKE"],
        )
        self.assertFalse(setup["automatic_runtime_installation"])
        self.assertFalse(setup["package_manager_execution"])

        runtime = toolkit["runtime_verification"]
        self.assertFalse(runtime["required_at_boot"])
        self.assertEqual(
            runtime["required_evidence_phases"],
            ["DESIGN-10", "AWS-10"],
        )
        self.assertEqual(
            runtime["required_capabilities"],
            ["retrieve_skill", "search_documentation"],
        )
        self.assertNotIn("hook_review", toolkit)
        self.assertEqual(report["fastlane_skills"]["status"], "READY")
        self.assertEqual(report["project_agents"]["status"], "READY")

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

    def test_launch_skill_keeps_plain_language_init_trigger(self) -> None:
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

    def test_repository_hooks_are_not_fastlane_dependency_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(REPOSITORY_ROOT, project)
            config = project / ".codex" / "config.toml"
            config.write_text("[features]\nhooks = false\n", encoding="utf-8")
            report = dependencies.inspect_repository(project)
        self.assertEqual(report["status"], "READY", report["diagnostics"])
        self.assertNotIn("hook_review", report["aws_agent_toolkit"])


if __name__ == "__main__":
    unittest.main()
