from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "fastlane_presenter.py"
SPEC = importlib.util.spec_from_file_location("fastlane_presenter", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
presenter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(presenter)


def report(**updates: object) -> dict[str, object]:
    interaction: dict[str, object] = {
        "owner_stage": "DEFINE",
        "response_mode": "OWNER_UPDATE",
        "state": "NEEDS_INPUT",
        "route_reason_code": "INTAKE_REQUIRED",
        "owner_action_required": True,
        "owner_action_kind": "ANSWER_OPEN_DECISIONS",
        "blocking_ids": [],
        "automatic_continuation_allowed": False,
        "formal_receipt_required": False,
        "aws_core": {"materiality": "NOT_MATERIAL", "evidence_status": "NOT_REQUIRED"},
    }
    interaction.update(updates)
    return {"interaction": interaction}


class FastlanePresenterTests(unittest.TestCase):
    def test_owner_update_has_one_action_and_no_internal_prompt_id(self) -> None:
        rendered = presenter.render_owner_update(report())
        self.assertTrue(rendered.startswith("FASTLANE \u00b7 DEFINE"))
        self.assertEqual(rendered.count("Need from you:"), 1)
        self.assertIn("Copyable reply:", rendered)
        self.assertNotIn("INTAKE-10", rendered)
        self.assertNotIn("NONE", rendered)
        self.assertNotIn("Audit:", rendered)

    def test_automatic_update_says_nothing_and_continues(self) -> None:
        rendered = presenter.render_owner_update(
            report(
                owner_stage="DESIGN",
                state="WORKING",
                route_reason_code="DESIGN_REQUIRED",
                owner_action_required=False,
                owner_action_kind="NONE_CONTINUE_AUTOMATICALLY",
                automatic_continuation_allowed=True,
            ),
            updated="Gate A was approved.",
        )
        self.assertIn("FASTLANE \u00b7 DESIGN", rendered)
        self.assertIn("Need from you: Nothing.", rendered)
        self.assertIn("compare complete architecture candidates", rendered)

    def test_formal_receipt_cannot_use_routine_presenter(self) -> None:
        with self.assertRaises(presenter.PresentationError):
            presenter.render_owner_update(
                report(
                    response_mode="GATE_A",
                    formal_receipt_required=True,
                    owner_action_kind="APPROVE_GATE_A",
                )
            )

    def test_prerequisite_renderer_has_one_action_and_all_steps(self) -> None:
        rendered = presenter.render_prerequisite_update(
            {
                "state": "PREREQUISITES_REQUIRED",
                "checklist": [
                    {"label": "Install Codex", "commands": ["codex --version"]},
                    {"label": "Install uv", "commands": ["uvx --version"]},
                ],
            }
        )
        self.assertEqual(rendered.count("Need from you:"), 1)
        self.assertIn("Install Codex", rendered)
        self.assertIn("Install uv", rendered)

    def test_unknown_or_conflicting_state_fails_closed(self) -> None:
        with self.assertRaises(presenter.PresentationError):
            presenter.render_owner_update(report(route_reason_code="UNKNOWN"))
        with self.assertRaises(presenter.PresentationError):
            presenter.render_owner_update(
                report(owner_action_required=False, owner_action_kind="ANSWER_OPEN_DECISIONS")
            )


if __name__ == "__main__":
    unittest.main()
