from __future__ import annotations

import hashlib
import io
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "package_release.py"
SPEC = importlib.util.spec_from_file_location("package_release", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
package_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package_release)


class PackageReleaseTests(unittest.TestCase):
    def test_manifest_is_the_only_internal_version_source(self) -> None:
        manifest = json.loads(
            (REPOSITORY_ROOT / "bootstrap.manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["bootstrap_version"], "1.0.0")
        self.assertIn("README.md", manifest["required_files"])
        for removed in ("VERSION", "CONTRIBUTING.md", "CHANGELOG.md"):
            self.assertFalse((REPOSITORY_ROOT / removed).exists())
            self.assertNotIn(removed, manifest["required_files"])
            self.assertNotIn(
                removed,
                (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8"),
            )

    def test_manifest_is_the_exact_template_file_inventory(self) -> None:
        template = REPOSITORY_ROOT
        actual = {
            path.relative_to(template).as_posix()
            for path in template.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
            and "dist" not in path.parts
        }
        manifest = json.loads(
            (template / "bootstrap.manifest.json").read_text(encoding="utf-8")
        )
        expected = set(manifest["required_files"])
        self.assertEqual(actual, expected)
        self.assertEqual(manifest["required_files"], sorted(expected))

    def test_archive_is_an_exact_deterministic_projection(self) -> None:
        first = package_release.build_release_bytes(REPOSITORY_ROOT)
        second = package_release.build_release_bytes(REPOSITORY_ROOT)
        self.assertEqual(first, second)

        _version, files = package_release.load_release_files(REPOSITORY_ROOT)
        expected_names = [
            package_release.archive_member(relative) for relative, _content in files
        ]
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            infos = archive.infolist()
            self.assertEqual([info.filename for info in infos], expected_names)
            self.assertIsNone(archive.testzip())
            for info, (_relative, content) in zip(infos, files, strict=True):
                self.assertEqual(info.date_time, package_release.FIXED_TIMESTAMP)
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, stat.S_IFREG | 0o644)
                self.assertEqual(info.extra, b"")
                self.assertEqual(info.comment, b"")
                self.assertEqual(archive.read(info), content)
                self.assertFalse(info.filename.endswith((".zip", ".zip.sha256")))

    def test_extracted_release_configures_in_place_and_passes_doctor(self) -> None:
        payload = package_release.build_release_bytes(REPOSITORY_ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                archive.extractall(destination)
            project = destination / package_release.ARCHIVE_ROOT
            setup = subprocess.run(
                [
                    sys.executable,
                    "bootstrap.py",
                    "--target",
                    str(project),
                    "--project-name",
                    "Release ZIP Example",
                    "--region",
                    "us-west-2",
                    "--budget",
                    "$20/month",
                    "--in-place-template-instance",
                ],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            doctor = subprocess.run(
                [
                    sys.executable,
                    "scripts/bootstrap_doctor.py",
                    "--root",
                    str(project),
                    "--json",
                ],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            report = json.loads(doctor.stdout)
            self.assertEqual(report["classification"], "ACTIVE_GREENFIELD")
            self.assertEqual(report["status"], "READY")
            self.assertEqual(report["next_prompt"], "INTAKE-10")

    def test_manifest_hashes_are_current(self) -> None:
        manifest_check = subprocess.run(
            [sys.executable, "scripts/update_manifest.py", "--check"],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            manifest_check.returncode,
            0,
            manifest_check.stdout + manifest_check.stderr,
        )

    def test_public_template_has_no_demo_or_simulation_entrypoint(self) -> None:
        self.assertFalse((REPOSITORY_ROOT / "scripts" / "run_demo.py").exists())
        manifest = json.loads(
            (REPOSITORY_ROOT / "bootstrap.manifest.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("scripts/run_demo.py", manifest["required_files"])
        self.assertNotIn(
            "docs/demo/internal-change-request-api.md",
            manifest["required_files"],
        )
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("run_demo.py", readme)
        self.assertNotIn("docs/demo/", readme)

    def test_written_checksum_is_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / package_release.ARCHIVE_NAME
            digest = package_release.write_release(REPOSITORY_ROOT, archive_path)
            self.assertEqual(digest, hashlib.sha256(archive_path.read_bytes()).hexdigest())
            self.assertEqual(
                package_release.checksum_path(archive_path).read_text(encoding="ascii"),
                f"{digest}  {archive_path.name}\n",
            )

    def test_check_cli_validates_without_committed_artifacts(self) -> None:
        self.assertFalse((REPOSITORY_ROOT / package_release.ARCHIVE_NAME).exists())
        self.assertFalse(
            (REPOSITORY_ROOT / f"{package_release.ARCHIVE_NAME}.sha256").exists()
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--check"],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Release package verified in memory", result.stdout)

    def test_default_output_is_ignored_dist_directory(self) -> None:
        default_output = (
            REPOSITORY_ROOT
            / package_release.DEFAULT_OUTPUT_DIRECTORY
            / package_release.ARCHIVE_NAME
        )
        self.assertEqual(default_output.parent.name, "dist")
        gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/dist/", gitignore.splitlines())

    def test_check_release_rejects_non_deterministic_builds(self) -> None:
        with mock.patch.object(
            package_release,
            "build_release_bytes",
            side_effect=[b"first", b"second"],
        ):
            with self.assertRaisesRegex(
                package_release.PackagingError,
                "different bytes",
            ):
                package_release.check_release(REPOSITORY_ROOT)

    def test_custom_output_checksum_names_custom_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "custom-fastlane.zip"
            digest = package_release.write_release(REPOSITORY_ROOT, archive_path)
            self.assertEqual(
                package_release.checksum_path(archive_path).read_text(encoding="ascii"),
                f"{digest}  {archive_path.name}\n",
            )
            self.assertEqual(
                package_release.expected_artifacts(
                    REPOSITORY_ROOT,
                    archive_path.name,
                ),
                (
                    archive_path.read_bytes(),
                    package_release.checksum_path(archive_path).read_bytes(),
                ),
            )

    def test_unsafe_manifest_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "bootstrap.manifest.json").write_text(
                json.dumps(
                    {
                        "bootstrap_version": "1.0.0",
                        "required_files": ["../outside"],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(package_release.PackagingError, "Unsafe"):
                package_release.load_release_files(root)

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_symlinked_release_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root
            outside = root / "outside"
            outside.write_text("not release content", encoding="utf-8")
            try:
                (template / "README.md").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"Symbolic links are unavailable: {exc}")
            (template / "bootstrap.manifest.json").write_text(
                json.dumps(
                    {
                        "bootstrap_version": "1.0.0",
                        "required_files": ["README.md"],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(package_release.PackagingError, "unsafe"):
                package_release.load_release_files(root)

    def test_invalid_manifest_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root
            (template / "bootstrap.manifest.json").write_text(
                json.dumps(
                    {
                        "bootstrap_version": "personal",
                        "required_files": ["bootstrap.manifest.json"],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(package_release.PackagingError, "semantic version"):
                package_release.load_release_files(root)

    def test_current_release_text_has_no_previous_major_reference(self) -> None:
        forbidden = "2" + ".0.0"
        text_suffixes = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}
        for path in REPOSITORY_ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix not in text_suffixes:
                continue
            content = path.read_text(encoding="utf-8")
            self.assertNotIn(forbidden, content, str(path.relative_to(REPOSITORY_ROOT)))


if __name__ == "__main__":
    unittest.main()
