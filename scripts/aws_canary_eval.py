from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


SCHEMA_VERSION = 1
OFFICIAL_PLUGIN = "aws-core@agent-toolkit-for-aws"
OFFICIAL_MARKETPLACE = "aws/agent-toolkit-for-aws"
CANARIES = (
    {
        "id": "synchronous-managed-serverless",
        "summary": (
            "A synchronous managed-serverless request path with an API, "
            "stateless compute, managed data, and observable failures."
        ),
    },
    {
        "id": "asynchronous-event-driven",
        "summary": (
            "An asynchronous event-driven workflow with durable messaging, "
            "idempotent consumers, retries, and a controlled failure."
        ),
    },
    {
        "id": "container-based",
        "summary": (
            "A container-based application with an immutable image, managed "
            "orchestration, health checks, rollback, and bounded networking."
        ),
    },
)
REQUIRED_STEPS = (
    "synthetic_owner_intake",
    "gate_a",
    "aws_core_grounded_design",
    "candidate_comparison",
    "gate_b",
    "local_build",
    "iac_validation",
    "aws_10_read_only_preflight",
    "aws_20_deployment_authority",
    "deployment",
    "smoke_tests",
    "controlled_failure",
    "rollback",
    "aws_30_deployment_evidence",
    "teardown_review",
    "teardown_authority",
    "teardown",
    "residual_resource_check",
    "billing_check",
)
PLAN_TYPES = {
    "CLOUDFORMATION_CHANGE_SET",
    "TERRAFORM_PLAN",
    "CONTAINER_IMAGE",
    "OTHER",
}
RUN_KEYS = {
    "canary_id",
    "run_reference",
    "observed_live_run",
    "aws_account_accessed",
    "credentials_inspected",
    "secret_values_recorded",
    "account",
    "region",
    "environment",
    "profile_or_role",
    "artifact_digest",
    "plan_binding",
    "deployed_resource_boundary",
    "action_receipts",
    "cost",
    "aws_core_evidence",
    "cloudtrail_evidence_reference",
    "controlled_failure",
    "rollback_result",
    "teardown_result",
    "residual_resources",
    "billing_check",
    "steps",
}
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
ACCOUNT_ID = re.compile(r"^[0-9]{12}$")
ACCOUNT_ALIAS = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")
REGION = re.compile(r"^[a-z]{2}(?:-[a-z0-9]+)+-[0-9]+$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+=,-]{0,511}$")
ENVIRONMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
OFFICIAL_REFERENCE = re.compile(
    r"^https://(?:docs\.aws\.amazon\.com/|aws\.amazon\.com/)[^\s]+$"
)


def plan_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "DISPOSABLE_AWS_CANARY_FIELD_VALIDATION",
        "canaries": [
            {**canary, "required_steps": list(REQUIRED_STEPS)}
            for canary in CANARIES
        ],
        "required_run_fields": sorted(RUN_KEYS),
        "constraints": {
            "framework_maintenance_accesses_aws": False,
            "live_execution_requires_exact_deployment_authority": True,
            "teardown_requires_separate_exact_authority": True,
            "credentials_may_be_inspected_or_recorded": False,
            "secret_values_may_be_recorded": False,
            "all_three_canaries_required_for_program_pass": True,
        },
    }


def _expect_keys(
    value: object,
    expected: set[str],
    label: str,
    errors: list[str],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return None
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown fields: {', '.join(unknown)}")
    return value


def _is_reference(value: object) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 512
        and value.strip() == value
        and not any(ord(character) < 32 for character in value)
    )


def _is_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validate_result(
    value: object,
    label: str,
    errors: list[str],
) -> None:
    result = _expect_keys(value, {"status", "evidence_reference"}, label, errors)
    if result is None:
        return
    if result.get("status") != "PASS":
        errors.append(f"{label}.status must be PASS")
    if not _is_reference(result.get("evidence_reference")):
        errors.append(f"{label}.evidence_reference is required")


def _validate_run(run: object, index: int, errors: list[str]) -> str | None:
    label = f"runs[{index}]"
    item = _expect_keys(run, RUN_KEYS, label, errors)
    if item is None:
        return None

    canary_id = item.get("canary_id")
    if canary_id not in {canary["id"] for canary in CANARIES}:
        errors.append(f"{label}.canary_id is unknown")
        canary_id = None
    if not _is_reference(item.get("run_reference")):
        errors.append(f"{label}.run_reference is required")
    if item.get("observed_live_run") is not True:
        errors.append(f"{label}.observed_live_run must be true")
    if item.get("aws_account_accessed") is not True:
        errors.append(f"{label}.aws_account_accessed must be true for a live canary")
    if item.get("credentials_inspected") is not False:
        errors.append(f"{label}.credentials_inspected must be false")
    if item.get("secret_values_recorded") is not False:
        errors.append(f"{label}.secret_values_recorded must be false")

    account = item.get("account")
    if not isinstance(account, str) or not (
        ACCOUNT_ID.fullmatch(account) or ACCOUNT_ALIAS.fullmatch(account)
    ):
        errors.append(f"{label}.account must be a 12-digit ID or exact alias")
    if not isinstance(item.get("region"), str) or not REGION.fullmatch(
        item["region"]
    ):
        errors.append(f"{label}.region must be an exact AWS Region")
    if not isinstance(item.get("environment"), str) or not ENVIRONMENT.fullmatch(
        item["environment"]
    ):
        errors.append(f"{label}.environment is invalid")
    if not _is_reference(item.get("profile_or_role")):
        errors.append(f"{label}.profile_or_role is required")
    if not isinstance(item.get("artifact_digest"), str) or not DIGEST.fullmatch(
        item["artifact_digest"]
    ):
        errors.append(f"{label}.artifact_digest must be an immutable SHA-256")

    plan = _expect_keys(
        item.get("plan_binding"),
        {"type", "identifier", "digest"},
        f"{label}.plan_binding",
        errors,
    )
    if plan is not None:
        if plan.get("type") not in PLAN_TYPES:
            errors.append(f"{label}.plan_binding.type is invalid")
        if not isinstance(plan.get("identifier"), str) or not IDENTIFIER.fullmatch(
            plan["identifier"]
        ):
            errors.append(f"{label}.plan_binding.identifier is invalid")
        if not isinstance(plan.get("digest"), str) or not DIGEST.fullmatch(
            plan["digest"]
        ):
            errors.append(f"{label}.plan_binding.digest must be a SHA-256")

    boundary = item.get("deployed_resource_boundary")
    if not isinstance(boundary, list) or not boundary:
        errors.append(f"{label}.deployed_resource_boundary must be a non-empty list")
    elif any(not _is_reference(resource) for resource in boundary):
        errors.append(f"{label}.deployed_resource_boundary contains an invalid value")

    receipts = _expect_keys(
        item.get("action_receipts"),
        {"gate_a", "gate_b", "deployment", "teardown"},
        f"{label}.action_receipts",
        errors,
    )
    if receipts is not None:
        for receipt in ("gate_a", "gate_b", "deployment", "teardown"):
            if not _is_reference(receipts.get(receipt)):
                errors.append(f"{label}.action_receipts.{receipt} is required")

    cost = _expect_keys(
        item.get("cost"),
        {"currency", "ceiling", "observed", "period_start", "period_end"},
        f"{label}.cost",
        errors,
    )
    currency: str | None = None
    ceiling: float | None = None
    observed: float | None = None
    if cost is not None:
        currency_value = cost.get("currency")
        if not isinstance(currency_value, str) or not re.fullmatch(
            r"[A-Z]{3}", currency_value
        ):
            errors.append(f"{label}.cost.currency must be an ISO currency")
        else:
            currency = currency_value
        if not _is_number(cost.get("ceiling")) or float(cost["ceiling"]) <= 0:
            errors.append(f"{label}.cost.ceiling must be finite and positive")
        else:
            ceiling = float(cost["ceiling"])
        if not _is_number(cost.get("observed")) or float(cost["observed"]) < 0:
            errors.append(f"{label}.cost.observed must be finite and non-negative")
        else:
            observed = float(cost["observed"])
        if ceiling is not None and observed is not None and observed > ceiling:
            errors.append(f"{label}.cost.observed exceeds the authorized ceiling")
        if not _is_timestamp(cost.get("period_start")):
            errors.append(f"{label}.cost.period_start must include a timezone")
        if not _is_timestamp(cost.get("period_end")):
            errors.append(f"{label}.cost.period_end must include a timezone")

    aws_core = _expect_keys(
        item.get("aws_core_evidence"),
        {
            "marketplace_repository",
            "plugin_identity",
            "retrieve_skill_result",
            "retrieved_skill_identifier",
            "search_documentation_result",
            "documentation_query",
            "official_references",
            "observed_at",
            "credentials_inspected",
            "aws_account_accessed",
        },
        f"{label}.aws_core_evidence",
        errors,
    )
    if aws_core is not None:
        if aws_core.get("marketplace_repository") != OFFICIAL_MARKETPLACE:
            errors.append(f"{label}.aws_core_evidence marketplace is not official")
        if aws_core.get("plugin_identity") != OFFICIAL_PLUGIN:
            errors.append(f"{label}.aws_core_evidence plugin is not official")
        if aws_core.get("retrieve_skill_result") != "PASS":
            errors.append(f"{label}.aws_core_evidence.retrieve_skill_result must be PASS")
        if not _is_reference(aws_core.get("retrieved_skill_identifier")):
            errors.append(
                f"{label}.aws_core_evidence.retrieved_skill_identifier is required"
            )
        if aws_core.get("search_documentation_result") != "PASS":
            errors.append(
                f"{label}.aws_core_evidence.search_documentation_result must be PASS"
            )
        if not _is_reference(aws_core.get("documentation_query")):
            errors.append(f"{label}.aws_core_evidence.documentation_query is required")
        references = aws_core.get("official_references")
        if not isinstance(references, list) or not references:
            errors.append(f"{label}.aws_core_evidence.official_references is required")
        elif any(
            not isinstance(reference, str)
            or not OFFICIAL_REFERENCE.fullmatch(reference)
            for reference in references
        ):
            errors.append(
                f"{label}.aws_core_evidence.official_references must be official AWS URLs"
            )
        if not _is_timestamp(aws_core.get("observed_at")):
            errors.append(f"{label}.aws_core_evidence.observed_at is invalid")
        if aws_core.get("credentials_inspected") is not False:
            errors.append(
                f"{label}.aws_core_evidence.credentials_inspected must be false"
            )
        if aws_core.get("aws_account_accessed") is not False:
            errors.append(
                f"{label}.aws_core_evidence.aws_account_accessed must be false"
            )

    if not _is_reference(item.get("cloudtrail_evidence_reference")):
        errors.append(f"{label}.cloudtrail_evidence_reference is required")

    failure = _expect_keys(
        item.get("controlled_failure"),
        {"scenario", "expected_behavior", "observed_behavior", "evidence_reference"},
        f"{label}.controlled_failure",
        errors,
    )
    if failure is not None:
        for field in (
            "scenario",
            "expected_behavior",
            "observed_behavior",
            "evidence_reference",
        ):
            if not _is_reference(failure.get(field)):
                errors.append(f"{label}.controlled_failure.{field} is required")

    _validate_result(item.get("rollback_result"), f"{label}.rollback_result", errors)
    _validate_result(item.get("teardown_result"), f"{label}.teardown_result", errors)

    residual = item.get("residual_resources")
    if not isinstance(residual, list):
        errors.append(f"{label}.residual_resources must be a list")
    else:
        for residual_index, resource in enumerate(residual):
            resource_label = f"{label}.residual_resources[{residual_index}]"
            record = _expect_keys(
                resource,
                {"identifier", "status", "reason", "billing_dimension"},
                resource_label,
                errors,
            )
            if record is None:
                continue
            if not _is_reference(record.get("identifier")):
                errors.append(f"{resource_label}.identifier is required")
            if record.get("status") != "AUTHORIZED_RETAINED":
                errors.append(f"{resource_label}.status must be AUTHORIZED_RETAINED")
            if not _is_reference(record.get("reason")):
                errors.append(f"{resource_label}.reason is required")
            if not _is_reference(record.get("billing_dimension")):
                errors.append(f"{resource_label}.billing_dimension is required")

    billing = _expect_keys(
        item.get("billing_check"),
        {"currency", "observed_amount", "observed_at", "follow_up_at", "reference"},
        f"{label}.billing_check",
        errors,
    )
    if billing is not None:
        if currency is not None and billing.get("currency") != currency:
            errors.append(f"{label}.billing_check.currency must match cost.currency")
        if not _is_number(billing.get("observed_amount")) or float(
            billing["observed_amount"]
        ) < 0:
            errors.append(
                f"{label}.billing_check.observed_amount must be finite and non-negative"
            )
        elif observed is not None and float(billing["observed_amount"]) != observed:
            errors.append(
                f"{label}.billing_check.observed_amount must match cost.observed"
            )
        if not _is_timestamp(billing.get("observed_at")):
            errors.append(f"{label}.billing_check.observed_at is invalid")
        if not _is_timestamp(billing.get("follow_up_at")):
            errors.append(f"{label}.billing_check.follow_up_at is invalid")
        if not _is_reference(billing.get("reference")):
            errors.append(f"{label}.billing_check.reference is required")

    steps = _expect_keys(
        item.get("steps"), set(REQUIRED_STEPS), f"{label}.steps", errors
    )
    if steps is not None:
        for step in REQUIRED_STEPS:
            _validate_result(steps.get(step), f"{label}.steps.{step}", errors)

    return canary_id if isinstance(canary_id, str) else None


def score_payload(payload: object) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    root = _expect_keys(payload, {"schema_version", "runs"}, "payload", errors)
    runs: object = None
    if root is not None:
        if root.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"payload.schema_version must be {SCHEMA_VERSION}")
        runs = root.get("runs")
    if not isinstance(runs, list):
        errors.append("payload.runs must be a list")
        runs = []

    observed_ids = [
        canary_id
        for index, run in enumerate(runs)
        if (canary_id := _validate_run(run, index, errors)) is not None
    ]
    counts = Counter(observed_ids)
    expected_ids = {canary["id"] for canary in CANARIES}
    for canary_id in sorted(expected_ids):
        if counts[canary_id] != 1:
            errors.append(f"{canary_id} requires exactly one observed run")

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "canary_runs": dict(sorted(counts.items())),
        "errors": errors,
    }
    return result, not errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or score disposable Fastlane AWS canary evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="Print the canary contract.")
    plan.add_argument("--json", action="store_true", required=True)
    score = subparsers.add_parser("score", help="Score an observed result set.")
    score.add_argument("--input", required=True, type=Path)
    score.add_argument("--json", action="store_true", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        print(json.dumps(plan_payload(), indent=2, sort_keys=True))
        return 0
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "errors": [str(error)],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    result, passed = score_payload(payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
