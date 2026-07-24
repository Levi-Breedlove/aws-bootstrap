from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "aws_canary_eval.py"
SPEC = importlib.util.spec_from_file_location("aws_canary_eval_pr4", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
aws_canary_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aws_canary_eval)


class AwsCanaryEvaluationTests(unittest.TestCase):
    def safe_run(self, canary_id: str, index: int) -> dict[str, object]:
        digest = "sha256:" + f"{index:x}" * 64
        step_results = {
            step: {
                "status": "PASS",
                "evidence_reference": f"{canary_id}:{step}",
            }
            for step in aws_canary_eval.REQUIRED_STEPS
        }
        return {
            "canary_id": canary_id,
            "run_reference": f"canary-run-{index}",
            "observed_live_run": True,
            "aws_account_accessed": True,
            "credentials_inspected": False,
            "secret_values_recorded": False,
            "account": "123456789012",
            "region": "us-west-2",
            "environment": f"canary-{index}",
            "profile_or_role": f"FastlaneCanaryRole{index}",
            "artifact_digest": digest,
            "plan_binding": {
                "type": "CLOUDFORMATION_CHANGE_SET",
                "identifier": f"arn:aws:cloudformation:us-west-2:123456789012:changeSet/canary-{index}",
                "digest": digest,
            },
            "deployed_resource_boundary": [f"fastlane-canary-{index}-*"],
            "action_receipts": {
                "gate_a": f"gate-a-{index}",
                "gate_b": f"gate-b-{index}",
                "deployment": f"aws-auth-{index}",
                "teardown": f"teardown-auth-{index}",
            },
            "cost": {
                "currency": "USD",
                "ceiling": 5.0,
                "observed": 0.5,
                "period_start": "2026-07-23T12:00:00Z",
                "period_end": "2026-07-23T13:00:00Z",
            },
            "aws_core_evidence": {
                "marketplace_repository": "aws/agent-toolkit-for-aws",
                "plugin_identity": "aws-core@agent-toolkit-for-aws",
                "retrieve_skill_result": "PASS",
                "retrieved_skill_identifier": "aws-serverless",
                "search_documentation_result": "PASS",
                "documentation_query": "AWS canary least privilege guidance",
                "official_references": [
                    "https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html"
                ],
                "observed_at": "2026-07-23T12:00:00Z",
                "credentials_inspected": False,
                "aws_account_accessed": False,
            },
            "cloudtrail_evidence_reference": f"cloudtrail-event-{index}",
            "controlled_failure": {
                "scenario": "one bounded dependency failure",
                "expected_behavior": "service fails safely and signals rollback",
                "observed_behavior": "service failed safely and signaled rollback",
                "evidence_reference": f"failure-{index}",
            },
            "rollback_result": {
                "status": "PASS",
                "evidence_reference": f"rollback-{index}",
            },
            "teardown_result": {
                "status": "PASS",
                "evidence_reference": f"teardown-{index}",
            },
            "residual_resources": [],
            "billing_check": {
                "currency": "USD",
                "observed_amount": 0.5,
                "observed_at": "2026-07-23T13:00:00Z",
                "follow_up_at": "2026-07-24T13:00:00Z",
                "reference": f"billing-{index}",
            },
            "steps": step_results,
        }

    def safe_payload(self) -> dict[str, object]:
        return {
            "schema_version": aws_canary_eval.SCHEMA_VERSION,
            "runs": [
                self.safe_run(canary["id"], index)
                for index, canary in enumerate(aws_canary_eval.CANARIES, 1)
            ],
        }

    def assert_fails_with(self, payload: dict[str, object], fragment: str) -> None:
        result, passed = aws_canary_eval.score_payload(payload)
        self.assertFalse(passed)
        self.assertTrue(
            any(fragment in error for error in result["errors"]),
            result["errors"],
        )

    def test_plan_defines_three_complete_canaries_without_automatic_aws(self) -> None:
        plan = aws_canary_eval.plan_payload()
        self.assertEqual(len(plan["canaries"]), 3)
        self.assertEqual(
            {canary["id"] for canary in plan["canaries"]},
            {
                "synchronous-managed-serverless",
                "asynchronous-event-driven",
                "container-based",
            },
        )
        for canary in plan["canaries"]:
            self.assertEqual(canary["required_steps"], list(aws_canary_eval.REQUIRED_STEPS))
        self.assertFalse(plan["constraints"]["framework_maintenance_accesses_aws"])
        self.assertTrue(
            plan["constraints"]["live_execution_requires_exact_deployment_authority"]
        )
        self.assertTrue(
            plan["constraints"]["teardown_requires_separate_exact_authority"]
        )

    def test_complete_observed_suite_passes(self) -> None:
        result, passed = aws_canary_eval.score_payload(self.safe_payload())
        self.assertTrue(passed, result["errors"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(set(result["canary_runs"]), {c["id"] for c in aws_canary_eval.CANARIES})

    def test_all_three_canaries_are_required_exactly_once(self) -> None:
        payload = self.safe_payload()
        payload["runs"].pop()
        self.assert_fails_with(payload, "container-based requires exactly one observed run")
        payload = self.safe_payload()
        payload["runs"].append(copy.deepcopy(payload["runs"][0]))
        self.assert_fails_with(
            payload,
            "synchronous-managed-serverless requires exactly one observed run",
        )

    def test_unknown_fields_and_secret_recording_fail_closed(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["access_key"] = "redacted"
        self.assert_fails_with(payload, "unknown fields: access_key")
        payload = self.safe_payload()
        payload["runs"][0]["secret_values_recorded"] = True
        self.assert_fails_with(payload, "secret_values_recorded must be false")
        payload = self.safe_payload()
        payload["runs"][0]["credentials_inspected"] = True
        self.assert_fails_with(payload, "credentials_inspected must be false")

    def test_identity_region_artifact_and_plan_binding_are_exact(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["account"] = "UNKNOWN!"
        self.assert_fails_with(payload, "account must be a 12-digit ID or exact alias")
        payload = self.safe_payload()
        payload["runs"][0]["region"] = "west"
        self.assert_fails_with(payload, "region must be an exact AWS Region")
        payload = self.safe_payload()
        payload["runs"][0]["artifact_digest"] = "latest"
        self.assert_fails_with(payload, "artifact_digest must be an immutable SHA-256")
        payload = self.safe_payload()
        payload["runs"][0]["plan_binding"]["type"] = "UNBOUND"
        self.assert_fails_with(payload, "plan_binding.type is invalid")

    def test_cost_is_finite_currency_bound_and_below_ceiling(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["cost"]["ceiling"] = float("inf")
        self.assert_fails_with(payload, "cost.ceiling must be finite and positive")
        payload = self.safe_payload()
        payload["runs"][0]["cost"]["observed"] = 6.0
        payload["runs"][0]["billing_check"]["observed_amount"] = 6.0
        self.assert_fails_with(payload, "cost.observed exceeds the authorized ceiling")
        payload = self.safe_payload()
        payload["runs"][0]["billing_check"]["currency"] = "EUR"
        self.assert_fails_with(payload, "billing_check.currency must match cost.currency")

    def test_aws_core_evidence_must_be_official_attributable_and_unauthenticated(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["aws_core_evidence"]["plugin_identity"] = "generic-aws-docs"
        self.assert_fails_with(payload, "aws_core_evidence plugin is not official")
        payload = self.safe_payload()
        payload["runs"][0]["aws_core_evidence"]["search_documentation_result"] = "FAIL"
        self.assert_fails_with(
            payload,
            "aws_core_evidence.search_documentation_result must be PASS",
        )
        payload = self.safe_payload()
        payload["runs"][0]["aws_core_evidence"]["official_references"] = [
            "https://example.com/aws"
        ]
        self.assert_fails_with(
            payload,
            "official_references must be official AWS URLs",
        )
        payload = self.safe_payload()
        payload["runs"][0]["aws_core_evidence"]["aws_account_accessed"] = True
        self.assert_fails_with(
            payload,
            "aws_core_evidence.aws_account_accessed must be false",
        )

    def test_failure_rollback_teardown_residual_and_every_step_are_observed(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["rollback_result"]["status"] = "FAILED"
        self.assert_fails_with(payload, "rollback_result.status must be PASS")
        payload = self.safe_payload()
        payload["runs"][0]["teardown_result"]["status"] = "PENDING"
        self.assert_fails_with(payload, "teardown_result.status must be PASS")
        payload = self.safe_payload()
        payload["runs"][0]["steps"].pop("controlled_failure")
        self.assert_fails_with(payload, "steps is missing fields: controlled_failure")
        payload = self.safe_payload()
        payload["runs"][0]["residual_resources"] = [
            {
                "identifier": "unexpected-table",
                "status": "UNAUTHORIZED",
                "reason": "teardown missed it",
                "billing_dimension": "storage",
            }
        ]
        self.assert_fails_with(payload, "status must be AUTHORIZED_RETAINED")

    def test_docs_define_three_canaries_mcp_conditions_and_separate_roles(self) -> None:
        canary_doc = (REPOSITORY_ROOT / "docs" / "AWS-CANARY.md").read_text(
            encoding="utf-8"
        )
        for text in (
            "Synchronous managed-serverless application",
            "Asynchronous event-driven workflow",
            "Container-based application",
            "aws:ViaAWSMCPService",
            "aws:CalledViaAWSMCP",
            "Design and read-only discovery role",
            "Deployment role",
            "Teardown role",
            "illustrative",
            "does not access AWS",
        ):
            self.assertIn(text, canary_doc)
        self.assertIn("AUTHORIZE AWS DEPLOYMENT", canary_doc)
        self.assertIn("AUTHORIZE AWS TEARDOWN", canary_doc)

    def test_evaluator_has_no_aws_network_or_process_execution_path(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import boto3",
            "import botocore",
            "import subprocess",
            "import socket",
            "import urllib",
            "import requests",
            "AWS_ACCESS_KEY",
            "AWS_SECRET_ACCESS_KEY",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
