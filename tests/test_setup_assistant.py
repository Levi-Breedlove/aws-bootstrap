from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "setup_assistant.py"
SPEC = importlib.util.spec_from_file_location("setup_assistant", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


def ready_evidence(**updates: object) -> dict[str, object]:
    evidence: dict[str, object] = {
        "repository_ready": True,
        "dependencies_ready": True,
        "doctor_passed": True,
        "git_available": True,
        "python_available": True,
        "python_version_supported": True,
        "official_marketplace_registered": None,
        "official_plugin_installed": None,
        "official_plugin_enabled": None,
        "official_plugin_loaded_in_session": None,
        "official_plugin_source_verified": None,
        "observed_marketplace_repository": None,
        "observed_plugin_source": None,
        "observed_plugin_identity": None,
        "legacy_plugin_enabled": False,
        "legacy_marketplace_registered": False,
        "unknown_plugin_sources": [],
    }
    evidence.update(updates)
    return evidence


class SetupAssistantTests(unittest.TestCase):
    def test_public_state_model_has_only_local_block_or_intake_ready(self) -> None:
        self.assertEqual(
            setup.SETUP_STATES,
            ("LOCAL_PREREQUISITES_REQUIRED", "READY_FOR_INTAKE"),
        )

    def test_welcome_is_stable_and_collects_three_setup_values(self) -> None:
        greeting = setup.opening_greeting()
        self.assertTrue(greeting.startswith("Welcome to AWS Codex Fastlane."))
        for phrase in (
            "project name",
            "preferred AWS Region",
            "development budget",
            "Gate A",
            "Gate B",
            "AWS Core",
        ):
            self.assertIn(phrase, greeting)
        self.assertIn("intake still continues", greeting)
        self.assertIn("does not inspect AWS credentials", greeting)

    def test_missing_aws_core_never_blocks_intake(self) -> None:
        report = setup.reduce_setup(ready_evidence())
        self.assertEqual(report["state"], "READY_FOR_INTAKE")
        self.assertEqual(report["owner_action_id"], "BEGIN_INTAKE_NOW")
        self.assertIsNone(report["owner_command"])
        self.assertEqual(report["resume_with"], "IN_CURRENT_RESPONSE")
        self.assertEqual(report["aws_core_status"], "DEFERRED_UNTIL_DESIGN")
        self.assertEqual(report["aws_access"], "NOT_USED")
        self.assertFalse(report["executed_external_commands"])

    def test_official_current_aws_core_is_reused_without_version_pin(self) -> None:
        report = setup.reduce_setup(
            ready_evidence(
                official_plugin_installed=True,
                official_plugin_enabled=True,
                official_plugin_loaded_in_session=True,
                official_plugin_source_verified=True,
                observed_marketplace_repository=setup.OFFICIAL_AWS_MARKETPLACE,
                observed_plugin_source=setup.OFFICIAL_AWS_MARKETPLACE_NAME,
                observed_plugin_identity=setup.OFFICIAL_AWS_CORE_IDENTITY,
            )
        )
        self.assertEqual(report["state"], "READY_FOR_INTAKE")
        self.assertEqual(report["aws_core_status"], "AVAILABLE")
        self.assertNotIn("plugin_version", report.get("details", {}))
        self.assertNotIn("plugin_commit", report.get("details", {}))

    def test_legacy_or_unknown_source_is_deferred_not_a_boot_loop(self) -> None:
        legacy = setup.reduce_setup(ready_evidence(legacy_plugin_enabled=True))
        self.assertEqual(legacy["state"], "READY_FOR_INTAKE")
        self.assertEqual(legacy["aws_core_status"], "DEFERRED_UNTIL_DESIGN")
        self.assertIn(
            setup.LEGACY_MARKETPLACE_REMOVE_COMMAND,
            json.dumps(legacy),
        )

        unknown = setup.reduce_setup(
            ready_evidence(unknown_plugin_sources=["aws-core@unknown-source"])
        )
        self.assertEqual(unknown["state"], "READY_FOR_INTAKE")
        self.assertIn("unverified source", unknown["observed"])

    def test_each_local_failure_returns_one_action(self) -> None:
        for key in (
            "repository_ready",
            "git_available",
            "python_available",
            "python_version_supported",
            "dependencies_ready",
            "doctor_passed",
        ):
            evidence = ready_evidence()
            evidence[key] = False
            report = setup.reduce_setup(evidence)
            self.assertEqual(report["state"], "LOCAL_PREREQUISITES_REQUIRED")
            self.assertEqual(report["owner_action_id"], "FIX_LOCAL_PREREQUISITE")
            self.assertTrue(report["owner_action"])
            self.assertEqual(report["resume_with"], "init template")
            self.assertEqual(report["aws_access"], "NOT_USED")

    def test_evidence_stdin_is_strict_and_non_secret(self) -> None:
        parsed = setup.read_session_evidence(
            io.StringIO(
                json.dumps(
                    {
                        "dependencies_ready": True,
                        "doctor_passed": True,
                        "official_plugin_enabled": True,
                    }
                )
            )
        )
        self.assertTrue(parsed["dependencies_ready"])
        for payload in (
            '{"hook_trusted": true}',
            '{"AWS_SECRET_ACCESS_KEY": "secret"}',
            '{"official_plugin_enabled": "yes"}',
            '[]',
            '',
        ):
            with self.assertRaises(setup.SetupError):
                setup.read_session_evidence(io.StringIO(payload))

    def test_optional_guide_is_owner_run_official_current_and_no_pin(self) -> None:
        for system, expected_uv in (
            ("Windows", "winget install --id astral-sh.uv"),
            ("Linux", "pipx install uv"),
            ("Darwin", "brew install uv"),
        ):
            guide = setup.build_guide(REPOSITORY_ROOT, system=system)
            rendered = setup.render_guide(guide)
            self.assertIn(setup.CODEX_GUIDE, rendered)
            self.assertIn(setup.AWS_PLUGIN_GUIDE, rendered)
            self.assertIn(setup.MARKETPLACE_COMMAND, rendered)
            self.assertIn(expected_uv, rendered)
            self.assertIn("owner-run instructions", rendered)
            self.assertNotIn("plugin marketplace add .", rendered)
            self.assertNotIn("1.1.0", rendered)
            self.assertNotIn("36f16570", rendered)
            self.assertFalse(guide["executed_external_commands"])
            self.assertEqual(guide["repository_writes"], "NONE")
            if system == "Linux":
                for command in (
                    "sudo apt update",
                    "sudo apt install bubblewrap",
                    "command -v bwrap",
                    "bwrap --version",
                ):
                    self.assertIn(command, rendered)

    def test_script_cannot_execute_installers_or_persist_user_state(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "os.system",
            "Popen(",
            "subprocess.run",
        ):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("execute", setup.main.__doc__ or "")
        self.assertNotIn("approval-digest", source)

    def test_rendered_ready_result_starts_intake_without_second_init(self) -> None:
        rendered = setup.render_setup_response(setup.reduce_setup(ready_evidence()))
        self.assertIn("Next: INTAKE-10 — starts now", rendered)
        self.assertNotIn("START GUIDED INTAKE", rendered)
        self.assertIn("Technical status: READY_FOR_INTAKE", rendered)
        self.assertNotIn("send: init template", rendered.casefold())
        self.assertNotIn("hook", rendered.casefold())

    def test_cli_welcome_and_json_status_are_machine_readable(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "welcome"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), setup.opening_greeting())

        evidence = {
            "dependencies_ready": True,
            "doctor_passed": True,
        }
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "status",
                "--root",
                str(REPOSITORY_ROOT),
                "--json",
                "--evidence-stdin",
            ],
            cwd=REPOSITORY_ROOT,
            check=True,
            input=json.dumps(evidence),
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        self.assertEqual(report["state"], "READY_FOR_INTAKE")
        self.assertIn(report["aws_core_status"], {"AVAILABLE", "DEFERRED_UNTIL_DESIGN"})

    def test_status_does_not_print_executable_or_repository_paths(self) -> None:
        output = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO('{"dependencies_ready":true,"doctor_passed":true}')):
            with redirect_stdout(output):
                exit_code = setup.main(
                    [
                        "status",
                        "--root",
                        str(REPOSITORY_ROOT),
                        "--json",
                        "--evidence-stdin",
                    ]
                )
        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        serialized = json.dumps(report)
        self.assertNotIn(str(REPOSITORY_ROOT), serialized)
        self.assertNotIn("executable", serialized.casefold())

    def test_hostile_manifest_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            try:
                (root / "bootstrap.manifest.json").symlink_to(SCRIPT_PATH)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaises(setup.SetupError):
                setup.canonical_root(root)


if __name__ == "__main__":
    unittest.main()
