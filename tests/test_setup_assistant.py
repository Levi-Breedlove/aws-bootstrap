from __future__ import annotations

import ast
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


REQUIRED_FIELDS = {
    "state",
    "progress_step",
    "observed",
    "explanation",
    "owner_action_id",
    "owner_action",
    "owner_command",
    "verification",
    "resume_with",
    "aws_credentials",
    "aws_access",
    "aws_authorization",
}


class SetupAssistantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project & hostile $ path"
        self.root.mkdir()
        (self.root / "bootstrap.manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "bootstrap_version": "1.1.0",
                    "required_files": ["bootstrap.manifest.json"],
                }
            ),
            encoding="utf-8",
        )
        self.tools = self.root.parent / "local tools"
        self.tools.mkdir()
        self.executables: dict[str, Path] = {}
        for name in ("git", "python", "python3", "bwrap", "uvx", "codex"):
            candidate = self.tools / name
            candidate.write_text("fixture", encoding="utf-8")
            self.executables[name] = candidate

    def which(self, name: str) -> str | None:
        candidate = self.executables.get(name)
        return str(candidate) if candidate else None

    def ready_evidence(self) -> dict[str, object]:
        return {
            "repository_ready": True,
            "dependencies_ready": True,
            "doctor_passed": True,
            "git_available": True,
            "python_available": True,
            "python_version_supported": True,
            "python3_available": True,
            "python3_version_supported": True,
            "bwrap_available": True,
            "uvx_available": True,
            "codex_available": True,
            "surface": "CODEX_CLI",
            "supported_surface": True,
            "codex_logged_in": True,
            "official_marketplace_registered": True,
            "official_plugin_installed": True,
            "official_plugin_enabled": True,
            "official_plugin_loaded_in_session": True,
            "official_plugin_source_verified": True,
            "observed_marketplace_repository": "aws/agent-toolkit-for-aws",
            "observed_plugin_source": "agent-toolkit-for-aws",
            "observed_plugin_identity": "aws-core@agent-toolkit-for-aws",
            "legacy_plugin_enabled": False,
            "unknown_plugin_sources": [],
            "official_plugin_version": "1.1.0",
            "hook_visible": True,
            "hook_source_official": True,
            "hook_plugin_identity": "aws-core@agent-toolkit-for-aws",
            "matching_hooks_inventoried": True,
            "conflicting_hooks": [],
            "hook_reviewed": True,
            "hook_trust_attested_by_owner": True,
            "deny_probe_passed": True,
            "deny_probe_blocked_before_execution": True,
            "allow_probe_passed": True,
            "allow_probe_output": "FASTLANE_HOOK_ALLOW_PROBE",
            "retrieve_skill_passed": True,
            "search_documentation_passed": True,
            "observer": "CODEX_LIVE_TOOL_CALL",
            "invoked_plugin_identity": "aws-core@agent-toolkit-for-aws",
            "retrieve_skill_plugin_identity": "aws-core@agent-toolkit-for-aws",
            "search_documentation_plugin_identity": "aws-core@agent-toolkit-for-aws",
            "requested_skill": "aws-serverless",
            "retrieved_skill": "aws-serverless-application",
            "documentation_query": (
                "AWS Lambda security best practices for serverless applications, "
                "including least-privilege IAM and input validation"
            ),
            "documentation_sources": ["https://docs.aws.amazon.com/lambda/"],
            "credentials_inspected": False,
            "aws_account_accessed": False,
        }

    def assert_state(self, evidence: dict[str, object], expected: str) -> dict[str, object]:
        report = setup.reduce_setup(evidence)
        self.assertEqual(report["state"], expected)
        self.assertTrue(REQUIRED_FIELDS.issubset(report))
        self.assertEqual(report["mode"], "INSTRUCTIONS_ONLY")
        self.assertFalse(report["executed_external_commands"])
        self.assertEqual(report["repository_writes"], "NONE")
        self.assertFalse(report["user_state_persisted_in_repository"])
        return report

    def public_cli_report(self, evidence: dict[str, object]) -> dict[str, object]:
        local = {
            key: value
            for key, value in evidence.items()
            if key not in setup.SESSION_EVIDENCE_FIELDS
        }
        session = {
            key: value
            for key, value in evidence.items()
            if key in setup.SESSION_EVIDENCE_FIELDS
        }
        output = io.StringIO()
        with (
            mock.patch.object(
                setup,
                "inspect_local_prerequisites",
                return_value=local,
            ),
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(session))),
            redirect_stdout(output),
        ):
            result = setup.main(
                [
                    "status",
                    "--root",
                    str(self.root),
                    "--surface",
                    "CODEX_CLI",
                    "--evidence-stdin",
                    "--json",
                ]
            )
        self.assertEqual(result, 0)
        return json.loads(output.getvalue())

    def test_local_inspection_detects_commands_without_executing_or_exposing_paths(self) -> None:
        evidence = setup.inspect_local_prerequisites(
            self.root,
            which=self.which,
            python_version=(3, 12, 1),
            system="Windows",
            surface="CODEX_CLI",
        )
        for key in (
            "git_available",
            "python_available",
            "python_version_supported",
            "python3_available",
            "bwrap_available",
            "uvx_available",
            "codex_available",
            "supported_surface",
        ):
            self.assertTrue(evidence[key])
        self.assertIsNone(evidence["python3_version_supported"])
        serialized = json.dumps(evidence, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn(str(self.tools), serialized)

    def test_repository_local_command_is_not_accepted(self) -> None:
        local_uvx = self.root / "uvx"
        local_uvx.write_text("untrusted fixture", encoding="utf-8")
        evidence = setup.inspect_local_prerequisites(
            self.root,
            which=lambda name: str(local_uvx) if name == "uvx" else self.which(name),
            python_version=(3, 12),
        )
        self.assertFalse(evidence["uvx_available"])

    def test_stdin_evidence_is_strictly_allowlisted_and_typed(self) -> None:
        accepted = setup.read_session_evidence(
            io.StringIO(
                json.dumps(
                    {
                        "dependencies_ready": True,
                        "python3_version": "3.11.7",
                        "hook_trust_attested_by_owner": True,
                        "documentation_sources": ["https://docs.aws.amazon.com/"],
                    }
                )
            )
        )
        self.assertTrue(accepted["dependencies_ready"])
        self.assertTrue(accepted["python3_version_supported"])
        with self.assertRaises(setup.SetupError):
            setup.read_session_evidence(io.StringIO('{"repository_ready": true}'))
        with self.assertRaises(setup.SetupError):
            setup.read_session_evidence(io.StringIO('{"doctor_passed": "yes"}'))
        with self.assertRaises(setup.SetupError):
            setup.read_session_evidence(io.StringIO('{"hook_trusted": true}'))
        for invalid_version in ("3", "3.11.1.2", "Python 3.12", "3.x"):
            with self.subTest(invalid_version=invalid_version):
                with self.assertRaises(setup.SetupError):
                    setup.read_session_evidence(
                        io.StringIO(json.dumps({"python3_version": invalid_version}))
                    )

    def test_python3_is_supported_as_fastlane_interpreter_off_windows(self) -> None:
        self.executables.pop("python")
        evidence = setup.inspect_local_prerequisites(
            self.root,
            which=self.which,
            python_version=(3, 12),
            system="Linux",
        )
        self.assertTrue(evidence["python_available"])
        self.assertEqual(evidence["fastlane_python_command"], "python3")

    def test_python3_version_remains_unverified_when_python_is_also_present(self) -> None:
        evidence = setup.inspect_local_prerequisites(
            self.root,
            which=self.which,
            python_version=(3, 12),
            system="Linux",
        )
        self.assertEqual(evidence["fastlane_python_command"], "python")
        self.assertTrue(evidence["python3_available"])
        self.assertIsNone(evidence["python3_version_supported"])

    def test_explicit_old_python3_version_blocks_hook_runtime(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(
            setup.read_session_evidence(io.StringIO('{"python3_version": "3.10.14"}'))
        )
        self.assert_state(evidence, "HOOK_RUNTIME_REQUIRED")

    def test_native_windows_still_requires_python_and_python3_separately(self) -> None:
        self.executables.pop("python")
        evidence = setup.inspect_local_prerequisites(
            self.root,
            which=self.which,
            python_version=(3, 12),
            system="Windows",
        )
        self.assertFalse(evidence["python_available"])
        self.assertTrue(evidence["python3_available"])

    def test_fresh_setup_requests_official_marketplace(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(
            official_marketplace_registered=False,
            official_plugin_installed=False,
            official_plugin_enabled=False,
            official_plugin_source_verified=False,
        )
        report = self.assert_state(evidence, "OFFICIAL_MARKETPLACE_REQUIRED")
        self.assertEqual(report["owner_command"], setup.MARKETPLACE_COMMAND)

    def test_dependency_checker_and_doctor_are_required_for_ready(self) -> None:
        evidence = self.ready_evidence()
        evidence["dependencies_ready"] = None
        report = self.assert_state(evidence, "LOCAL_PREREQUISITES_REQUIRED")
        self.assertIn("bootstrap_dependencies.py", report["owner_command"])

        evidence["dependencies_ready"] = True
        evidence["doctor_passed"] = False
        report = self.assert_state(evidence, "LOCAL_PREREQUISITES_REQUIRED")
        self.assertIn("bootstrap_doctor.py", report["owner_command"])

    def test_registered_marketplace_without_plugin_requests_installation(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(official_plugin_installed=False, official_plugin_enabled=False)
        report = self.assert_state(evidence, "AWS_CORE_INSTALLATION_REQUIRED")
        combined = f"{report['owner_action']} {report['verification']}".casefold()
        self.assertNotIn("restart", combined)
        self.assertNotIn("new session", combined)

    def test_official_plugin_disabled_requests_enable(self) -> None:
        evidence = self.ready_evidence()
        evidence["official_plugin_enabled"] = False
        self.assert_state(evidence, "AWS_CORE_ENABLE_REQUIRED")

    def test_enabled_plugin_not_loaded_requests_only_a_new_session(self) -> None:
        evidence = self.ready_evidence()
        evidence["official_plugin_loaded_in_session"] = False
        report = self.assert_state(evidence, "AWS_CORE_SESSION_RESTART_REQUIRED")
        self.assertEqual(report["owner_action_id"], "START_NEW_CODEX_SESSION")
        self.assertNotIn("continue setup", report["owner_action"].casefold())

    def test_official_plugin_enabled_is_reused(self) -> None:
        evidence = self.ready_evidence()
        evidence["hook_reviewed"] = False
        report = self.assert_state(evidence, "HOOK_REVIEW_REQUIRED")
        self.assertNotIn("install AWS Core", report["owner_action"])

    def test_legacy_plugin_only_is_source_unverified(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(
            official_plugin_installed=False,
            official_plugin_enabled=False,
            official_plugin_source_verified=False,
            legacy_plugin_enabled=True,
        )
        report = self.assert_state(evidence, "AWS_CORE_SOURCE_UNVERIFIED")
        self.assertIn("legacy", report["observed"].casefold())

    def test_duplicate_official_and_legacy_plugins_block(self) -> None:
        evidence = self.ready_evidence()
        evidence["legacy_plugin_enabled"] = True
        report = self.assert_state(evidence, "AWS_CORE_DUPLICATE_BLOCKED")
        self.assertEqual(len(report["details"]["enabled_sources"]), 2)
        self.assertIn("aws-core@agent-toolkit-for-aws", report["observed"])
        self.assertIn(
            "aws-core@aws-codex-fastlane-dependencies", report["observed"]
        )

    def test_unknown_plugin_source_blocks(self) -> None:
        evidence = self.ready_evidence()
        evidence["official_plugin_enabled"] = False
        evidence["unknown_plugin_sources"] = ["aws-core@unreviewed-marketplace"]
        report = self.assert_state(evidence, "AWS_CORE_SOURCE_UNVERIFIED")
        self.assertIn("aws-core@unreviewed-marketplace", report["observed"])

    def test_official_source_requires_observed_marketplace_identity(self) -> None:
        evidence = self.ready_evidence()
        evidence["observed_marketplace_repository"] = "unreviewed/toolkit"
        self.assert_state(evidence, "AWS_CORE_SOURCE_UNVERIFIED")

    def test_official_source_inventory_and_version_must_be_observed(self) -> None:
        for missing in (
            "legacy_plugin_enabled",
            "unknown_plugin_sources",
            "official_plugin_version",
        ):
            with self.subTest(missing=missing):
                evidence = self.ready_evidence()
                evidence.pop(missing)
                self.assert_state(evidence, "AWS_CORE_SOURCE_UNVERIFIED")
        evidence = self.ready_evidence()
        evidence["observed_plugin_identity"] = "aws-core@unknown"
        self.assert_state(evidence, "AWS_CORE_SOURCE_UNVERIFIED")

    def test_newer_official_version_does_not_block(self) -> None:
        evidence = self.ready_evidence()
        evidence["official_plugin_version"] = "9.0.0"
        evidence["hook_reviewed"] = False
        self.assert_state(evidence, "HOOK_REVIEW_REQUIRED")
        evidence["hook_reviewed"] = True
        report = self.assert_state(evidence, "READY_FOR_INTAKE")
        self.assertTrue(report["aws_core"]["version_differs_from_last_tested"])

    def test_missing_uvx_is_local_prerequisite(self) -> None:
        evidence = self.ready_evidence()
        evidence["uvx_available"] = False
        report = self.assert_state(evidence, "LOCAL_PREREQUISITES_REQUIRED")
        self.assertIsNone(report["owner_command"])
        self.assertIn(setup.UV_GUIDE, report["owner_action"])

    def test_missing_python3_is_hook_runtime_required(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(python3_available=False, system="WINDOWS")
        report = self.assert_state(evidence, "HOOK_RUNTIME_REQUIRED")
        self.assertIn("WSL2", report["explanation"])

    def test_unverified_or_old_python3_hook_runtime_is_blocked(self) -> None:
        evidence = self.ready_evidence()
        evidence["python3_version_supported"] = False
        report = self.assert_state(evidence, "HOOK_RUNTIME_REQUIRED")
        self.assertIn("3.11", report["observed"])

    def test_unsupported_surface_maps_to_local_prerequisite(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(surface="CODEX_IDE_EXTENSION", supported_surface=False)
        report = self.assert_state(evidence, "LOCAL_PREREQUISITES_REQUIRED")
        self.assertIn("IDE extension", report["explanation"])

    def test_supported_web_surface_does_not_require_local_codex_cli(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(
            surface="CHATGPT_WEB_WORK",
            supported_surface=True,
            codex_available=False,
        )
        self.assert_state(evidence, "READY_FOR_INTAKE")

    def test_unverified_login_is_explicit(self) -> None:
        evidence = self.ready_evidence()
        evidence["codex_logged_in"] = None
        self.assert_state(evidence, "CODEX_LOGIN_VERIFICATION_REQUIRED")

    def test_web_login_guidance_does_not_require_codex_cli(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(
            surface="CHATGPT_WEB_WORK",
            supported_surface=True,
            codex_available=False,
            codex_logged_in=False,
        )
        report = self.assert_state(
            evidence, "CODEX_LOGIN_VERIFICATION_REQUIRED"
        )
        self.assertIsNone(report["owner_command"])
        self.assertIn("ChatGPT", report["owner_action"])

    def test_hook_trust_pending_has_its_own_attestation_state(self) -> None:
        evidence = self.ready_evidence()
        evidence["hook_trust_attested_by_owner"] = False
        report = self.assert_state(evidence, "HOOK_TRUST_ATTESTATION_REQUIRED")
        self.assertEqual(report["owner_action_id"], "ATTEST_OFFICIAL_HOOK_TRUST")

    def test_conflicting_hooks_block(self) -> None:
        evidence = self.ready_evidence()
        evidence["conflicting_hooks"] = ["unknown Bash hook"]
        self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")

    def test_probe_pending_and_failures_are_distinct(self) -> None:
        evidence = self.ready_evidence()
        evidence["deny_probe_passed"] = None
        pending = self.assert_state(evidence, "HOOK_PROBES_REQUIRED")
        self.assertEqual(pending["owner_command"], "continue setup")
        rendered = setup.render_setup_response(pending)
        self.assertIn("Current step: Reviewing and testing", rendered)
        self.assertNotIn("Then send:", rendered)
        self.assertTrue(
            rendered.rstrip().endswith(
                "Technical status: HOOK_PROBES_REQUIRED"
            )
        )
        evidence["deny_probe_passed"] = False
        self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")
        evidence["deny_probe_passed"] = True
        evidence["allow_probe_passed"] = False
        self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")

    def test_allow_probe_requires_exact_output(self) -> None:
        evidence = self.ready_evidence()
        evidence["allow_probe_output"] = "unexpected output"
        self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")

    def test_handshake_pending_and_tool_failures_are_distinct(self) -> None:
        evidence = self.ready_evidence()
        evidence["retrieve_skill_passed"] = None
        self.assert_state(evidence, "AWS_CORE_HANDSHAKE_REQUIRED")
        evidence["retrieve_skill_passed"] = False
        retrieve_failure = self.assert_state(
            evidence, "AWS_CORE_VERIFICATION_BLOCKED"
        )
        rendered = setup.render_setup_response(retrieve_failure)
        self.assertIn("Observed plugin source: aws/agent-toolkit-for-aws", rendered)
        self.assertIn(
            "Invoked plugin identity: aws-core@agent-toolkit-for-aws", rendered
        )
        self.assertIn("retrieve_skill: FAIL", rendered)
        self.assertIn("search_documentation: PASS", rendered)
        self.assertIn("Retrieved skill: aws-serverless-application", rendered)
        self.assertIn("Documentation query: AWS Lambda", rendered)
        self.assertIn("https://docs.aws.amazon.com/lambda/", rendered)
        evidence["retrieve_skill_passed"] = True
        evidence["search_documentation_passed"] = False
        search_failure = self.assert_state(
            evidence, "AWS_CORE_VERIFICATION_BLOCKED"
        )
        rendered = setup.render_setup_response(search_failure)
        self.assertIn("retrieve_skill: PASS", rendered)
        self.assertIn("search_documentation: FAIL", rendered)

    def test_missing_attributable_handshake_evidence_blocks(self) -> None:
        evidence = self.ready_evidence()
        evidence["documentation_sources"] = []
        self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")

    def test_handshake_requires_exact_live_observer_skill_query_and_sources(self) -> None:
        invalid_values = {
            "observer": "MODEL_MEMORY",
            "requested_skill": "aws-cdk",
            "documentation_query": "similar but not exact",
            "documentation_sources": ["https://example.com/not-aws"],
            "credentials_inspected": None,
            "aws_account_accessed": None,
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                evidence = self.ready_evidence()
                evidence[field] = value
                self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")

    def test_handshake_blocks_credential_inspection_or_aws_account_access(self) -> None:
        for field in ("credentials_inspected", "aws_account_accessed"):
            with self.subTest(field=field):
                evidence = self.ready_evidence()
                evidence[field] = True
                report = self.assert_state(
                    evidence, "AWS_CORE_VERIFICATION_BLOCKED"
                )
                self.assertIn("credentials", report["explanation"].casefold())

    def test_each_capability_must_be_attributed_to_invoked_official_plugin(self) -> None:
        evidence = self.ready_evidence()
        evidence["search_documentation_plugin_identity"] = "aws-core@unknown"
        report = self.assert_state(evidence, "AWS_CORE_VERIFICATION_BLOCKED")
        self.assertIn("not attributable", report["observed"])

    def test_success_is_friendly_complete_and_idempotent(self) -> None:
        evidence = self.ready_evidence()
        first = self.assert_state(evidence, "READY_FOR_INTAKE")
        second = setup.reduce_setup(dict(evidence))
        self.assertEqual(first, second)
        rendered = setup.render_setup_response(first)
        self.assertIn("Progress: 4 of 4 complete", rendered)
        self.assertIn("START GUIDED INTAKE", rendered)
        self.assertIn("Repository and doctor checks passed", rendered)
        self.assertIn("credentials were not configured or checked", rendered)
        self.assertIn("Observed plugin source: aws/agent-toolkit-for-aws", rendered)
        self.assertIn(
            "Invoked plugin identity: aws-core@agent-toolkit-for-aws", rendered
        )
        self.assertIn("Retrieved skill: aws-serverless-application — PASS", rendered)
        self.assertIn("Documentation query:", rendered)
        self.assertIn("https://docs.aws.amazon.com/lambda/", rendered)
        self.assertEqual(
            first["details"]["invoked_plugin_identity"],
            "aws-core@agent-toolkit-for-aws",
        )

    def test_successful_setup_resumes_from_first_unresolved_state(self) -> None:
        evidence = self.ready_evidence()
        evidence.update(
            official_marketplace_registered=False,
            official_plugin_installed=False,
            official_plugin_enabled=False,
            official_plugin_loaded_in_session=False,
            hook_reviewed=False,
            hook_trust_attested_by_owner=False,
            deny_probe_passed=None,
            deny_probe_blocked_before_execution=None,
            allow_probe_passed=None,
            allow_probe_output=None,
            retrieve_skill_passed=None,
            search_documentation_passed=None,
        )

        expected_states: list[str] = []

        def observe(expected: str) -> None:
            expected_states.append(expected)
            first = setup.reduce_setup(evidence)
            second = setup.reduce_setup(dict(evidence))
            self.assertEqual(first, second)
            self.assertEqual(first["state"], expected)

        observe("OFFICIAL_MARKETPLACE_REQUIRED")
        evidence["official_marketplace_registered"] = True
        observe("AWS_CORE_INSTALLATION_REQUIRED")
        evidence["official_plugin_installed"] = True
        observe("AWS_CORE_ENABLE_REQUIRED")
        evidence["official_plugin_enabled"] = True
        observe("AWS_CORE_SESSION_RESTART_REQUIRED")
        evidence["official_plugin_loaded_in_session"] = True
        observe("HOOK_REVIEW_REQUIRED")
        evidence["hook_reviewed"] = True
        observe("HOOK_TRUST_ATTESTATION_REQUIRED")
        evidence["hook_trust_attested_by_owner"] = True
        observe("HOOK_PROBES_REQUIRED")
        evidence.update(
            deny_probe_passed=True,
            deny_probe_blocked_before_execution=True,
            allow_probe_passed=True,
            allow_probe_output="FASTLANE_HOOK_ALLOW_PROBE",
        )
        observe("AWS_CORE_HANDSHAKE_REQUIRED")
        evidence.update(
            retrieve_skill_passed=True,
            search_documentation_passed=True,
        )
        observe("READY_FOR_INTAKE")
        self.assertEqual(len(expected_states), 9)
        rendered = setup.render_setup_response(setup.reduce_setup(evidence))
        self.assertIn("AWS credentials were not configured or checked", rendered)
        self.assertIn("No AWS account was accessed", rendered)
        self.assertTrue(rendered.rstrip().endswith("Technical status: READY_FOR_INTAKE"))

    def test_all_declared_states_are_reachable_and_have_required_fields(self) -> None:
        base = self.ready_evidence()
        cases: list[tuple[str, dict[str, object]]] = []

        def changed(**updates: object) -> dict[str, object]:
            item = dict(base)
            item.update(updates)
            return item

        cases.extend(
            [
                ("LOCAL_PREREQUISITES_REQUIRED", changed(git_available=False)),
                ("CODEX_LOGIN_VERIFICATION_REQUIRED", changed(codex_logged_in=False)),
                (
                    "OFFICIAL_MARKETPLACE_REQUIRED",
                    changed(
                        official_marketplace_registered=False,
                        official_plugin_installed=False,
                        official_plugin_enabled=False,
                    ),
                ),
                (
                    "AWS_CORE_INSTALLATION_REQUIRED",
                    changed(official_plugin_installed=False, official_plugin_enabled=False),
                ),
                ("AWS_CORE_ENABLE_REQUIRED", changed(official_plugin_enabled=False)),
                (
                    "AWS_CORE_SESSION_RESTART_REQUIRED",
                    changed(official_plugin_loaded_in_session=False),
                ),
                ("AWS_CORE_DUPLICATE_BLOCKED", changed(legacy_plugin_enabled=True)),
                (
                    "AWS_CORE_SOURCE_UNVERIFIED",
                    changed(official_plugin_source_verified=False),
                ),
                ("HOOK_RUNTIME_REQUIRED", changed(python3_available=False)),
                ("HOOK_REVIEW_REQUIRED", changed(hook_reviewed=False)),
                (
                    "HOOK_TRUST_ATTESTATION_REQUIRED",
                    changed(hook_trust_attested_by_owner=False),
                ),
                ("HOOK_PROBES_REQUIRED", changed(deny_probe_passed=None)),
                (
                    "AWS_CORE_HANDSHAKE_REQUIRED",
                    changed(retrieve_skill_passed=None),
                ),
                (
                    "AWS_CORE_VERIFICATION_BLOCKED",
                    changed(retrieve_skill_passed=False),
                ),
                ("READY_FOR_INTAKE", changed()),
            ]
        )
        self.assertEqual({state for state, _ in cases}, set(setup.SETUP_STATES))
        for state, evidence in cases:
            with self.subTest(state=state):
                self.assert_state(evidence, state)
                cli_report = self.public_cli_report(evidence)
                self.assertEqual(cli_report["state"], state)
                self.assertIsInstance(cli_report["owner_action_id"], str)
                self.assertTrue(cli_report["owner_action_id"].strip())
                self.assertIsInstance(cli_report["owner_action"], str)
                self.assertTrue(cli_report["owner_action"].strip())
                self.assertNotIn("owner_actions", cli_report)

    def test_guide_is_chronological_instructions_only(self) -> None:
        guide = setup.build_guide(self.root, system="Windows")
        serialized = json.dumps(guide)
        self.assertEqual(guide["mode"], "INSTRUCTIONS_ONLY")
        self.assertFalse(guide["executed_external_commands"])
        self.assertIn("python3", serialized)
        self.assertIn("uvx", serialized)
        self.assertIn("codex login status", serialized)
        self.assertIn(setup.MARKETPLACE_COMMAND, serialized)
        self.assertIn("WSL2", serialized)
        self.assertIn("sudo apt update", serialized)
        self.assertIn("sudo apt install bubblewrap", serialized)
        self.assertIn("command -v bwrap", serialized)
        self.assertIn("bwrap --version", serialized)
        self.assertNotIn(str(self.root), serialized)

    def test_setup_guide_verifies_bubblewrap_on_wsl_and_linux(self) -> None:
        setup_guide = (REPOSITORY_ROOT / "docs" / "SETUP.md").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(setup_guide.count("command -v bwrap"), 2)
        self.assertGreaterEqual(setup_guide.count("bwrap --version"), 2)

    def test_helper_has_no_external_execution_or_file_write_surface(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_roots.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertNotIn("subprocess", imported_roots)
        self.assertNotIn("os", imported_roots)
        for forbidden in (
            "os.system",
            "Popen",
            "subprocess.run",
            "write_text(",
            "write_bytes(",
            "touch(",
            "mkdir(",
        ):
            self.assertNotIn(forbidden, source)

    def test_status_cli_actionable_state_exits_zero(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "status",
                "--root",
                str(self.root),
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn(report["state"], setup.SETUP_STATES)
        self.assertTrue(REQUIRED_FIELDS.issubset(report))

    def test_unsafe_or_missing_root_exits_nonzero(self) -> None:
        missing = self.root / "missing"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "status",
                "--root",
                str(missing),
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["state"], "LOCAL_PREREQUISITES_REQUIRED")

    def test_cli_exposes_only_status_and_guide(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "execute", "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
