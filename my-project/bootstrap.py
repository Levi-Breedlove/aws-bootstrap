#!/usr/bin/env python3
"""Install the Fastlane template without overwriting unreviewed user files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Sequence

PLACEHOLDERS = {
    "My AWS Project": "AWS Codex Project",
    "{{AWS_REGION}}": "us-west-2",
    "{{MONTHLY_BUDGET}}": "$50/month",
}

SKIP_NAMES = {".git", "__pycache__"}
SKIP_SUFFIXES = {".zip", ".pyc"}
SKIP_NAMES_CASEFOLD = {name.casefold() for name in SKIP_NAMES}
NO_RENDER_PATHS = {
    "bootstrap.py",
    "bootstrap.manifest.json",
    "scripts/bootstrap_doctor.py",
    "scripts/task_waves.py",
}
CORE_CONTROL_PATHS = {
    "AGENTS.md",
    "PRD.md",
    "RUNBOOK.md",
    "TASKS.md",
    "VERIFY.md",
    "bootstrap.manifest.json",
    "bootstrap.py",
    "bootstrap.yaml",
    "prompts/CODEX-PROMPTS.md",
    "scripts/bootstrap_doctor.py",
    "scripts/task_waves.py",
}
ADOPTION_ACTIONS = {"PRESERVE", "ADOPT_TEMPLATE", "STAGE_FOR_MERGE"}
RUNTIME_CONTROL_PATHS = {
    "bootstrap.py",
    "scripts/bootstrap_doctor.py",
    "scripts/task_waves.py",
}
RFC3339_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)
NON_HUMAN_IDENTITY_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:codex|agent|automation|system|bot|model|ai|assistant|"
    r"service|todo|tbd|tbc|unknown|pending|unassigned)(?![A-Za-z0-9])",
    re.IGNORECASE,
)


@dataclass
class CopyReport:
    """Summary of a preflighted template installation."""

    planned: int = 0
    written: int = 0
    unchanged: int = 0
    collisions: int = 0
    unresolved: int = 0
    preserved: int = 0
    adopted: int = 0
    staged: int = 0
    partial_adoption: bool = False


@dataclass(frozen=True)
class CopyOperation:
    """One operation that is safe to apply after the complete preflight."""

    relative: str
    source: Path
    destination: Path
    content: bytes | None
    action: str
    expected_destination_sha256: str | None = None


@dataclass(frozen=True)
class AdoptionDecision:
    """A hash-bound decision for one existing, non-identical target file."""

    path: str
    action: str
    expected_target_sha256: str
    expected_template_sha256: str


@dataclass(frozen=True)
class AdoptionPlan:
    """Reviewed decisions bound to exact source and target roots."""

    source_root: Path
    target_root: Path
    decisions: dict[str, AdoptionDecision] = field(default_factory=dict)
    authorized_by: str | None = None
    authorized_at: str | None = None
    authorization_source: str | None = None
    plan_sha256: str | None = None


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_adoption_plan_sha256(
    source_root: Path,
    target_root: Path,
    decisions: object,
) -> str:
    """Bind an authorization receipt to both roots and the ordered decisions."""

    return sha256_bytes(
        json.dumps(
            {
                "schema_version": 1,
                "source_root": str(source_root.resolve()),
                "target_root": str(target_root.resolve()),
                "decisions": decisions,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def adoption_decision_payload(decisions: dict[str, AdoptionDecision]) -> list[dict[str, str]]:
    """Return the canonical ordered JSON representation of parsed decisions."""

    return [
        {
            "path": decision.path,
            "action": decision.action,
            "expected_target_sha256": decision.expected_target_sha256,
            "expected_template_sha256": decision.expected_template_sha256,
        }
        for decision in decisions.values()
    ]


def validate_rfc3339(value: object, field_name: str) -> str:
    """Return a strict, timezone-qualified RFC 3339 timestamp."""

    if not isinstance(value, str) or RFC3339_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} requires an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} requires an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} timestamp must include a timezone")
    return value


def validate_human_identity(value: object, field_name: str) -> str:
    """Reject unresolved, synthetic, or automation identities at a human gate."""

    if not isinstance(value, str):
        raise ValueError(f"{field_name} requires a named human owner")
    normalized = value.strip()
    if (
        not normalized
        or any(character in normalized for character in "\r\n<>")
        or NON_HUMAN_IDENTITY_PATTERN.search(normalized) is not None
    ):
        raise ValueError(f"{field_name} requires a named human owner")
    return normalized


def validate_adoption_authority(plan: AdoptionPlan) -> None:
    """Validate the complete programmatic plan and any destructive authority."""

    if not isinstance(plan.source_root, Path) or not isinstance(plan.target_root, Path):
        raise ValueError("Adoption plan roots must be Path objects")
    if not isinstance(plan.decisions, dict):
        raise ValueError("Adoption plan decisions must be a path-keyed object")
    for key, decision in plan.decisions.items():
        relative = validate_relative_path(key)
        if not isinstance(decision, AdoptionDecision):
            raise ValueError(f"{relative}: invalid programmatic adoption decision")
        if decision.path != relative:
            raise ValueError(
                f"{relative}: decision path does not match its lookup key"
            )
        if decision.action not in ADOPTION_ACTIONS:
            raise ValueError(f"{relative}: invalid adoption action {decision.action!r}")
        validate_digest(
            decision.expected_target_sha256,
            "expected_target_sha256",
            relative,
        )
        validate_digest(
            decision.expected_template_sha256,
            "expected_template_sha256",
            relative,
        )

    if not any(
        decision.action == "ADOPT_TEMPLATE" for decision in plan.decisions.values()
    ):
        return
    validate_human_identity(plan.authorized_by, "Adoption authorization")
    if plan.authorization_source != "OWNER_CONFIRMATION":
        raise ValueError("Adoption authorization_source must be OWNER_CONFIRMATION")
    validate_rfc3339(plan.authorized_at, "Adoption authorization")
    expected = canonical_adoption_plan_sha256(
        plan.source_root,
        plan.target_root,
        adoption_decision_payload(plan.decisions),
    )
    if plan.plan_sha256 != expected:
        raise ValueError("Adoption authorization does not match the complete plan")


def is_text_file(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def render_text(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(key, value)
    return text


def paths_overlap(first: Path, second: Path) -> bool:
    first = first.resolve()
    second = second.resolve()
    return first == second or first in second.parents or second in first.parents


def validate_non_overlapping_paths(source: Path, target: Path) -> None:
    """Reject overlapping source and target trees before creating anything."""

    source = source.resolve()
    target = target.resolve()
    if not source.is_dir():
        raise ValueError(f"Template source is not a directory: {source}")
    filesystem_root = Path(target.anchor).resolve()
    if target in {filesystem_root, Path.home().resolve()}:
        raise ValueError(f"Target must not be a filesystem root or home directory: {target}")
    if any(part.casefold() == ".git" for part in target.parts):
        raise ValueError(f"Target must not be inside Git metadata: {target}")
    if paths_overlap(source, target):
        raise ValueError(
            "Source and target directories must not overlap: "
            f"source={source}, target={target}"
        )
    if target.exists() and not target.is_dir():
        raise ValueError(f"Target exists and is not a directory: {target}")


def validate_relative_path(raw: str) -> str:
    """Return one canonical repository-relative POSIX path or fail closed."""

    if (
        not isinstance(raw, str)
        or not raw
        or raw == "."
        or "\\" in raw
        or any(character in raw for character in "*?[]{}")
    ):
        raise ValueError(f"Invalid adoption path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(
        part in {"", ".", ".."} or part.casefold() == ".git"
        for part in path.parts
    ):
        raise ValueError(f"Invalid adoption path: {raw!r}")
    canonical = path.as_posix()
    if canonical != raw:
        raise ValueError(f"Adoption path is not canonical: {raw!r}")
    return canonical


def validate_digest(value: object, field_name: str, path: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{path}: invalid {field_name}")
    return value


def validate_template_control_hashes(source: Path) -> None:
    """Verify trusted runtime bytes before an installer tells users to run them."""

    manifest_path = source / "bootstrap.manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to verify template control hashes: {exc}") from exc
    controls = manifest.get("control_sha256") if isinstance(manifest, dict) else None
    if not isinstance(controls, dict) or set(controls) != RUNTIME_CONTROL_PATHS:
        raise ValueError(
            "bootstrap.manifest.json control_sha256 must name the exact runtime controls"
        )
    for relative in sorted(RUNTIME_CONTROL_PATHS):
        expected = validate_digest(controls[relative], "control_sha256", relative)
        path = source / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Runtime control is missing or unsafe: {relative}")
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise ValueError(f"Runtime control hash mismatch: {relative}")


def load_adoption_plan(path: Path, source: Path, target: Path) -> AdoptionPlan:
    """Load a strict, duplicate-free, hash-bound brownfield adoption plan."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read adoption map {path}: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Adoption map must be an object with schema_version 1")
    expected_keys = {
        "schema_version",
        "source_root",
        "target_root",
        "decisions",
        "authorization",
    }
    if set(payload) != expected_keys:
        raise ValueError(
            "Adoption map fields must be exactly: " + ", ".join(sorted(expected_keys))
        )

    source_root = Path(str(payload["source_root"])).expanduser().resolve()
    target_root = Path(str(payload["target_root"])).expanduser().resolve()
    if source_root != source.resolve() or target_root != target.resolve():
        raise ValueError("Adoption map source_root or target_root does not match this run")

    raw_decisions = payload["decisions"]
    if not isinstance(raw_decisions, list):
        raise ValueError("Adoption map decisions must be a list")

    decisions: dict[str, AdoptionDecision] = {}
    for item in raw_decisions:
        if not isinstance(item, dict) or set(item) != {
            "path",
            "action",
            "expected_target_sha256",
            "expected_template_sha256",
        }:
            raise ValueError("Every adoption decision must contain exactly four fields")
        relative = validate_relative_path(item["path"])
        if relative in decisions:
            raise ValueError(f"Duplicate adoption decision: {relative}")
        action = item["action"]
        if action not in ADOPTION_ACTIONS:
            raise ValueError(f"{relative}: invalid adoption action {action!r}")
        decisions[relative] = AdoptionDecision(
            path=relative,
            action=action,
            expected_target_sha256=validate_digest(
                item["expected_target_sha256"], "expected_target_sha256", relative
            ),
            expected_template_sha256=validate_digest(
                item["expected_template_sha256"], "expected_template_sha256", relative
            ),
        )
    raw_authorization = payload["authorization"]
    destructive = any(
        decision.action == "ADOPT_TEMPLATE" for decision in decisions.values()
    )
    if raw_authorization is None:
        if destructive:
            raise ValueError(
                "ADOPT_TEMPLATE requires an exact owner-confirmation receipt"
            )
        return AdoptionPlan(source_root, target_root, decisions)
    if not isinstance(raw_authorization, dict) or set(raw_authorization) != {
        "authorized_by",
        "authorized_at",
        "authorization_source",
        "plan_sha256",
    }:
        raise ValueError(
            "Adoption authorization must contain exactly authorized_by, "
            "authorized_at, authorization_source, and plan_sha256"
        )
    authorized_by = raw_authorization["authorized_by"]
    authorized_at = raw_authorization["authorized_at"]
    authorization_source = raw_authorization["authorization_source"]
    plan_digest = validate_digest(
        raw_authorization["plan_sha256"],
        "plan_sha256",
        "authorization",
    )
    authorized_by = validate_human_identity(
        authorized_by,
        "Adoption authorization",
    )
    validate_rfc3339(authorized_at, "Adoption authorization")
    if authorization_source != "OWNER_CONFIRMATION":
        raise ValueError(
            "Adoption authorization_source must be OWNER_CONFIRMATION"
        )
    result = AdoptionPlan(
        source_root,
        target_root,
        decisions,
        authorized_by,
        authorized_at,
        authorization_source,
        plan_digest,
    )
    validate_adoption_authority(result)
    return result


def rendered_bytes(
    path: Path,
    values: dict[str, str],
    *,
    render: bool = True,
) -> bytes:
    if is_text_file(path):
        content = path.read_text(encoding="utf-8")
        if render:
            content = render_text(content, values)
        return content.encode("utf-8")
    return path.read_bytes()


def has_unsafe_parent(root: Path, destination: Path) -> bool:
    """Return true when an existing parent could redirect or block a write."""

    current = root
    for part in destination.relative_to(root).parts[:-1]:
        current = current / part
        if current.is_symlink():
            return True
        if current.exists() and not current.is_dir():
            return True
    return False


def atomic_write_bytes(destination: Path, content: bytes, source: Path) -> None:
    """Write one generated file atomically in its destination directory."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        shutil.copymode(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def validate_copy_operation(operation: CopyOperation, root: Path) -> None:
    """Recheck one planned destination without changing either tree."""

    if has_unsafe_parent(root, operation.destination):
        raise ValueError(
            f"{operation.relative}: destination parent changed after preflight"
        )
    if operation.content is None:
        if operation.destination.is_symlink() or (
            operation.destination.exists() and not operation.destination.is_dir()
        ):
            raise ValueError(
                f"{operation.relative}: directory destination changed after preflight"
            )
        return
    if operation.expected_destination_sha256 is None:
        if operation.destination.exists() or operation.destination.is_symlink():
            raise ValueError(
                f"{operation.relative}: destination appeared after preflight"
            )
        return
    if (
        operation.destination.is_symlink()
        or not operation.destination.is_file()
        or sha256_bytes(operation.destination.read_bytes())
        != operation.expected_destination_sha256
    ):
        raise ValueError(f"{operation.relative}: destination changed after preflight")


def copy_template(
    source: Path,
    target: Path,
    values: dict[str, str],
    force: bool = False,
    *,
    dry_run: bool = False,
    adoption_plan: AdoptionPlan | None = None,
    staging_target: Path | None = None,
) -> CopyReport:
    """Preflight and apply a new install or a reviewed brownfield overlay."""

    source = source.resolve()
    target = target.resolve()
    validate_non_overlapping_paths(source, target)
    if force:
        raise ValueError(
            "Blanket --force is disabled; use a hash-bound per-path adoption map"
        )
    if adoption_plan and (
        adoption_plan.source_root != source or adoption_plan.target_root != target
    ):
        raise ValueError("Adoption plan roots do not match this copy operation")
    if adoption_plan:
        validate_adoption_authority(adoption_plan)
    if staging_target is not None:
        staging_target = staging_target.expanduser().resolve()
        if staging_target in {
            Path(staging_target.anchor).resolve(),
            Path.home().resolve(),
        }:
            raise ValueError(
                f"Staging target must not be a filesystem root or home directory: {staging_target}"
            )
        if any(part.casefold() == ".git" for part in staging_target.parts):
            raise ValueError(
                f"Staging target must not be inside Git metadata: {staging_target}"
            )
        if paths_overlap(source, staging_target) or paths_overlap(target, staging_target):
            raise ValueError("Staging target must be separate from source and target")
        if staging_target.exists() and not staging_target.is_dir():
            raise ValueError(f"Staging target is not a directory: {staging_target}")

    discovered_items = sorted(
        source.rglob("*"), key=lambda item: item.relative_to(source).parts
    )
    symlinks = [item for item in discovered_items if item.is_symlink()]
    if symlinks:
        raise ValueError(
            "Template source contains unsupported symbolic link: " f"{symlinks[0]}"
        )

    items: list[Path] = []
    casefolded_paths: dict[str, str] = {}
    for item in discovered_items:
        relative_path = item.relative_to(source)
        if any(
            part.casefold() in SKIP_NAMES_CASEFOLD for part in relative_path.parts
        ) or item.suffix.casefold() in SKIP_SUFFIXES:
            continue
        relative = relative_path.as_posix()
        casefolded = "/".join(part.casefold() for part in relative_path.parts)
        previous = casefolded_paths.get(casefolded)
        if previous is not None and previous != relative:
            raise ValueError(
                "Template paths collide on a case-insensitive filesystem: "
                f"{previous}, {relative}"
            )
        casefolded_paths[casefolded] = relative
        items.append(item)

    report = CopyReport()
    operations: list[CopyOperation] = []
    collision_paths: set[str] = set()
    decisions_used: set[str] = set()
    receipts: list[str] = []
    preserved_checks: list[tuple[str, Path, str]] = []

    source_agent_paths = {
        item.relative_to(source).as_posix().casefold()
        for item in items
        if item.name.casefold() == "agents.md"
    }
    if target.is_dir():
        for target_item in sorted(target.rglob("*")):
            try:
                relative_target = target_item.relative_to(target)
            except ValueError:
                continue
            if any(
                part.casefold() in SKIP_NAMES_CASEFOLD
                for part in relative_target.parts
            ):
                continue
            relative = relative_target.as_posix()
            if (
                target_item.name.casefold() == "agents.md"
                and relative.casefold() not in source_agent_paths
            ):
                report.partial_adoption = True
                print(f"PRESERVED TARGET CONTROL {relative} reason=target-only-AGENTS")

    for item in items:
        relative_path = item.relative_to(source)
        relative = relative_path.as_posix()

        destination = target / relative_path
        if item.is_dir():
            if destination.is_symlink() or (
                destination.exists() and not destination.is_dir()
            ):
                report.collisions += 1
                report.unresolved += 1
                collision_paths.add(relative)
                print(f"COLLISION {relative} reason=target-type")
            elif not destination.exists():
                operations.append(
                    CopyOperation(relative, item, destination, None, "CREATE_DIRECTORY")
                )
            continue

        if has_unsafe_parent(target, destination):
            report.collisions += 1
            report.unresolved += 1
            collision_paths.add(relative)
            print(f"COLLISION {relative} reason=unsafe-parent")
            continue

        content = rendered_bytes(
            item,
            values,
            render=relative not in NO_RENDER_PATHS,
        )
        template_digest = sha256_bytes(content)
        if destination.is_symlink() or (
            destination.exists() and not destination.is_file()
        ):
            report.collisions += 1
            report.unresolved += 1
            collision_paths.add(relative)
            print(f"COLLISION {relative} reason=target-type")
            continue

        if not destination.exists():
            operations.append(CopyOperation(relative, item, destination, content, "WRITE"))
            report.planned += 1
            continue

        try:
            target_content = destination.read_bytes()
        except OSError as exc:
            raise ValueError(f"Unable to read collision target {destination}: {exc}") from exc
        target_digest = sha256_bytes(target_content)
        if target_content == content:
            report.unchanged += 1
            print(f"UNCHANGED {relative} sha256={target_digest}")
            continue

        report.collisions += 1
        collision_paths.add(relative)
        decision = adoption_plan.decisions.get(relative) if adoption_plan else None
        if decision is None:
            report.unresolved += 1
            print(
                f"COLLISION {relative} target_sha256={target_digest} "
                f"template_sha256={template_digest}"
            )
            continue

        decisions_used.add(relative)
        if decision.expected_target_sha256 != target_digest:
            raise ValueError(f"{relative}: target changed after adoption review")
        if decision.expected_template_sha256 != template_digest:
            raise ValueError(f"{relative}: rendered template changed after adoption review")

        if decision.action == "PRESERVE":
            report.preserved += 1
            report.partial_adoption |= (
                relative in CORE_CONTROL_PATHS
                or PurePosixPath(relative).name.casefold() == "agents.md"
            )
            preserved_checks.append((relative, destination, target_digest))
            receipts.append(
                f"ADOPTION PRESERVE {relative} pre={target_digest} post={target_digest}"
            )
        elif decision.action == "ADOPT_TEMPLATE":
            operations.append(
                CopyOperation(
                    relative,
                    item,
                    destination,
                    content,
                    "ADOPT_TEMPLATE",
                    target_digest,
                )
            )
            report.planned += 1
            report.adopted += 1
            receipts.append(
                f"ADOPTION ADOPT_TEMPLATE {relative} pre={target_digest} "
                f"post={template_digest}"
            )
        else:
            if staging_target is None:
                raise ValueError(
                    f"{relative}: STAGE_FOR_MERGE requires --staging-target"
                )
            staged_destination = staging_target / relative_path
            if has_unsafe_parent(staging_target, staged_destination):
                raise ValueError(f"{relative}: unsafe staging parent")
            if staged_destination.is_symlink() or (
                staged_destination.exists() and not staged_destination.is_file()
            ):
                raise ValueError(f"{relative}: unsafe staging collision")
            if staged_destination.exists() and staged_destination.read_bytes() != content:
                raise ValueError(f"{relative}: staging target already has different content")
            if not staged_destination.exists():
                operations.append(
                    CopyOperation(
                        relative,
                        item,
                        staged_destination,
                        content,
                        "STAGE_FOR_MERGE",
                    )
                )
                report.planned += 1
            report.staged += 1
            # Staged content has not been reconciled into the active target yet.
            report.partial_adoption = True
            receipts.append(
                f"ADOPTION STAGE_FOR_MERGE {relative} pre={target_digest} "
                f"staged={template_digest}"
            )

    if adoption_plan:
        unused = sorted(set(adoption_plan.decisions) - decisions_used)
        if unused:
            raise ValueError(
                "Adoption map contains paths that are not current collisions: "
                + ", ".join(unused)
            )

    if report.unresolved or dry_run:
        for receipt in sorted(receipts):
            print(f"PLAN {receipt}")
        for operation in operations:
            if operation.content is not None:
                print(f"PLAN {operation.action} {operation.relative}")
        return report

    for relative, destination, expected_digest in preserved_checks:
        if (
            destination.is_symlink()
            or not destination.is_file()
            or sha256_bytes(destination.read_bytes()) != expected_digest
        ):
            raise ValueError(f"{relative}: preserved target changed after preflight")

    # Recheck the complete operation set before the first write so late drift in
    # one destination cannot follow an earlier destructive adoption write.
    for operation in operations:
        operation_root = (
            staging_target if operation.action == "STAGE_FOR_MERGE" else target
        )
        if operation_root is None:
            raise ValueError(f"{operation.relative}: operation root is unavailable")
        validate_copy_operation(operation, operation_root)

    target.mkdir(parents=True, exist_ok=True)
    for operation in operations:
        operation_root = (
            staging_target if operation.action == "STAGE_FOR_MERGE" else target
        )
        if operation_root is None:
            raise ValueError(f"{operation.relative}: operation root is unavailable")
        validate_copy_operation(operation, operation_root)
        if operation.content is None:
            operation.destination.mkdir(parents=True, exist_ok=True)
            continue
        atomic_write_bytes(operation.destination, operation.content, operation.source)
        print(f"{operation.action} {operation.relative}")
        if operation.action in {"ADOPT_TEMPLATE", "STAGE_FOR_MERGE"}:
            print(
                f"ADOPTION RECEIPT {operation.action} {operation.relative} "
                f"post={sha256_bytes(operation.content)}"
            )
        report.written += 1
    for receipt in sorted(receipts):
        if receipt.startswith("ADOPTION PRESERVE"):
            print(f"ADOPTION RECEIPT {receipt.removeprefix('ADOPTION ')}")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or safely adopt an AWS Codex Fastlane project."
    )
    parser.add_argument("--target", required=True, help="Target project directory")
    parser.add_argument("--project-name", required=True, help="Human-readable project name")
    parser.add_argument("--region", default="us-west-2", help="Primary AWS Region")
    parser.add_argument(
        "--budget",
        default="$50/month",
        help='Monthly cost ceiling, for example "$50/month"',
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Deprecated and rejected; use --adoption-map",
    )
    parser.add_argument(
        "--adoption-map",
        type=Path,
        help=(
            "Per-path JSON collision decisions bound to SHA-256 digests; "
            "ADOPT_TEMPLATE also requires an exact owner-confirmation receipt"
        ),
    )
    parser.add_argument(
        "--staging-target",
        type=Path,
        help="Separate target required by STAGE_FOR_MERGE decisions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview writes and collision digests without changing the target",
    )
    args = parser.parse_args(argv)

    source = Path(__file__).resolve().parent
    target = Path(args.target).expanduser().resolve()
    values = dict(PLACEHOLDERS)
    values["My AWS Project"] = args.project_name
    values["{{AWS_REGION}}"] = args.region
    values["{{MONTHLY_BUDGET}}"] = args.budget

    try:
        validate_template_control_hashes(source)
        adoption_plan = (
            load_adoption_plan(args.adoption_map, source, target)
            if args.adoption_map
            else None
        )
        report = copy_template(
            source,
            target,
            values,
            args.force,
            dry_run=args.dry_run,
            adoption_plan=adoption_plan,
            staging_target=args.staging_target,
        )
    except (OSError, ValueError) as exc:
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 2

    print()
    if args.dry_run:
        print("Dry run complete. No files were changed.")
    elif report.unresolved:
        print("Bootstrap stopped with unresolved, preserved target collisions.")
    elif report.partial_adoption:
        print("Bootstrap partially adopted; merge staged/preserved control files and run doctor.")
    else:
        print("Bootstrap complete.")
    print(f"Project root: {target}")
    print(
        "Summary: "
        f"{report.planned} planned, {report.written} written, "
        f"{report.unchanged} unchanged, {report.collisions} collision(s), "
        f"{report.unresolved} unresolved, {report.preserved} preserved, "
        f"{report.adopted} adopted, {report.staged} staged"
    )
    if report.partial_adoption:
        print("Target-only or preserved control instructions require reconciliation.")

    if report.unresolved:
        print("Review every digest and supply a hash-bound per-path adoption map.")
        return 1
    if args.dry_run:
        return 0
    if report.partial_adoption:
        return 3

    print()
    print("Next steps:")
    print("1. Run: python scripts/bootstrap_doctor.py --root .")
    print("2. Paste BOOT-00 and START AWS CODEX BOOTSTRAP.")
    print("3. Use START GUIDED INTAKE when BOOT-00 returns it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
