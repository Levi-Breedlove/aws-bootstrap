from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


bootstrap = load_module(
    "bootstrap_under_test", REPOSITORY_ROOT / "my-project" / "bootstrap.py"
)


class BootstrapSafetyTests(unittest.TestCase):
    def test_rejects_target_inside_source_before_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source"
            source.mkdir()
            (source / "template.txt").write_text("template", encoding="utf-8")
            target = source / "generated" / "project"

            with self.assertRaisesRegex(ValueError, "must not overlap"):
                bootstrap.copy_template(source, target, {}, force=False)

            self.assertFalse(target.exists())

    def test_rejects_source_inside_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "parent"
            source = target / "source"
            source.mkdir(parents=True)

            with self.assertRaisesRegex(ValueError, "must not overlap"):
                bootstrap.validate_non_overlapping_paths(source, target)

    def test_dry_run_does_not_create_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            (source / "PRD.md").write_text("My AWS Project", encoding="utf-8")

            report = bootstrap.copy_template(
                source,
                target,
                {"My AWS Project": "Example"},
                force=False,
                dry_run=True,
            )

            self.assertEqual(report.planned, 1)
            self.assertEqual(report.written, 0)
            self.assertFalse(target.exists())

    def test_collision_free_copy_renders_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            (source / "nested").mkdir()
            (source / "nested" / "PRD.md").write_text(
                "My AWS Project",
                encoding="utf-8",
            )

            report = bootstrap.copy_template(
                source,
                target,
                {"My AWS Project": "Example"},
                force=False,
            )

            self.assertEqual(report.planned, 1)
            self.assertEqual(report.written, 1)
            self.assertEqual(
                (target / "nested" / "PRD.md").read_text(encoding="utf-8"),
                "Example",
            )

    def test_existing_user_file_is_preserved_as_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            (source / "PRD.md").write_text("generated", encoding="utf-8")
            (source / "new.txt").write_text("new", encoding="utf-8")
            destination = target / "PRD.md"
            destination.write_text("user content", encoding="utf-8")

            report = bootstrap.copy_template(source, target, {}, force=False)

            self.assertEqual(report.collisions, 1)
            self.assertEqual(report.written, 0)
            self.assertEqual(destination.read_text(encoding="utf-8"), "user content")
            self.assertFalse((target / "new.txt").exists())

    def test_identical_file_is_unchanged_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            (source / "same.txt").write_text("same", encoding="utf-8")
            destination = target / "same.txt"
            destination.write_text("same", encoding="utf-8")
            original_stat = destination.stat()

            report = bootstrap.copy_template(source, target, {}, force=True)

            self.assertEqual(report.unchanged, 1)
            self.assertEqual(report.written, 0)
            self.assertEqual(destination.stat().st_mtime_ns, original_stat.st_mtime_ns)

    def test_source_symlink_is_rejected_before_target_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            target = root / "target"
            outside = root / "outside.txt"
            source.mkdir()
            outside.write_text("secret", encoding="utf-8")
            try:
                os.symlink(outside, source / "linked.txt")
            except OSError as exc:
                self.skipTest(f"Symbolic links are unavailable: {exc}")

            with self.assertRaisesRegex(ValueError, "unsupported symbolic link"):
                bootstrap.copy_template(source, target, {}, force=False)

            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
