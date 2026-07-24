from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "model_roleplay_eval.py"
SPEC = importlib.util.spec_from_file_location("model_roleplay_eval", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
model_roleplay_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model_roleplay_eval)


class TemplateCompatibilityTests(unittest.TestCase):
    def passing_payload(self) -> dict[str, object]:
        runs: list[dict[str, object]] = []
        for scenario in model_roleplay_eval.SCENARIOS:
            for iteration in range(1, model_roleplay_eval.REQUIRED_RUNS + 1):
                runs.append(
                    {
                        "scenario_id": scenario["id"],
                        "iteration": iteration,
                        "model": "synthetic-test-model",
                        "evidence_reference": f"{scenario['id']}:{iteration}",
                        "live_model_observed": True,
                        "scores": {
                            criterion: 5
                            for criterion in model_roleplay_eval.CRITERIA
                        },
                        "violations": [],
                        "credentials_inspected": False,
                        "aws_account_accessed": False,
                    }
                )
        return {"runs": runs}

    def test_setup_policy_matches_setup_first_runtime(self) -> None:
        security = (REPOSITORY_ROOT / "SECURITY.md").read_text(encoding="utf-8")
        dependency = (
            REPOSITORY_ROOT / "docs" / "DEPENDENCY-POLICY.md"
        ).read_text(encoding="utf-8")
        combined = security + "\n" + dependency
        stale_missing_policy = "Missing AWS Core never " + "blocks initialization"
        stale_optional_policy = "AWS Core is optional during " + "BOOT-00"
        self.assertNotIn(stale_missing_policy, combined)
        self.assertNotIn(stale_optional_policy, combined)
        expected = "Fresh templates require current official AWS Core before initialization"
        self.assertIn(expected, security)
        self.assertIn(expected, dependency)
        self.assertIn("Initialized projects skip the prerequisite gate", combined)

    def test_model_roleplay_plan_is_complete_and_non_operational(self) -> None:
        plan = model_roleplay_eval.plan_payload()
        self.assertEqual(len(plan["scenarios"]), 13)
        self.assertEqual(set(plan["criteria"]), set(model_roleplay_eval.CRITERIA))
        self.assertFalse(plan["constraints"]["ordinary_ci_invokes_live_model"])
        self.assertTrue(plan["constraints"]["observed_live_runs_required"])
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "subprocess",
            "OPENAI_API_KEY",
            "AWS_ACCESS_KEY",
            "boto3",
            "urllib",
            "socket",
        ):
            self.assertNotIn(forbidden, source)

    def test_model_roleplay_score_accepts_complete_safe_evidence(self) -> None:
        result, passed = model_roleplay_eval.score_payload(self.passing_payload())
        self.assertTrue(passed, result)
        self.assertEqual(result["status"], "PASS")

    def test_model_roleplay_score_rejects_regression_and_unsafe_evidence(self) -> None:
        payload = self.passing_payload()
        first = payload["runs"][0]
        first["scores"]["authorization_integrity"] = 4
        first["credentials_inspected"] = True
        first["aws_account_accessed"] = True
        result, passed = model_roleplay_eval.score_payload(payload)
        self.assertFalse(passed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(
            any("authorization_integrity" in error for error in result["errors"])
        )
        self.assertTrue(any("credentials" in error for error in result["errors"]))
        self.assertTrue(any("AWS account" in error for error in result["errors"]))

    def test_model_roleplay_score_rejects_missing_scenarios(self) -> None:
        result, passed = model_roleplay_eval.score_payload({"runs": []})
        self.assertFalse(passed)
        for scenario in model_roleplay_eval.SCENARIOS:
            self.assertTrue(
                any(scenario["id"] in error for error in result["errors"])
            )


if __name__ == "__main__":
    unittest.main()
