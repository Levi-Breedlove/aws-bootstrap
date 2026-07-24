from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 2
PASS_STATUS = "CANARY_EVIDENCE_CONTRACT_PASS"
OFFICIAL_PLUGIN = "aws-core@agent-toolkit-for-aws"
OFFICIAL_MARKETPLACE = "aws/agent-toolkit-for-aws"
CANARIES = (
    {"id": "synchronous-managed-serverless", "summary": "Synchronous managed-serverless application."},
    {"id": "asynchronous-event-driven", "summary": "Asynchronous event-driven workflow."},
    {"id": "container-based", "summary": "Container-based application."},
)
EVIDENCE_KEYS = (
    "gate_a",
    "gate_b",
    "aws_20",
    "teardown_authority",
    "cloudtrail_export",
    "iac_plan_or_change_set",
    "smoke_tests",
    "rollback",
    "teardown",
    "billing_reports",
)
CHRONOLOGY_KEYS = (
    "deployment_authorized_at",
    "deployment_started_at",
    "controlled_failure_at",
    "rollback_completed_at",
    "teardown_authorized_at",
    "teardown_completed_at",
    "billing_observed_at",
    "follow_up_at",
)
RUN_KEYS = {
    "canary_id",
    "run_reference",
    "account",
    "region",
    "environment",
    "profile_or_role",
    "artifact_digest",
    "plan_binding",
    "deployed_resource_boundary",
    "operations",
    "cost",
    "deployment_authority",
    "teardown_authority",
    "aws_core_evidence",
    "chronology",
    "controlled_failure",
    "rollback_result",
    "teardown_result",
    "residual_resources",
    "evidence_manifest",
    "credentials_inspected",
    "secret_values_recorded",
}
DEPLOYMENT_AUTHORITY_KEYS = {
    "authorization_id",
    "account",
    "region",
    "environment",
    "profile_or_role",
    "resources",
    "operations",
    "artifact_digest",
    "plan_binding",
    "currency",
    "cost_ceiling",
    "rollback_boundary",
    "authorized_at",
    "expires_at",
}
TEARDOWN_AUTHORITY_KEYS = {
    "authorization_id",
    "account",
    "region",
    "environment",
    "profile_or_role",
    "resources_to_remove",
    "resources_to_retain",
    "operations",
    "post_teardown_verification",
    "authorized_at",
    "expires_at",
}
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
ACCOUNT_ID = re.compile(r"^[0-9]{12}$")
ACCOUNT_ALIAS = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")
REGION = re.compile(r"^[a-z]{2}(?:-[a-z0-9]+)+-[0-9]+$")
REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+=,-]{0,511}$")
OFFICIAL_REFERENCE = re.compile(r"^https://(?:docs\.aws\.amazon\.com/|aws\.amazon\.com/)[^\s]+$")
SECRET_PATTERN = re.compile(
    r"AKIA[0-9A-Z]{16}|aws_secret_access_key|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|"
    r"OPENAI_API_KEY|CODEX_API_KEY|GH_TOKEN|GITHUB_TOKEN",
    re.IGNORECASE,
)


def plan_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "OFFLINE_DISPOSABLE_AWS_CANARY_EVIDENCE_VERIFICATION",
        "canaries": list(CANARIES),
        "required_evidence_manifest_entries": list(EVIDENCE_KEYS),
        "constraints": {
            "bundle_root_required": True,
            "framework_maintenance_accesses_aws": False,
            "deployment_and_teardown_authority_are_distinct": True,
            "credentials_may_be_inspected_or_recorded": False,
            "secret_values_may_be_recorded": False,
            "proof_scope": "exported evidence integrity and internal consistency, not AWS truth",
        },
    }


def _expect_keys(value: object, expected: set[str], label: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return None
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        errors.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown fields: {', '.join(unknown)}")
    return value


def _reference(value: object) -> bool:
    return isinstance(value, str) and bool(REFERENCE.fullmatch(value))


def _bounded_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 512
        and value == value.strip()
        and not any(ord(character) < 32 for character in value)
    )


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _decimal(value: object, label: str, errors: list[str], *, positive: bool) -> Decimal | None:
    if not isinstance(value, str) or re.fullmatch(r"(?:0|[1-9]\d*)(?:\.\d{1,4})?", value) is None:
        errors.append(f"{label} must be a canonical decimal string")
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation:
        errors.append(f"{label} is invalid")
        return None
    if not amount.is_finite() or amount < 0 or (positive and amount <= 0):
        errors.append(f"{label} must be {'positive' if positive else 'non-negative'}")
        return None
    return amount


def _list(value: object, label: str, errors: list[str], *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        errors.append(f"{label} must be a {'list' if allow_empty else 'non-empty list'}")
        return []
    if any(not _reference(item) for item in value):
        errors.append(f"{label} contains an invalid value")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label} contains duplicates")
    return list(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _safe_bundle_file(bundle_root: Path, relative: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        errors.append(f"{label}.path must be a relative bundle path")
        return None
    candidate = bundle_root / relative
    current = bundle_root
    if current.is_symlink():
        errors.append(f"{label}.path must not traverse a symlinked bundle root")
        return None
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            errors.append(f"{label}.path must be a regular file with no symlinked path component")
            return None
    try:
        resolved_root = bundle_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError):
        errors.append(f"{label}.path escapes or is missing from the evidence bundle")
        return None
    if candidate.is_symlink() or not resolved.is_file():
        errors.append(f"{label}.path must be a regular non-symlink file")
        return None
    return resolved


def _validate_manifest(value: object, bundle_root: Path, label: str, errors: list[str]) -> None:
    manifest = _expect_keys(value, set(EVIDENCE_KEYS), label, errors)
    if manifest is None:
        return
    for key in EVIDENCE_KEYS:
        entry = _expect_keys(manifest.get(key), {"path", "sha256"}, f"{label}.{key}", errors)
        if entry is None:
            continue
        declared = entry.get("sha256")
        if not isinstance(declared, str) or DIGEST.fullmatch(declared) is None:
            errors.append(f"{label}.{key}.sha256 must be a SHA-256 digest")
            continue
        path = _safe_bundle_file(bundle_root, entry.get("path"), f"{label}.{key}", errors)
        if path is None:
            continue
        if _sha256(path) != declared:
            errors.append(f"{label}.{key} digest does not match the exported file")
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            errors.append(f"{label}.{key} cannot be read: {exc}")
            continue
        if SECRET_PATTERN.search(content):
            errors.append(f"{label}.{key} contains a secret-like value")


def _validate_plan(value: object, label: str, errors: list[str]) -> dict[str, str] | None:
    plan = _expect_keys(value, {"type", "identifier", "digest"}, label, errors)
    if plan is None:
        return None
    if plan.get("type") not in {"CLOUDFORMATION_CHANGE_SET", "TERRAFORM_PLAN", "CONTAINER_IMAGE", "OTHER"}:
        errors.append(f"{label}.type is invalid")
    if not _reference(plan.get("identifier")):
        errors.append(f"{label}.identifier is invalid")
    if not isinstance(plan.get("digest"), str) or DIGEST.fullmatch(plan["digest"]) is None:
        errors.append(f"{label}.digest must be a SHA-256")
    return {key: str(plan.get(key, "")) for key in ("type", "identifier", "digest")}


def _match_authority_common(
    authority: Mapping[str, Any],
    run: Mapping[str, Any],
    label: str,
    errors: list[str],
) -> None:
    for key in ("account", "region", "environment", "profile_or_role"):
        if authority.get(key) != run.get(key):
            errors.append(f"{label}.{key} does not match the canary run")


def _validate_deployment_authority(value: object, run: Mapping[str, Any], label: str, errors: list[str]) -> tuple[datetime | None, datetime | None]:
    item = _expect_keys(value, DEPLOYMENT_AUTHORITY_KEYS, label, errors)
    if item is None:
        return None, None
    if not isinstance(item.get("authorization_id"), str) or re.fullmatch(r"AWS-AUTH-\d{4,}", item["authorization_id"]) is None:
        errors.append(f"{label}.authorization_id is invalid")
    _match_authority_common(item, run, label, errors)
    if item.get("resources") != run.get("deployed_resource_boundary"):
        errors.append(f"{label}.resources do not match the deployed boundary")
    if item.get("operations") != run.get("operations"):
        errors.append(f"{label}.operations do not match the canary run")
    if item.get("artifact_digest") != run.get("artifact_digest"):
        errors.append(f"{label}.artifact_digest does not match the canary run")
    if item.get("plan_binding") != run.get("plan_binding"):
        errors.append(f"{label}.plan_binding does not match the canary run")
    cost = run.get("cost") if isinstance(run.get("cost"), Mapping) else {}
    if item.get("currency") != cost.get("currency") or item.get("cost_ceiling") != cost.get("ceiling"):
        errors.append(f"{label} cost ceiling does not match the canary run")
    if not _reference(item.get("rollback_boundary")):
        errors.append(f"{label}.rollback_boundary is required")
    authorized = _timestamp(item.get("authorized_at"))
    expires = _timestamp(item.get("expires_at"))
    if authorized is None or expires is None or authorized >= expires:
        errors.append(f"{label} authorization timestamps are invalid")
    return authorized, expires


def _validate_teardown_authority(value: object, run: Mapping[str, Any], label: str, errors: list[str]) -> tuple[datetime | None, datetime | None]:
    item = _expect_keys(value, TEARDOWN_AUTHORITY_KEYS, label, errors)
    if item is None:
        return None, None
    if not isinstance(item.get("authorization_id"), str) or re.fullmatch(r"TEARDOWN-AUTH-\d{4,}", item["authorization_id"]) is None:
        errors.append(f"{label}.authorization_id is invalid")
    _match_authority_common(item, run, label, errors)
    if item.get("resources_to_remove") != run.get("deployed_resource_boundary"):
        errors.append(f"{label}.resources_to_remove do not match the deployed boundary")
    _list(item.get("resources_to_retain"), f"{label}.resources_to_retain", errors, allow_empty=True)
    _list(item.get("operations"), f"{label}.operations", errors)
    if not _reference(item.get("post_teardown_verification")):
        errors.append(f"{label}.post_teardown_verification is required")
    authorized = _timestamp(item.get("authorized_at"))
    expires = _timestamp(item.get("expires_at"))
    if authorized is None or expires is None or authorized >= expires:
        errors.append(f"{label} authorization timestamps are invalid")
    return authorized, expires


def _validate_aws_core(value: object, label: str, errors: list[str]) -> None:
    keys = {
        "marketplace_repository", "plugin_identity", "retrieve_skill_result",
        "retrieved_skill_identifier", "search_documentation_result",
        "documentation_query", "official_references", "observed_at",
        "credentials_inspected", "aws_account_accessed",
    }
    item = _expect_keys(value, keys, label, errors)
    if item is None:
        return
    if item.get("marketplace_repository") != OFFICIAL_MARKETPLACE or item.get("plugin_identity") != OFFICIAL_PLUGIN:
        errors.append(f"{label} must identify official AWS Core")
    if item.get("retrieve_skill_result") != "PASS" or not _reference(item.get("retrieved_skill_identifier")):
        errors.append(f"{label}.retrieve_skill must pass with an identifier")
    references = item.get("official_references")
    if item.get("search_documentation_result") != "PASS" or not _bounded_text(item.get("documentation_query")):
        errors.append(f"{label}.search_documentation must pass with an exact query")
    if not isinstance(references, list) or not references or any(not isinstance(reference, str) or OFFICIAL_REFERENCE.fullmatch(reference) is None for reference in references):
        errors.append(f"{label}.official_references must contain official AWS URLs")
    if _timestamp(item.get("observed_at")) is None:
        errors.append(f"{label}.observed_at is invalid")
    if item.get("credentials_inspected") is not False or item.get("aws_account_accessed") is not False:
        errors.append(f"{label} must be unauthenticated documentation evidence")


def _validate_result(value: object, label: str, errors: list[str]) -> None:
    item = _expect_keys(value, {"status", "evidence_key"}, label, errors)
    if item is None:
        return
    if item.get("status") != "PASS" or item.get("evidence_key") not in EVIDENCE_KEYS:
        errors.append(f"{label} must be PASS and reference one manifest evidence key")


def _validate_run(run: object, index: int, bundle_root: Path, errors: list[str]) -> str | None:
    label = f"runs[{index}]"
    item = _expect_keys(run, RUN_KEYS, label, errors)
    if item is None:
        return None
    canary_id = item.get("canary_id")
    if canary_id not in {canary["id"] for canary in CANARIES}:
        errors.append(f"{label}.canary_id is unknown")
        return None
    if not _reference(item.get("run_reference")):
        errors.append(f"{label}.run_reference is invalid")
    if item.get("credentials_inspected") is not False or item.get("secret_values_recorded") is not False:
        errors.append(f"{label} must not inspect credentials or record secrets")
    account = item.get("account")
    if not isinstance(account, str) or not (ACCOUNT_ID.fullmatch(account) or ACCOUNT_ALIAS.fullmatch(account)):
        errors.append(f"{label}.account must be a 12-digit ID or exact alias")
    if not isinstance(item.get("region"), str) or REGION.fullmatch(item["region"]) is None:
        errors.append(f"{label}.region must be an exact AWS Region")
    for key in ("environment", "profile_or_role"):
        if not _reference(item.get(key)):
            errors.append(f"{label}.{key} is invalid")
    if not isinstance(item.get("artifact_digest"), str) or DIGEST.fullmatch(item["artifact_digest"]) is None:
        errors.append(f"{label}.artifact_digest must be a SHA-256")
    _validate_plan(item.get("plan_binding"), f"{label}.plan_binding", errors)
    _list(item.get("deployed_resource_boundary"), f"{label}.deployed_resource_boundary", errors)
    _list(item.get("operations"), f"{label}.operations", errors)

    cost = _expect_keys(item.get("cost"), {"currency", "ceiling", "observed"}, f"{label}.cost", errors)
    if cost is not None:
        if not isinstance(cost.get("currency"), str) or re.fullmatch(r"[A-Z]{3}", cost["currency"]) is None:
            errors.append(f"{label}.cost.currency must be an ISO currency")
        ceiling = _decimal(cost.get("ceiling"), f"{label}.cost.ceiling", errors, positive=True)
        observed = _decimal(cost.get("observed"), f"{label}.cost.observed", errors, positive=False)
        if ceiling is not None and observed is not None and observed > ceiling:
            errors.append(f"{label}.cost.observed exceeds the authorized ceiling")

    deployment_authorized, deployment_expires = _validate_deployment_authority(
        item.get("deployment_authority"), item, f"{label}.deployment_authority", errors
    )
    teardown_authorized, teardown_expires = _validate_teardown_authority(
        item.get("teardown_authority"), item, f"{label}.teardown_authority", errors
    )
    deployment = item.get("deployment_authority") if isinstance(item.get("deployment_authority"), Mapping) else {}
    teardown = item.get("teardown_authority") if isinstance(item.get("teardown_authority"), Mapping) else {}
    if deployment.get("authorization_id") == teardown.get("authorization_id"):
        errors.append(f"{label} deployment and teardown authority must be distinct")

    _validate_aws_core(item.get("aws_core_evidence"), f"{label}.aws_core_evidence", errors)
    _validate_result(item.get("rollback_result"), f"{label}.rollback_result", errors)
    _validate_result(item.get("teardown_result"), f"{label}.teardown_result", errors)
    failure = _expect_keys(item.get("controlled_failure"), {"scenario", "expected", "observed", "evidence_key"}, f"{label}.controlled_failure", errors)
    if failure is not None:
        for key in ("scenario", "expected", "observed"):
            if not _reference(failure.get(key)):
                errors.append(f"{label}.controlled_failure.{key} is invalid")
        if failure.get("evidence_key") not in EVIDENCE_KEYS:
            errors.append(f"{label}.controlled_failure.evidence_key is invalid")
    residual = item.get("residual_resources")
    if not isinstance(residual, list):
        errors.append(f"{label}.residual_resources must be a list")
    elif any(not _reference(value) for value in residual):
        errors.append(f"{label}.residual_resources contains an invalid value")

    chronology = _expect_keys(item.get("chronology"), set(CHRONOLOGY_KEYS), f"{label}.chronology", errors)
    times: dict[str, datetime] = {}
    if chronology is not None:
        for key in CHRONOLOGY_KEYS:
            parsed = _timestamp(chronology.get(key))
            if parsed is None:
                errors.append(f"{label}.chronology.{key} is invalid")
            else:
                times[key] = parsed
        if len(times) == len(CHRONOLOGY_KEYS):
            ordered = [times[key] for key in CHRONOLOGY_KEYS]
            if any(left > right for left, right in zip(ordered, ordered[1:])):
                errors.append(f"{label}.chronology is out of order")
            if deployment_authorized != times["deployment_authorized_at"] or teardown_authorized != times["teardown_authorized_at"]:
                errors.append(f"{label}.chronology does not match authority timestamps")
            if deployment_expires is not None and times["deployment_started_at"] > deployment_expires:
                errors.append(f"{label} deployment authority was expired before deployment")
            if teardown_expires is not None and times["teardown_completed_at"] > teardown_expires:
                errors.append(f"{label} teardown authority expired before teardown completed")
    _validate_manifest(item.get("evidence_manifest"), bundle_root, f"{label}.evidence_manifest", errors)
    return str(canary_id)


def score_payload(payload: object, bundle_root: Path) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    try:
        resolved_root = bundle_root.resolve(strict=True)
    except OSError:
        resolved_root = bundle_root
        errors.append("bundle_root must be an existing directory")
    if not resolved_root.is_dir():
        errors.append("bundle_root must be an existing directory")
    root = _expect_keys(payload, {"schema_version", "runs"}, "payload", errors)
    runs: object = []
    if root is not None:
        if root.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"payload.schema_version must be {SCHEMA_VERSION}")
        runs = root.get("runs")
    if not isinstance(runs, list):
        errors.append("payload.runs must be a list")
        runs = []
    identities: list[tuple[str, str]] = []
    observed: list[str] = []
    for index, run in enumerate(runs):
        canary_id = _validate_run(run, index, resolved_root, errors)
        if canary_id is not None and isinstance(run, dict):
            observed.append(canary_id)
            identities.append((canary_id, str(run.get("run_reference", ""))))
    for identity, count in Counter(identities).items():
        if count != 1:
            errors.append(f"duplicate canary run: {identity[0]} / {identity[1]}")
    counts = Counter(observed)
    for canary in CANARIES:
        if counts[canary["id"]] != 1:
            errors.append(f"{canary['id']} requires exactly one observed run")
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": PASS_STATUS if not errors else "CANARY_EVIDENCE_CONTRACT_FAIL",
        "proof_scope": "exported evidence integrity and internal consistency, not AWS truth",
        "canary_runs": dict(sorted(counts.items())),
        "errors": errors,
    }
    return result, not errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or verify offline Fastlane AWS canary evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--json", action="store_true", required=True)
    score = subparsers.add_parser("score")
    score.add_argument("--input", required=True, type=Path)
    score.add_argument("--bundle-root", required=True, type=Path)
    score.add_argument("--json", action="store_true", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        print(json.dumps(plan_payload(), indent=2, sort_keys=True))
        return 0
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "status": "CANARY_EVIDENCE_CONTRACT_FAIL", "errors": [str(exc)]}, indent=2, sort_keys=True))
        return 2
    result, passed = score_payload(payload, args.bundle_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())