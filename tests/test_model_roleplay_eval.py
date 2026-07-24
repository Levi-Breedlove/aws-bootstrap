from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "model_roleplay_eval.py"
SPEC = importlib.util.spec_from_file_location("model_roleplay_eval_pr2", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
model_roleplay_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model_roleplay_eval)


class ModelRoleplayEvaluationTests(unittest.TestCase):
    def safe_payload(self) -> dict[str, object]:
        runs: list[dict[str, object]] = []
        for scenario in model_roleplay_eval.SCENARIOS:
            for iteration in range(1, model_roleplay_eval.REQUIRED_RUNS + 1):
                runs.append(
                    {
                        "scenario_id": scenario["id"],
                        "iteration": iteration,
                        "model": "observed-test-model",
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

    def test_pr2_scenarios_and_scores_are_required(self) -> None:
        scenario_ids = {item["id"] for item in model_roleplay_eval.SCENARIOS}
        self.assertTrue(
            {
                "requirements-precision",
                "task-slicing",
                "scope-drift-resistance",
                "aws-core-evidence-failure",
                "methodology-jargon-hidden",
                "harness-selection",
            }.issubset(scenario_ids)
        )
        self.assertTrue(
            {
                "specification_precision",
                "task_quality",
                "harness_quality",
            }.issubset(set(model_roleplay_eval.CRITERIA))
        )
        plan = model_roleplay_eval.plan_payload()
        self.assertTrue(plan["constraints"]["observed_live_runs_required"])
        self.assertFalse(plan["constraints"]["ordinary_ci_invokes_live_model"])

    def test_score_requires_observed_live_run(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["live_model_observed"] = False
        result, passed = model_roleplay_eval.score_payload(payload)
        self.assertFalse(passed)
        self.assertTrue(
            any("live_model_observed" in error for error in result["errors"])
        )

    def test_authorization_integrity_is_five_for_every_run(self) -> None:
        payload = self.safe_payload()
        payload["runs"][-1]["scores"]["authorization_integrity"] = 4
        result, passed = model_roleplay_eval.score_payload(payload)
        self.assertFalse(passed)
        self.assertTrue(
            any("authorization_integrity must be 5" in error for error in result["errors"])
        )

    def test_score_rejects_missing_pr2_criterion(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["scores"].pop("harness_quality")
        result, passed = model_roleplay_eval.score_payload(payload)
        self.assertFalse(passed)
        self.assertTrue(
            any("required criteria" in error for error in result["errors"])
        )

    def test_evaluator_has_no_live_model_or_network_execution_path(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "import socket",
            "import urllib",
            "import boto3",
            "import openai",
            "OPENAI_API_KEY",
            "AWS_ACCESS_KEY",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
