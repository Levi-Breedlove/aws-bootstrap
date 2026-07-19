from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "uv_setup_assistant.py"
SPEC = importlib.util.spec_from_file_location("uv_setup_assistant", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class UvSetupAssistantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project & hostile $ path"
        self.root.mkdir()
        manifest = {
            "schema_version": 1,
            "bootstrap_version": "1.0.0",
            "required_files": ["bootstrap.manifest.json"],
        }
        (self.root / "bootstrap.manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        self.tools = self.root.parent / "local tools"
        self.tools.mkdir()
        self.winget = self.tools / "winget.exe"
        self.uvx = self.tools / "uvx.exe"
        self.pipx = self.tools / "pipx"
        self.winget.write_bytes(b"winget fixture")
        self.uvx.write_bytes(b"uvx fixture")
        self.pipx.write_bytes(b"pipx fixture")

    def test_windows_plan_is_instruction_only_and_exposes_no_local_path(self) -> None:
        report = setup.build_plan(
            self.root,
            which=lambda name: str(self.winget) if name == "winget" else None,
            system="Windows",
        )
        self.assertEqual(report["state"], "UV_INSTALL_INSTRUCTIONS_REQUIRED")
        self.assertEqual(report["mode"], "INSTRUCTIONS_ONLY")
        self.assertFalse(report["executed"])
        self.assertEqual(report["repository_writes"], "NONE")
        self.assertFalse(report["user_state_persisted_in_repository"])
        self.assertEqual(
            report["owner_install"]["command"],
            [
                "winget",
                "install",
                "--id",
                setup.UV_WINGET_ID,
                "--exact",
                "--source",
                "winget",
            ],
        )
        self.assertTrue(report["owner_install"]["package_manager_detected"])
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn(str(self.winget), serialized)
        self.assertNotIn("approval_digest", serialized)

    def test_missing_linux_package_manager_returns_official_guide_only(self) -> None:
        report = setup.build_plan(
            self.root,
            which=lambda _name: None,
            system="Linux",
        )
        self.assertEqual(report["state"], "UV_INSTALL_INSTRUCTIONS_REQUIRED")
        self.assertEqual(report["owner_install"]["method"], "OFFICIAL_GUIDE")
        self.assertIsNone(report["owner_install"]["command"])
        self.assertEqual(report["official_guide"], setup.OFFICIAL_GUIDE)

    def test_existing_uvx_is_detected_but_not_executed_or_disclosed(self) -> None:
        report = setup.build_plan(
            self.root,
            which=lambda name: str(self.uvx) if name == "uvx" else None,
            system="Windows",
        )
        self.assertEqual(report["state"], "UV_DETECTED_OWNER_VERIFICATION_REQUIRED")
        self.assertEqual(report["verification_command"], ["uvx", "--version"])
        self.assertFalse(report["executed"])
        self.assertNotIn(str(self.uvx), json.dumps(report, sort_keys=True))

    def test_repository_local_uvx_is_not_treated_as_installed(self) -> None:
        local_uvx = self.root / "uvx.exe"
        local_uvx.write_text("untrusted repository fixture", encoding="utf-8")
        report = setup.build_plan(
            self.root,
            which=lambda name: str(local_uvx) if name == "uvx" else None,
            system="Linux",
        )
        self.assertEqual(report["state"], "UV_INSTALL_INSTRUCTIONS_REQUIRED")

    def test_non_windows_pipx_instruction_is_owner_run(self) -> None:
        report = setup.build_plan(
            self.root,
            which=lambda name: str(self.pipx) if name == "pipx" else None,
            system="Linux",
        )
        self.assertEqual(report["owner_install"]["method"], "PIPX")
        self.assertEqual(report["owner_install"]["command"], ["pipx", "install", "uv"])
        self.assertTrue(report["owner_install"]["package_manager_detected"])

    def test_helper_contains_no_command_execution_surface(self) -> None:
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
            "execute_plan",
            "approval_digest",
            "APPROVE UV INSTALL",
            "shell=True",
            "os.system",
            "Popen",
        ):
            self.assertNotIn(forbidden, source)

    def test_cli_exposes_plan_only(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "execute", "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_dependency_contract_is_instruction_only_and_persists_no_user_state(self) -> None:
        dependency_path = REPOSITORY_ROOT / "scripts" / "bootstrap_dependencies.py"
        dependency_spec = importlib.util.spec_from_file_location("deps_for_uv", dependency_path)
        assert dependency_spec is not None and dependency_spec.loader is not None
        module = importlib.util.module_from_spec(dependency_spec)
        dependency_spec.loader.exec_module(module)
        report = module.inspect_repository(REPOSITORY_ROOT)
        contract = report["aws_agent_toolkit"]["uv_setup"]
        self.assertEqual(contract["status"], "UV_SETUP_ASSISTANCE_AVAILABLE")
        self.assertEqual(contract["mode"], "INSTRUCTIONS_ONLY")
        self.assertFalse(contract["automatic_runtime_installation"])
        self.assertFalse(contract["user_state_persisted_in_repository"])
        serialized = json.dumps(
            json.loads((REPOSITORY_ROOT / "bootstrap.yaml").read_text(encoding="utf-8")),
            sort_keys=True,
        ).casefold()
        for forbidden in (
            "client_path",
            "cli_version",
            "plugin_installation",
            "hook_trust",
            "credential",
            "username",
            "setup_history",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
