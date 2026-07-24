from __future__ import annotations

import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "aws_canary_eval.py"
SPEC = importlib.util.spec_from_file_location("aws_canary_eval_preview", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
aws_canary_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aws_canary_eval)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class AwsCanaryEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.bundle = Path(self.temporary.name)

    def safe_run(self, canary_id: str, index: int) -> dict[str, object]:
        manifest: dict[str, dict[str, str]] = {}
        for key in aws_canary_eval.EVIDENCE_KEYS:
            path = self.bundle / canary_id / f"{key}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{canary_id} {key} observed evidence\n", encoding="utf-8")
            manifest[key] = {
                "path": path.relative_to(self.bundle).as_posix(),
                "sha256": digest(path),
            }
        artifact = "sha256:" + f"{index:x}" * 64
        plan = {
            "type": "CLOUDFORMATION_CHANGE_SET",
            "identifier": f"canary-plan-{index}",
            "digest": "sha256:" + f"{index + 3:x}" * 64,
        }
        resources = [f"arn:aws:cloudformation:us-west-2:111122223333:stack/canary-{index}"]
        operations = ["cloudformation:CreateStack", "cloudformation:UpdateStack"]
        chronology = {
            "deployment_authorized_at": "2027-01-01T00:00:00+00:00",
            "deployment_started_at": "2027-01-01T00:01:00+00:00",
            "controlled_failure_at": "2027-01-01T00:02:00+00:00",
            "rollback_completed_at": "2027-01-01T00:03:00+00:00",
            "teardown_authorized_at": "2027-01-01T00:04:00+00:00",
            "teardown_completed_at": "2027-01-01T00:05:00+00:00",
            "billing_observed_at": "2027-01-01T00:06:00+00:00",
            "follow_up_at": "2027-01-02T00:06:00+00:00",
        }
        common = {
            "account": "111122223333",
            "region": "us-west-2",
            "environment": f"canary-{index}",
            "profile_or_role": "FastlaneCanaryDeploymentRole",
        }
        return {
            "canary_id": canary_id,
            "run_reference": f"canary-run-{index}",
            **common,
            "artifact_digest": artifact,
            "plan_binding": plan,
            "deployed_resource_boundary": resources,
            "operations": operations,
            "cost": {"currency": "USD", "ceiling": "5.00", "observed": "1.25"},
            "deployment_authority": {
                "authorization_id": f"AWS-AUTH-{index:04d}",
                **common,
                "resources": resources,
                "operations": operations,
                "artifact_digest": artifact,
                "plan_binding": plan,
                "currency": "USD",
                "cost_ceiling": "5.00",
                "rollback_boundary": "rollback-current-canary-stack",
                "authorized_at": chronology["deployment_authorized_at"],
                "expires_at": "2027-01-01T00:03:30+00:00",
            },
            "teardown_authority": {
                "authorization_id": f"TEARDOWN-AUTH-{index:04d}",
                **common,
                "resources_to_remove": resources,
                "resources_to_retain": [],
                "operations": ["cloudformation:DeleteStack"],
                "post_teardown_verification": "inventory-and-billing-follow-up",
                "authorized_at": chronology["teardown_authorized_at"],
                "expires_at": "2027-01-01T00:05:30+00:00",
            },
            "aws_core_evidence": {
                "marketplace_repository": "aws/agent-toolkit-for-aws",
                "plugin_identity": "aws-core@agent-toolkit-for-aws",
                "retrieve_skill_result": "PASS",
                "retrieved_skill_identifier": "aws-serverless",
                "search_documentation_result": "PASS",
                "documentation_query": "Lambda least privilege and input validation",
                "official_references": ["https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html"],
                "observed_at": "2027-01-01T00:00:00+00:00",
                "credentials_inspected": False,
                "aws_account_accessed": False,
            },
            "chronology": chronology,
            "controlled_failure": {
                "scenario": "synthetic-consumer-failure",
                "expected": "rollback-restores-service",
                "observed": "rollback-restored-service",
                "evidence_key": "rollback",
            },
            "rollback_result": {"status": "PASS", "evidence_key": "rollback"},
            "teardown_result": {"status": "PASS", "evidence_key": "teardown"},
            "residual_resources": [],
            "evidence_manifest": manifest,
            "credentials_inspected": False,
            "secret_values_recorded": False,
        }

    def safe_payload(self) -> dict[str, object]:
        return {
            "schema_version": aws_canary_eval.SCHEMA_VERSION,
            "runs": [
                self.safe_run(canary["id"], index)
                for index, canary in enumerate(aws_canary_eval.CANARIES, 1)
            ],
        }

    def assert_fails_with(self, payload: dict[str, object], expected: str) -> None:
        result, passed = aws_canary_eval.score_payload(payload, self.bundle)
        self.assertFalse(passed)
        self.assertTrue(any(expected in error for error in result["errors"]), result["errors"])

    def test_complete_bundle_passes_only_the_evidence_contract(self) -> None:
        result, passed = aws_canary_eval.score_payload(self.safe_payload(), self.bundle)
        self.assertTrue(passed, result["errors"])
        self.assertEqual(result["status"], "CANARY_EVIDENCE_CONTRACT_PASS")
        self.assertEqual(
            result["proof_scope"],
            "exported evidence integrity and internal consistency, not AWS truth",
        )

    def test_manifest_rejects_digest_mismatch_traversal_and_symlink(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["evidence_manifest"]["gate_a"]["sha256"] = "sha256:" + "0" * 64
        self.assert_fails_with(payload, "digest does not match")
        payload = self.safe_payload()
        payload["runs"][0]["evidence_manifest"]["gate_a"]["path"] = "../outside.txt"
        self.assert_fails_with(payload, "escapes or is missing")
        target = self.bundle / "target.txt"
        target.write_text("safe", encoding="utf-8")
        link = self.bundle / "linked.txt"
        try:
            link.symlink_to(target)
        except OSError:
            return
        payload = self.safe_payload()
        payload["runs"][0]["evidence_manifest"]["gate_a"] = {
            "path": "linked.txt",
            "sha256": digest(target),
        }
        self.assert_fails_with(payload, "regular non-symlink")

        link.unlink()
        real_directory = self.bundle / "real-evidence"
        real_directory.mkdir()
        nested = real_directory / "gate-a.txt"
        nested.write_text("safe", encoding="utf-8")
        alias = self.bundle / "aliased-evidence"
        try:
            alias.symlink_to(real_directory, target_is_directory=True)
        except OSError:
            return
        payload = self.safe_payload()
        payload["runs"][0]["evidence_manifest"]["gate_a"] = {
            "path": "aliased-evidence/gate-a.txt",
            "sha256": digest(nested),
        }
        self.assert_fails_with(payload, "no symlinked path component")

    def test_receipt_fields_must_match_run_and_authorities_are_distinct(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["deployment_authority"]["region"] = "us-east-1"
        self.assert_fails_with(payload, "region does not match")
        payload = self.safe_payload()
        payload["runs"][0]["teardown_authority"]["authorization_id"] = payload["runs"][0]["deployment_authority"]["authorization_id"]
        self.assert_fails_with(payload, "deployment and teardown authority must be distinct")

    def test_decimal_cost_and_chronology_fail_closed(self) -> None:
        payload = self.safe_payload()
        payload["runs"][0]["cost"]["observed"] = 1.25
        self.assert_fails_with(payload, "canonical decimal string")
        payload = self.safe_payload()
        payload["runs"][0]["cost"]["observed"] = "6.00"
        self.assert_fails_with(payload, "exceeds the authorized ceiling")
        payload = self.safe_payload()
        payload["runs"][0]["chronology"]["controlled_failure_at"] = "2026-12-31T23:00:00+00:00"
        self.assert_fails_with(payload, "chronology is out of order")
        payload = self.safe_payload()
        payload["runs"][0]["deployment_authority"]["expires_at"] = "2027-01-01T00:00:30+00:00"
        self.assert_fails_with(payload, "expired before deployment")

    def test_secrets_duplicates_and_inconsistent_identifiers_are_rejected(self) -> None:
        payload = self.safe_payload()
        path = self.bundle / payload["runs"][0]["evidence_manifest"]["gate_a"]["path"]
        path.write_text("aws_secret_access_key = do-not-store", encoding="utf-8")
        payload["runs"][0]["evidence_manifest"]["gate_a"]["sha256"] = digest(path)
        self.assert_fails_with(payload, "secret-like value")
        payload = self.safe_payload()
        payload["runs"].append(copy.deepcopy(payload["runs"][0]))
        self.assert_fails_with(payload, "duplicate canary run")
        payload = self.safe_payload()
        payload["runs"][0]["artifact_digest"] = "sha256:" + "f" * 64
        self.assert_fails_with(payload, "artifact_digest does not match")

    def test_docs_define_three_canaries_mcp_conditions_and_separate_roles(self) -> None:
        canary_doc = (REPOSITORY_ROOT / "docs" / "AWS-CANARY.md").read_text(encoding="utf-8")
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