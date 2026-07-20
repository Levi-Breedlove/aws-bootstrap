from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPOSITORY_ROOT
TEMPLATE_SOURCE_MODE = "{{SETUP_STATUS}}" in (
    REPOSITORY_ROOT / "bootstrap.yaml"
).read_text(encoding="utf-8")
source_template_only = unittest.skipUnless(
    TEMPLATE_SOURCE_MODE,
    "maintainer source-integrity test is not applicable after project configuration",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


doctor = load_module(
    "bootstrap_doctor_under_test",
    PROJECT_ROOT / "scripts" / "bootstrap_doctor.py",
)
bootstrap_runtime = load_module(
    "bootstrap_runtime_for_doctor_tests",
    PROJECT_ROOT / "bootstrap.py",
)


def codes(report: dict[str, object]) -> set[str]:
    return {item["code"] for item in report["diagnostics"]}  # type: ignore[index]


def set_table_value(
    text: str,
    heading: str,
    next_heading: str,
    field: str,
    value: str,
) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start + len(heading))
    section = text[start:end]
    lines = section.splitlines(keepends=True)
    prefix = f"| {field} |"
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {field!r} row in {heading!r}")
    suffix = "\n" if lines[matches[0]].endswith("\n") else ""
    lines[matches[0]] = f"| {field} | {value} |{suffix}"
    return text[:start] + "".join(lines) + text[end:]


def set_receipt(text: str, gate: str, receipt: str) -> str:
    start_marker = f"<!-- bootstrap:{gate}-receipt:start -->"
    end_marker = f"<!-- bootstrap:{gate}-receipt:end -->"
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker, start)
    body = f"\n```text\n{receipt}\n```\n"
    return text[:start] + body + text[end:]


def approve_gate_a(text: str) -> str:
    for field, value in {
        "Project mode": "`greenfield`",
        "Delivery profile": "`quick-mvp`",
        "Effective risk": "`low`",
        "AWS lane": "`documentation-only`",
    }.items():
        text = set_table_value(
            text,
            "## Document status",
            "## 1. Workload profile",
            field,
            value,
        )
    text = set_table_value(
        text,
        "## Document status",
        "## 1. Workload profile",
        "Gate A derived status",
        "`APPROVED_FOR_DESIGN`",
    )
    text = set_table_value(
        text,
        "### Gate A — agent analysis record",
        "### Gate A — owner acceptance record",
        "Requirements revision analyzed",
        "`REQ-0001`",
    )
    for field in (
        "Open blocking finding IDs",
        "Proposed assumption IDs required to proceed",
        "Open blocking decision IDs",
    ):
        text = set_table_value(
            text,
            "### Gate A — agent analysis record",
            "### Gate A — owner acceptance record",
            field,
            "`NONE`",
        )
    text = set_table_value(
        text,
        "### Gate A — agent analysis record",
        "### Gate A — owner acceptance record",
        "Agent recommendation",
        "`READY_FOR_OWNER_APPROVAL`",
    )
    gate_a_card = {
        "Outcome": "`OUT-001 — Deliver FR-001`",
        "Owner and users": "`alice; development users`",
        "Scope and non-goals": "`FR-001 in scope; production is out of scope`",
        "Measurable requirement/acceptance IDs": "`FR-001, EX-001`",
        "Data boundary": "`Synthetic internal test data only`",
        "Identity/security boundary": "`Local development identity; no public access`",
        "Environment/Region": "`Development; us-west-2`",
        "Failure/recovery": "`Fail closed; local rollback to baseline`",
        "Cost posture": "`MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`",
        "Intake provenance": "`owner message MSG-000`",
    }
    for field, value in gate_a_card.items():
        text = set_table_value(
            text,
            "### Gate A — readiness card",
            "### Gate A — owner acceptance record",
            field,
            value,
        )
    owner_values = {
        "Approver": "alice",
        "Owner decision": "`APPROVED`",
        "Authorized requirements revision": "`REQ-0001`",
        "Authorized cost posture": "`MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`",
        "Explicitly accepted assumption IDs": "`NONE`",
        "Authorization provided at": "`2026-07-17T10:00:00-07:00`",
        "Authorization source": "`owner message MSG-001`",
        "Verbatim owner receipt": "`RECORDED_BELOW`",
        "Derived Gate A state": "`APPROVED_FOR_DESIGN`",
    }
    for field, value in owner_values.items():
        text = set_table_value(
            text,
            "### Gate A — owner acceptance record",
            "### Gate A validation and invalidation rules",
            field,
            value,
        )
    return set_receipt(
        text,
        "gate-a",
        "\n".join(
            [
                "APPROVE REQUIREMENTS GATE A",
                "Requirements revision: REQ-0001",
                "Cost posture: MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
                "Accepted assumptions: NONE",
                "Approver: alice",
            ]
        ),
    )


def approve_gate_b(text: str, *, baseline: str = "a" * 40) -> str:
    text = set_table_value(
        text,
        "## Document status",
        "## 1. Workload profile",
        "Gate B derived status",
        "`APPROVED_FOR_CONSTRUCTION`",
    )
    agent_values = {
        "Requirements revision reviewed": "`REQ-0001`",
        "Design revision reviewed": "`DES-0001`",
        "Construction authorization ID reviewed": "`AUTH-0001`",
        "PRD completeness gaps": "`NONE`",
        "Requirement-to-design-and-test traceability gaps": "`NONE`",
        "Unresolved risk or preservation gaps": "`NONE`",
        "Agent recommendation": "`READY_FOR_CONSTRUCTION_APPROVAL`",
    }
    for field, value in agent_values.items():
        text = set_table_value(
            text,
            "## 27. Gate B agent review record",
            "## 28. Construction envelope",
            field,
            value,
        )
    gate_b_card = {
        "Design basis IDs": "`DES-0001, FR-001`",
        "Architecture/components": "`Bounded app and focused tests`",
        "Interfaces/data flow": "`Local request and response flow`",
        "Identity/secrets": "`No secrets; local development identity`",
        "Failure/retry/concurrency": "`Fail closed; bounded retries; serialized state`",
        "Deployment/operations": "`Documentation-only AWS lane; local commands`",
        "Validation/evidence": "`EX-001 and focused unittest evidence`",
        "Rollback/recovery/teardown": "`Restore the authorized baseline commit`",
        "Brownfield compatibility/migration": "`NOT_APPLICABLE — greenfield project`",
        "Outstanding gaps": "`NONE`",
    }
    for field, value in gate_b_card.items():
        text = set_table_value(
            text,
            "### Gate B — readiness card",
            "## 28. Construction envelope",
            field,
            value,
        )
    envelope_values = {
        "Project mode": "`greenfield`",
        "Delivery profile and effective risk": "`quick-mvp / low`",
        "Project AWS lane": "`documentation-only`",
        "Authorized outcome": "`OUT-001 — Deliver the FR-001 outcome`",
        "Authorized requirement and design IDs": "`REQ: REQ-0001; DES: DES-0001; SCOPE_IDS: FR-001`",
        "Authorized baseline commit": f"`{baseline}`",
        "Protected dirty paths": "`NONE`",
        "In-scope components and environments": "`app and tests in development`",
        "Allowed repository write set": "`PATHS: app/**; tests/**`",
        "Excluded or owner-only write set": "`PATHS: docs/project/PRD.md; bootstrap.yaml`",
        "Allowed external-state targets": "`NONE`",
        "Task boundary": "`DERIVED_FROM_AUTHORIZED_IDS_AND_WRITE_SET`",
        "Autonomous construction": "`ALLOWED`",
        "Maximum generated tasks": "`8`",
        "Maximum parallel workers": "`2`",
        "Parallelism rule": "`Disjoint changes in isolated worktrees; otherwise serialize`",
        "Attempt budget": "`3`",
        "Checkpoint cadence": "`COMMIT_AFTER_EACH_VALIDATED_WAVE_BEFORE_PAUSE`",
        "Local command boundary": "`ALLOW_PREFIXES: python -m unittest`",
        "GitHub boundary": "`NONE`",
        "GitHub repository, branch, and merge constraints": "`NONE`",
        "AWS boundary": "`DOCS_ONLY`",
        "Rollback, recovery, and teardown boundary": "`Local rollback only; teardown prohibited`",
        "Mandatory stop conditions": "`Any boundary, gate, attempt, or evidence mismatch`",
        "Authorization expiry or completion condition": "`Expires at 2099-12-31T23:59:59Z; earlier completion: release review`",
    }
    aws_not_applicable = "`NOT_APPLICABLE — AWS boundary DOCS_ONLY authorizes no authenticated action`"
    for field in doctor.AWS_DETAIL_FIELDS:
        envelope_values[field] = aws_not_applicable
    for field, value in envelope_values.items():
        text = set_table_value(
            text,
            "## 28. Construction envelope",
            "## 29. Gate B owner authorization record",
            field,
            value,
        )
    envelope_digest = doctor.canonical_envelope_sha256(text)
    text = set_table_value(
        text,
        "## 27. Gate B agent review record",
        "## 28. Construction envelope",
        "Construction envelope SHA-256 reviewed",
        f"`{envelope_digest}`",
    )
    owner_values = {
        "Approver": "alice",
        "Owner decision": "`APPROVED`",
        "Authorized requirements revision": "`REQ-0001`",
        "Authorized design revision": "`DES-0001`",
        "Authorized construction authorization ID": "`AUTH-0001`",
        "Authorized construction envelope SHA-256": f"`{envelope_digest}`",
        "Authorization provided at": "`2026-07-17T10:30:00-07:00`",
        "Authorization source": "`owner message MSG-002`",
        "Verbatim owner receipt": "`RECORDED_BELOW`",
        "Derived Gate B state": "`APPROVED_FOR_CONSTRUCTION`",
    }
    for field, value in owner_values.items():
        text = set_table_value(
            text,
            "## 29. Gate B owner authorization record",
            "## 30. Gate B validation and invalidation rules",
            field,
            value,
        )
    return set_receipt(
        text,
        "gate-b",
        "\n".join(
            [
                "APPROVE PRD AND CONSTRUCTION GATE B",
                "Requirements revision: REQ-0001",
                "Design revision: DES-0001",
                "Construction authorization: AUTH-0001",
                f"Construction envelope SHA-256: {envelope_digest}",
                "Use the proposed construction envelope above.",
                "Approver: alice",
            ]
        ),
    )


def rebind_gate_b_envelope(text: str) -> str:
    digest = doctor.canonical_envelope_sha256(text)
    text = set_table_value(
        text,
        "## 27. Gate B agent review record",
        "## 28. Construction envelope",
        "Construction envelope SHA-256 reviewed",
        f"`{digest}`",
    )
    text = set_table_value(
        text,
        "## 29. Gate B owner authorization record",
        "## 30. Gate B validation and invalidation rules",
        "Authorized construction envelope SHA-256",
        f"`{digest}`",
    )
    return set_receipt(
        text,
        "gate-b",
        "\n".join(
            [
                "APPROVE PRD AND CONSTRUCTION GATE B",
                "Requirements revision: REQ-0001",
                "Design revision: DES-0001",
                "Construction authorization: AUTH-0001",
                f"Construction envelope SHA-256: {digest}",
                "Use the proposed construction envelope above.",
                "Approver: alice",
            ]
        ),
    )


def current_greenfield_state(state: dict[str, object], *, gate_b: bool = False) -> None:
    setup = state["setup"]
    project = state["project"]
    lifecycle = state["lifecycle"]
    assert isinstance(setup, dict)
    assert isinstance(project, dict)
    assert isinstance(lifecycle, dict)
    setup.update({"status": "CONFIGURED", "method": "EXTERNAL_COPY"})
    project.update(
        {
            "name": "Doctor Test Project",
            "region": "us-west-2",
            "cost_posture": "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
            "mode": "greenfield",
            "delivery_profile": "quick-mvp",
            "effective_risk": "low",
            "aws_lane": "documentation-only",
            "brownfield_baseline": "NOT_APPLICABLE",
        }
    )
    lifecycle["gate_a"] = "APPROVED_FOR_DESIGN"
    if gate_b:
        lifecycle["gate_b"] = "APPROVED_FOR_CONSTRUCTION"


def record_aws_core_evidence(
    text: str,
    phase: str,
    status: str = "PASS",
    *,
    binding: str | None = None,
) -> str:
    if binding is None:
        binding = {
            "BOOT-00": "bootstrap:1.1.0",
            "DESIGN-10": "DES-0001",
            "AWS-10": "sha256:" + "a" * 64,
        }[phase]
    replacement = (
        f"| `{phase}` | `aws/agent-toolkit-for-aws` | "
        "`aws-core@agent-toolkit-for-aws` | "
        "`retrieve_skill` + `search_documentation` | "
        "`aws-architecture` | `Current AWS service and IAM guidance` | "
        "`https://docs.aws.amazon.com/` | `DES-0001 architecture review` | "
        f"`2026-07-20T12:00:00Z` | `{binding}` | `{status}` |"
    )
    updated, count = re.subn(
        rf"^\| `{re.escape(phase)}` \|.*$",
        replacement,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise AssertionError(f"Missing AWS Core evidence row for {phase}")
    return updated


def current_task_snapshot(
    text: str,
    *,
    gate_b: str = "APPROVED_FOR_CONSTRUCTION",
    baseline: str = "a" * 40,
) -> str:
    replacements = {
        "| Gate B state | `BLOCKED` |": f"| Gate B state | `{gate_b}` |",
        "| Baseline commit | `TODO` |": f"| Baseline commit | `{baseline}` |",
        "| Last known-green commit | `TODO` |": f"| Last known-green commit | `{baseline}` |",
        "| Next safe action | Complete Gate B; when current, run `TASK-10` |": "| Next safe action | Run `TASK-10` |",
    }
    for old, new in replacements.items():
        if old not in text:
            raise AssertionError(f"Missing task snapshot row: {old}")
        text = text.replace(old, new, 1)
    return text


def ready_task(
    write_set: str = "app/main.py",
    *,
    requirements: str = "REQ-0001; FR-001",
    design: str = "DES-0001; implementation design",
    outcome: str = "The authorized slice is implemented without expanding scope.",
    external_state: str = "NONE",
    command: str = "python -m unittest",
    github_issue: str = "PENDING_SYNC",
) -> str:
    return f"""

### TASK-001 — Implement the authorized slice

- Status: `READY`
- Requirements: `{requirements}`
- Design: `{design}`
- Authorization: `AUTH-0001`
- Depends on: `NONE`
- Dependency waivers: `NONE`
- Owner: `UNASSIGNED`
- Run ID: `NONE`
- Risk: `low`
- Write set: `{write_set}`
- External state: `{external_state}`
- AWS mode: `NONE`
- Attempt budget: `3`
- Attempts used: `0`
- Evidence: `NONE`
- Blocker: `NONE`
- Skip record: `NONE`
- GitHub issue: `{github_issue}`
- Last checkpoint: `NONE`
- Last updated: `2026-07-17T11:00:00-07:00`

#### Outcome

{outcome}

#### Acceptance criteria

- [ ] The authorized behavior passes its focused test.

#### Validation

```bash
{command}
```

#### Execution log

Not started.
"""


class BootstrapDoctorTests(unittest.TestCase):
    def copy_project(self, destination: Path) -> Path:
        project = destination / "project"
        project.mkdir()
        manifest = json.loads(
            (PROJECT_ROOT / "bootstrap.manifest.json").read_text(encoding="utf-8")
        )
        for relative in manifest["required_files"]:
            source = PROJECT_ROOT.joinpath(*PurePosixPath(relative).parts)
            target = project.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        values = dict(bootstrap_runtime.PLACEHOLDERS)
        values.update(
            {
                "My AWS Project": "Doctor Test Project",
                "{{AWS_REGION}}": "us-west-2",
                "{{COST_POSTURE}}": "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
            }
        )
        for relative in manifest["required_files"]:
            if not bootstrap_runtime.should_render_path(relative):
                continue
            path = project.joinpath(*PurePosixPath(relative).parts)
            rendered = bootstrap_runtime.rendered_bytes(path, values, render=True)
            if rendered != path.read_bytes():
                path.write_bytes(rendered)
        return project

    def approve_project(self, project: Path, *, gate_b: bool = True) -> None:
        baseline = "a" * 40
        if gate_b:
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            subprocess.run(["git", "-C", str(project), "config", "user.name", "Doctor Test"], check=True)
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "doctor@example.test"],
                check=True,
            )
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "baseline"], check=True)
            baseline = subprocess.run(
                ["git", "-C", str(project), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        prd_path = project / "docs/project/PRD.md"
        text = approve_gate_a(prd_path.read_text(encoding="utf-8"))
        if gate_b:
            text = approve_gate_b(text, baseline=baseline)
        prd_path.write_text(text, encoding="utf-8")
        state_path = project / "bootstrap.yaml"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        current_greenfield_state(state, gate_b=gate_b)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        if gate_b:
            tasks_path = project / "docs/project/TASKS.md"
            tasks_path.write_text(
                current_task_snapshot(
                    tasks_path.read_text(encoding="utf-8"), baseline=baseline
                ),
                encoding="utf-8",
            )
            verify_path = project / "docs/project/VERIFY.md"
            verify_text = record_aws_core_evidence(
                verify_path.read_text(encoding="utf-8"), "BOOT-00"
            )
            verify_text = record_aws_core_evidence(verify_text, "DESIGN-10")
            verify_path.write_text(verify_text, encoding="utf-8")

    def initialize_task_plan(self, project: Path, task_text: str) -> None:
        state_path = project / "bootstrap.yaml"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["execution"]["plan_revision"] = "PLAN-0001"
        state["execution"]["plan_state"] = "CURRENT"
        state["execution"]["attempts"] = {"TASK-001": 0}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        tasks_path = project / "docs/project/TASKS.md"
        text = tasks_path.read_text(encoding="utf-8").replace(
            "| Task-plan revision | `UNINITIALIZED` |",
            "| Task-plan revision | `PLAN-0001` |",
            1,
        )
        text = text.replace(
            "| Task-plan state | `UNINITIALIZED` |",
            "| Task-plan state | `CURRENT` |",
            1,
        )
        tasks_path.write_text(text + task_text, encoding="utf-8")

    def pause_project_at_real_checkpoint(self, project: Path) -> str:
        """Create a coherent paused checkpoint with coordinator ledgers dirty."""

        subprocess.run(["git", "-C", str(project), "add", "docs/project/PRD.md"], check=True)
        subprocess.run(
            ["git", "-C", str(project), "commit", "-qm", "approve gate b prd"],
            check=True,
        )
        known_green = subprocess.run(
            ["git", "-C", str(project), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.initialize_task_plan(project, ready_task())

        state_path = project / "bootstrap.yaml"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["execution"].update(
            {
                "mode": "SINGLE_TASK",
                "state": "CHECKPOINTED",
                "run_id": "RUN-0001",
                "coordinator": "doctor-test-coordinator",
                "basis": {
                    "requirements_revision": "REQ-0001",
                    "design_revision": "DES-0001",
                    "construction_authorization": "AUTH-0001",
                },
                "active_tasks": [],
                "last_checkpoint": {
                    "id": "CP-0001",
                    "at": "2026-07-17T12:00:00-07:00",
                    "evidence_ref": "docs/project/VERIFY.md#cp-0001",
                },
            }
        )
        state_path.write_text(json.dumps(state), encoding="utf-8")

        tasks_path = project / "docs/project/TASKS.md"
        text = tasks_path.read_text(encoding="utf-8")
        for field, value in {
            "Run state": "`PAUSED`",
            "Active run ID": "`RUN-0001`",
            "Coordinator": "`doctor-test-coordinator`",
            "Last checkpoint": "`CP-0001`",
            "Last known-green commit": f"`{known_green}`",
            "Next safe action": "Resume the current checkpointed run.",
        }.items():
            text = set_table_value(
                text,
                "## Active execution snapshot",
                "## Coordinator and worker contract",
                field,
                value,
            )
        checkpoint = (
            f"| `CP-0001` | `RUN-0001` | 2026-07-17T12:00:00-07:00 | "
            f"`REQ-0001` / `DES-0001` / `AUTH-0001` | "
            f"Commit: `{known_green}`; Dirty: NONE | "
            "TASK-001 READY attempts=0/3 | Evidence: NONE; External: NONE | "
            "Blockers: NONE; Next: resume TASK-001 |\n"
        )
        text = text.replace("\n\nTo resume,", "\n" + checkpoint + "\nTo resume,", 1)
        tasks_path.write_text(text, encoding="utf-8")

        verify_path = project / "docs/project/VERIFY.md"
        verify_path.write_text(
            verify_path.read_text(encoding="utf-8")
            + "\n\n### CP-0001\n\nCheckpoint receipt recorded.\n",
            encoding="utf-8",
        )
        return known_green

    @source_template_only
    def test_template_source_is_coherent_and_routes_to_intake(self) -> None:
        report = doctor.inspect_project(PROJECT_ROOT, template_source=True)

        self.assertTrue(report["ok"], report["diagnostics"])
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["bootstrap_version"], "1.1.0")
        self.assertEqual(report["classification"], "TEMPLATE_SOURCE")
        self.assertEqual(report["next_prompt"], "INTAKE-10")
        self.assertEqual(
            report["gates"],
            {"gate_a": "BLOCKED", "gate_b": "BLOCKED"},
        )
        self.assertEqual(report["evidence_state"], "NOT_READY")
        self.assertEqual(
            report["authorizations"],
            {"construction": "NONE", "aws": "NONE"},
        )

    def test_doctor_does_not_mutate_project(self) -> None:
        before = {
            path.relative_to(PROJECT_ROOT): (
                path.read_bytes(),
                path.stat().st_mode,
                path.stat().st_mtime_ns,
            )
            for path in PROJECT_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }

        doctor.inspect_project(PROJECT_ROOT, template_source=True)

        after = {
            path.relative_to(PROJECT_ROOT): (
                path.read_bytes(),
                path.stat().st_mode,
                path.stat().st_mtime_ns,
            )
            for path in PROJECT_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(after, before)

    @source_template_only
    def test_active_project_rejects_unresolved_placeholders(self) -> None:
        report = doctor.inspect_project(PROJECT_ROOT)

        self.assertFalse(report["ok"])
        self.assertIn("PLACEHOLDER_UNRESOLVED", codes(report))
        self.assertEqual(report["next_prompt"], "STOP")

    def test_missing_manifest_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            (project / "docs/project/PRD.md").unlink()

            report = doctor.inspect_project(project)

        self.assertIn("REQUIRED_FILE_MISSING", codes(report))
        self.assertFalse(report["resume_safe"])

    def test_required_file_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.copy_project(root)
            outside = root / "outside.md"
            outside.write_text("not a PRD", encoding="utf-8")
            (project / "docs/project/PRD.md").unlink()
            try:
                os.symlink(outside, project / "docs/project/PRD.md")
            except OSError as exc:
                self.skipTest(f"Symbolic links unavailable: {exc}")

            report = doctor.inspect_project(project)

        self.assertIn("REQUIRED_FILE_SYMLINK", codes(report))

    def test_state_prd_revision_drift_stops(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            path = project / "bootstrap.yaml"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["lifecycle"]["requirements_revision"] = "REQ-0002"
            path.write_text(json.dumps(state), encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("STATE_PRD_DRIFT", codes(report))
        self.assertEqual(report["next_prompt"], "STOP")

    def test_high_risk_requires_high_risk_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"].update(
                {
                    "mode": "greenfield",
                    "delivery_profile": "quick-mvp",
                    "effective_risk": "high",
                    "aws_lane": "explicit-gate",
                    "brownfield_baseline": "NOT_APPLICABLE",
                }
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            for field, value in {
                "Project mode": "`greenfield`",
                "Delivery profile": "`quick-mvp`",
                "Effective risk": "`high`",
                "AWS lane": "`explicit-gate`",
            }.items():
                text = set_table_value(
                    text, "## Document status", "## 1. Workload profile", field, value
                )
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("PROJECT_RISK_PROFILE", codes(report))

    def test_persisted_running_state_is_not_safe_to_resume(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            path = project / "bootstrap.yaml"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["execution"]["state"] = "RUNNING"
            path.write_text(json.dumps(state), encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("RUN_UNCLEAN_INTERRUPTION", codes(report))
        self.assertEqual(report["next_prompt"], "STOP")

    def test_exact_approved_receipts_route_uninitialized_plan_to_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)

            report = doctor.inspect_project(project)

        self.assertTrue(report["ok"], report["diagnostics"])
        self.assertEqual(report["next_prompt"], "TASK-10")

    def test_altered_approved_gate_b_receipt_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            text = text.replace("Approver: alice\n```\n<!-- bootstrap:gate-b", "Approver: mallory\n```\n<!-- bootstrap:gate-b")
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_B_RECEIPT_MISMATCH", codes(report))

    def test_task_dependency_cycle_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["execution"]["plan_revision"] = "PLAN-0001"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            tasks_path = project / "docs/project/TASKS.md"
            text = tasks_path.read_text(encoding="utf-8").replace(
                "| Task-plan revision | `UNINITIALIZED` |",
                "| Task-plan revision | `PLAN-0001` |",
            )
            text += """

### TASK-001 — First

- Status: `READY`
- Depends on: `TASK-002`

### TASK-002 — Second

- Status: `READY`
- Depends on: `TASK-001`
"""
            tasks_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("TASK_GRAPH_INVALID", codes(report))

    def test_doctor_never_executes_project_task_tool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            sentinel = Path(directory) / "executed"
            (project / "scripts" / "task_waves.py").write_text(
                f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('bad')\nraise RuntimeError('executed')\n",
                encoding="utf-8",
            )

            report = doctor.inspect_project(project)
            executed = sentinel.exists()

        self.assertFalse(report["ok"])
        self.assertIn("CONTROL_HASH_MISMATCH", codes(report))
        self.assertFalse(executed)

    def test_fenced_fake_task_is_not_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            tasks_path = project / "docs/project/TASKS.md"
            tasks_path.write_text(
                tasks_path.read_text(encoding="utf-8")
                + """
```markdown
### TASK-999 — This is documentation, not a task
- Status: `IN_PROGRESS`
- Depends on: `TASK-999`
```
""",
                encoding="utf-8",
            )

            report = doctor.inspect_project(project)

        self.assertTrue(report["ok"], report["diagnostics"])
        self.assertEqual(report["tasks"]["total"], 0)

    def test_fenced_prd_tables_cannot_shadow_authoritative_structure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            fake = """```markdown
## 28. Construction envelope

| Field | Authorized boundary |
|---|---|
| Authorized baseline commit | `ffffffffffffffffffffffffffffffffffffffff` |
```

"""
            prd_path.write_text(
                fake + prd_path.read_text(encoding="utf-8"), encoding="utf-8"
            )

            report = doctor.inspect_project(project)

        self.assertNotIn("PRD_STRUCTURE", codes(report))
        self.assertNotIn("GATE_B_ENVELOPE_HASH", codes(report))

    def test_write_boundaries_reject_git_directory_case_insensitively(self) -> None:
        for value in (".git/config", ".GIT/config", "app/.Git/index"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                doctor.parse_task_write_set(value, "TASK-001")

    def test_embedded_task_parser_enforces_key_task_invariants(self) -> None:
        snapshot = {
            "Requirements revision": "REQ-0001",
            "Design revision": "DES-0001",
            "Construction authorization": "AUTH-0001",
            "Gate B state": "APPROVED_FOR_CONSTRUCTION",
            "Run state": "NOT_STARTED",
            "Active run ID": "NONE",
        }
        ledger = (PROJECT_ROOT / "docs/project/TASKS.md").read_text(encoding="utf-8")
        task = ready_task()
        cases = {
            "duplicate singleton metadata": ledger + task.replace(
                "- Status: `READY`", "- Status: `READY`\n- Status: `READY`", 1
            ),
            "stale execution basis": ledger + task.replace("REQ-0001; FR-001", "REQ-9999; FR-001", 1),
            "missing objective section": ledger + task.replace("#### Validation", "#### Checks", 1),
            "ambiguous external target": ledger + task.replace(
                "- External state: `NONE`", "- External state: `aws:*`", 1
            ),
            "fenced heading cannot satisfy section": ledger
            + task.replace("#### Outcome", "#### Summary", 1).replace(
                "python -m unittest", "#### Outcome\nFake fenced heading\npython -m unittest", 1
            ),
        }
        for label, text in cases.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                doctor.validate_task_records(text, snapshot)

    def test_done_requires_observed_log_and_passing_structured_local_evidence(self) -> None:
        snapshot = {
            "Requirements revision": "REQ-0001",
            "Design revision": "DES-0001",
            "Construction authorization": "AUTH-0001",
            "Gate B state": "APPROVED_FOR_CONSTRUCTION",
            "Task-plan state": "CURRENT",
            "Run state": "NOT_STARTED",
            "Active run ID": "NONE",
        }
        ledger = (PROJECT_ROOT / "docs/project/TASKS.md").read_text(encoding="utf-8")
        done = (
            ready_task()
            .replace("- Status: `READY`", "- Status: `DONE`", 1)
            .replace("- Evidence: `NONE`", "- Evidence: `EV-0001`", 1)
            .replace("- [ ]", "- [x]", 1)
        )
        valid_verify = """## Task completion evidence

| Evidence ID | Task | Command or observation | Result | Actor | Observed at | Commit / worktree / artifact | Durable source | Status |
|---|---|---|---|---|---|---|---|---|
| EV-0001 | TASK-001 | python -m unittest | passed | alice | 2026-07-17T12:00:00-07:00 | commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | docs/project/VERIFY.md#ev-0001 | LOCAL_PASS |
"""
        with self.assertRaisesRegex(ValueError, "observed Execution log"):
            doctor.validate_task_records(ledger + done, snapshot, valid_verify)

        observed = done.replace(
            "Not started.",
            "2026-07-17T12:00:00-07:00 coordinator observed validation pass.",
            1,
        )
        stock_verify = (PROJECT_ROOT / "docs/project/VERIFY.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "wrong task|placeholder evidence|LOCAL_PASS"):
            doctor.validate_task_records(ledger + observed, snapshot, stock_verify)

        invalid_id = observed.replace("EV-0001", "EVIDENCE-0001", 1)
        with self.assertRaisesRegex(ValueError, "invalid local Evidence ID"):
            doctor.validate_task_records(ledger + invalid_id, snapshot, valid_verify)

        multi_done = observed.replace("EV-0001", "EV-0001, EV-0002", 1)
        multi_verify = valid_verify + (
            "| EV-0002 | TASK-001 | python -m unittest integration | passed | alice | "
            "2026-07-17T12:01:00-07:00 | "
            "commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | "
            "docs/project/VERIFY.md#ev-0002 | VERIFIED |\n"
        )
        doctor.validate_task_records(ledger + multi_done, snapshot, multi_verify)

        mixed_url = observed.replace(
            "EV-0001", "EV-0001, https://evidence.example.test/runs/EV-0001", 1
        )
        doctor.validate_task_records(ledger + mixed_url, snapshot, valid_verify)

        traversal_source = valid_verify.replace(
            "docs/project/VERIFY.md#ev-0001", "artifact: a/../b", 1
        )
        with self.assertRaisesRegex(ValueError, "durable source"):
            doctor.validate_task_records(ledger + observed, snapshot, traversal_source)

    def test_malformed_nested_state_never_crashes(self) -> None:
        for key in ("project", "lifecycle", "execution"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                project = self.copy_project(Path(directory))
                state_path = project / "bootstrap.yaml"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                state[key] = "malformed"
                state_path.write_text(json.dumps(state), encoding="utf-8")

                report = doctor.inspect_project(project)

                self.assertFalse(report["ok"])
                self.assertIn("STATE_SCHEMA", codes(report))
                self.assertEqual(report["next_prompt"], "STOP")

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"]["mode"] = []
            state["lifecycle"]["gate_a"] = {}
            state["execution"]["state"] = []
            state["execution"]["active_tasks"] = [{}]
            state_path.write_text(json.dumps(state), encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertFalse(report["ok"])
        self.assertIn("PROJECT_VOCABULARY", codes(report))
        self.assertIn("STATE_GATE", codes(report))
        self.assertIn("STATE_RUN", codes(report))

    def test_gate_a_requires_exact_assumption_acceptance_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project, gate_b=False)
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            text = set_table_value(
                text,
                "### Gate A — agent analysis record",
                "### Gate A — owner acceptance record",
                "Proposed assumption IDs required to proceed",
                "`ASM-001`",
            )
            text = set_table_value(
                text,
                "### Gate A — owner acceptance record",
                "### Gate A validation and invalidation rules",
                "Explicitly accepted assumption IDs",
                "`ASM-001, ASM-999`",
            )
            text = set_table_value(
                text,
                "### Gate A — owner acceptance record",
                "### Gate A validation and invalidation rules",
                "Authorization source",
                "`TODO`",
            )
            text = set_receipt(
                text,
                "gate-a",
                "\n".join(
                    [
                        "APPROVE REQUIREMENTS GATE A",
                        "Requirements revision: REQ-0001",
                        "Cost posture: MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
                        "Accepted assumptions: ASM-001, ASM-999",
                        "Approver: alice",
                    ]
                ),
            )
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_A_ASSUMPTIONS", codes(report))
        self.assertIn("GATE_A_OWNER_RECORD", codes(report))

    def test_gate_approvers_must_be_explicit_humans(self) -> None:
        for identity in (
            "Codex",
            "AI",
            "AUTOMATION",
            "release agent",
            "system",
            "service-account",
            "PENDING",
            "PLACEHOLDER",
            "NOT_STARTED",
        ):
            with self.subTest(identity=identity):
                self.assertFalse(doctor.explicit_human_approver(identity))
        self.assertTrue(doctor.explicit_human_approver("Alice Rivera"))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            prd_path = project / "docs/project/PRD.md"
            text = approve_gate_a(prd_path.read_text(encoding="utf-8"))
            text = set_table_value(
                text,
                "### Gate A — owner acceptance record",
                "## 14. Architecture overview",
                "Approver",
                "`PENDING`",
            )
            text = text.replace(
                "Approver: alice\n```\n<!-- bootstrap:gate-a",
                "Approver: PENDING\n```\n<!-- bootstrap:gate-a",
            )
            prd_path.write_text(text, encoding="utf-8")
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            current_greenfield_state(state)
            state_path.write_text(json.dumps(state), encoding="utf-8")

            gate_a_report = doctor.inspect_project(project)

        self.assertIn("GATE_A_HUMAN_APPROVER", codes(gate_a_report))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 29. Gate B owner authorization record",
                "## 30. Gate B validation and invalidation rules",
                "Approver",
                "`PLACEHOLDER`",
            )
            text = text.replace(
                "Approver: alice\n```\n<!-- bootstrap:gate-b",
                "Approver: PLACEHOLDER\n```\n<!-- bootstrap:gate-b",
            )
            prd_path.write_text(text, encoding="utf-8")

            gate_b_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_HUMAN_APPROVER", codes(gate_b_report))

    def test_gate_a_assumption_order_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project, gate_b=False)
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            text = set_table_value(
                text,
                "### Gate A — agent analysis record",
                "### Gate A — owner acceptance record",
                "Proposed assumption IDs required to proceed",
                "`ASM-001, ASM-002`",
            )
            text = set_table_value(
                text,
                "### Gate A — owner acceptance record",
                "### Gate A validation and invalidation rules",
                "Explicitly accepted assumption IDs",
                "`ASM-002, ASM-001`",
            )
            text = set_receipt(
                text,
                "gate-a",
                "\n".join(
                    [
                        "APPROVE REQUIREMENTS GATE A",
                        "Requirements revision: REQ-0001",
                        "Cost posture: MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
                        "Accepted assumptions: ASM-002, ASM-001",
                        "Approver: alice",
                    ]
                ),
            )
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_A_ASSUMPTIONS", codes(report))

    def test_gate_b_rejects_any_unresolved_critical_envelope_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Mandatory stop conditions",
                "`TODO`",
            )
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_B_ENVELOPE", codes(report))

    def test_gate_b_requires_fresh_design_aws_core_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            verify_path = project / "docs/project/VERIFY.md"
            verify_path.write_text(
                record_aws_core_evidence(
                    verify_path.read_text(encoding="utf-8"),
                    "DESIGN-10",
                    "NOT_STARTED",
                ),
                encoding="utf-8",
            )

            report = doctor.inspect_project(project)

        self.assertIn("AWS_CORE_EVIDENCE_REQUIRED", codes(report))
        self.assertEqual(report["next_prompt"], "STOP")

    def test_missing_aws_10_evidence_blocks_aws_execution_planning(self) -> None:
        verify_text = (REPOSITORY_ROOT / "docs/project/VERIFY.md").read_text(
            encoding="utf-8"
        )
        rows = doctor.parse_aws_core_evidence(verify_text)
        binding = "sha256:" + "a" * 64
        self.assertTrue(
            doctor.aws_core_phase_evidence_issues(
                rows, "AWS-10", expected_binding=binding
            )
        )

        passed = record_aws_core_evidence(
            verify_text, "AWS-10", binding=binding
        )
        passed_rows = doctor.parse_aws_core_evidence(passed)
        self.assertEqual(
            doctor.aws_core_phase_evidence_issues(
                passed_rows, "AWS-10", expected_binding=binding
            ),
            [],
        )
        self.assertTrue(
            doctor.aws_core_phase_evidence_issues(
                passed_rows,
                "AWS-10",
                expected_binding="sha256:" + "b" * 64,
            )
        )

    def test_split_aws_rows_are_conditionally_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS account",
                "`NONE`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")

            docs_only_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_ENVELOPE", codes(docs_only_report))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            text = set_table_value(
                text, "## Document status", "## 1. Workload profile", "AWS lane", "`fast-dev`"
            )
            for field, value in {
                "Project AWS lane": "`fast-dev`",
                "AWS boundary": "`MUTATE_LISTED_RESOURCES`",
            }.items():
                text = set_table_value(
                    text,
                    "## 28. Construction envelope",
                    "## 29. Gate B owner authorization record",
                    field,
                    value,
                )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"]["aws_lane"] = "fast-dev"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            mutation_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_ENVELOPE", codes(mutation_report))

    def test_fast_dev_mutation_requires_nonproduction_artifact_and_finite_validity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"]["aws_lane"] = "fast-dev"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            text = set_table_value(
                text, "## Document status", "## 1. Workload profile", "AWS lane", "`fast-dev`"
            )
            values = {
                "Project AWS lane": "`fast-dev`",
                "AWS boundary": "`MUTATE_LISTED_RESOURCES`",
                "AWS account": "`ACCOUNT: 123456789012`",
                "AWS role or profile": "`ROLE: fast-dev-deployer`",
                "AWS Region": "`REGION: us-west-2`",
                "AWS environment": "`ENVIRONMENT: production; CLASS: PRODUCTION`",
                "AWS stack or application": "`STACK: fastlane-test`",
                "AWS resource allowlist": "`RESOURCES: arn:aws:cloudformation:us-west-2:123456789012:stack/fastlane-test`",
                "AWS allowed operations": "`OPERATIONS: cloudformation:CreateChangeSet, cloudformation:ExecuteChangeSet`",
                "AWS cost ceiling": "`USD: 20`",
                "AWS prohibited operations": "`PROHIBITED: IAM broadening, wildcard resources, destructive replacement`",
                "AWS artifact authorization and provenance": "`EXACT_DIGEST: sha256:"
                + "1" * 64
                + "`",
                "AWS rollback boundary": "`ROLLBACK: delete only the authorized fastlane-test stack`",
                "AWS authorization validity": "`Expires at 2099-01-01T00:00:00Z; earlier completion: authorized stack reaches terminal state`",
            }
            for field, value in values.items():
                text = set_table_value(
                    text,
                    "## 28. Construction envelope",
                    "## 29. Gate B owner authorization record",
                    field,
                    value,
                )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")

            production_report = doctor.inspect_project(project)

            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS environment",
                "`ENVIRONMENT: dev; CLASS: NON_PRODUCTION`",
            )
            text = set_table_value(
                text,
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS artifact authorization and provenance",
                "`latest build`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            artifact_report = doctor.inspect_project(project)

            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS artifact authorization and provenance",
                "`EXACT_DIGEST: sha256:" + "2" * 64 + "`",
            )
            text = set_table_value(
                text,
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS authorization validity",
                "`forever`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            validity_report = doctor.inspect_project(project)

            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS authorization validity",
                "`Expires at 2099-01-01T00:00:00Z; earlier completion: authorized stack reaches terminal state`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            valid_mutation_report = doctor.inspect_project(project)

            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS cost ceiling",
                "`unlimited`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            invalid_cost_report = doctor.inspect_project(project)

            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS cost ceiling",
                "`USD: 20.00`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")

            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"]["aws_lane"] = "explicit-gate"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            text = prd_path.read_text(encoding="utf-8")
            text = set_table_value(
                text,
                "## Document status",
                "## 1. Workload profile",
                "AWS lane",
                "`explicit-gate`",
            )
            text = set_table_value(
                text,
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Project AWS lane",
                "`explicit-gate`",
            )
            text = set_table_value(
                text,
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "AWS environment",
                "`ENVIRONMENT: production; CLASS: PRODUCTION`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            explicit_gate_report = doctor.inspect_project(project)

        production_messages = "\n".join(
            item["message"] for item in production_report["diagnostics"]
        )
        artifact_messages = "\n".join(
            item["message"] for item in artifact_report["diagnostics"]
        )
        validity_messages = "\n".join(
            item["message"] for item in validity_report["diagnostics"]
        )
        invalid_cost_messages = "\n".join(
            item["message"] for item in invalid_cost_report["diagnostics"]
        )
        self.assertIn("must be NON_PRODUCTION", production_messages)
        self.assertIn("EXACT_DIGEST", artifact_messages)
        self.assertIn("Expires at <ISO8601>", validity_messages)
        self.assertIn("finite positive currency amount", invalid_cost_messages)
        self.assertEqual(invalid_cost_report["authorizations"]["aws"], "NONE")
        self.assertNotIn("GATE_B_ENVELOPE", codes(valid_mutation_report))
        self.assertNotIn("AWS_LANE_BOUNDARY", codes(valid_mutation_report))
        self.assertNotIn("GATE_B_ENVELOPE", codes(explicit_gate_report))
        self.assertNotIn("AWS_LANE_BOUNDARY", codes(explicit_gate_report))

    def test_cost_posture_and_mutation_ceiling_are_canonical_and_bounded(self) -> None:
        self.assertIsNone(
            doctor.parse_cost_posture(
                "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED"
            )
        )
        currency, amount = doctor.parse_cost_posture(
            "MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00"
        )
        self.assertEqual(currency, "USD")
        self.assertEqual(str(amount), "20.00")
        doctor.validate_aws_cost_ceiling(
            "USD: 20.00",
            "MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00",
        )
        for invalid in (
            "unlimited",
            "HARD_CAP_NOT_STATED",
            "-1",
            "NaN",
            "Infinity",
            "20.00",
            "usd: 20.00",
            "USD: 0",
            "USD: 20.000",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "finite positive"):
                    doctor.validate_aws_cost_ceiling(
                        invalid,
                        "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
                    )
        for invalid_currency in ("ZZZ: 20.00", "XTS: 20.00", "XXX: 20.00"):
            with self.subTest(invalid_currency=invalid_currency):
                with self.assertRaisesRegex(ValueError, "current ISO 4217"):
                    doctor.validate_aws_cost_ceiling(
                        invalid_currency,
                        "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
                    )
        with self.assertRaisesRegex(ValueError, "current ISO 4217"):
            doctor.parse_cost_posture(
                "MINIMIZE_TOTAL_COST; HARD_CAP: ZZZ 20.00"
            )
        self.assertEqual(
            bootstrap_runtime.ISO_4217_CURRENCY_CODES,
            doctor.ISO_4217_CURRENCY_CODES,
        )
        with self.assertRaisesRegex(ValueError, "currency must match"):
            doctor.validate_aws_cost_ceiling(
                "EUR: 10.00",
                "MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00",
            )
        with self.assertRaisesRegex(ValueError, "exceeds"):
            doctor.validate_aws_cost_ceiling(
                "USD: 20.01",
                "MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00",
            )

    def test_gate_a_receipt_binds_exact_owner_cost_posture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project, gate_b=False)

            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "### Gate A — readiness card",
                "### Gate A — owner acceptance record",
                "Cost posture",
                "`MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00`",
            )
            prd_path.write_text(text, encoding="utf-8")

            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"]["cost_posture"] = (
                "MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00"
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertFalse(report["ok"])
        self.assertIn("GATE_A_COST_AUTHORIZATION", codes(report))
        self.assertIn("GATE_A_RECEIPT_MISMATCH", codes(report))
        self.assertEqual(report["authorizations"]["aws"], "NONE")
        self.assertEqual(report["next_prompt"], "STOP")

    def test_gate_b_hash_binds_every_envelope_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Maximum generated tasks",
                "`7`",
            )
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_B_ENVELOPE_HASH", codes(report))
        self.assertIn("GATE_B_RECEIPT_MISMATCH", codes(report))

    def test_gate_b_project_rows_must_exactly_match_document_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Project mode",
                "`brownfield`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_B_PROJECT_DRIFT", codes(report))

    def test_gate_readiness_cards_are_required_for_ready_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project, gate_b=False)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "### Gate A — readiness card",
                "### Gate A — owner acceptance record",
                "Owner and users",
                "`UNASSIGNED`",
            )
            prd_path.write_text(text, encoding="utf-8")

            gate_a_report = doctor.inspect_project(project)

        self.assertIn("GATE_A_READINESS_CARD", codes(gate_a_report))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "### Gate B — readiness card",
                "## 28. Construction envelope",
                "Validation/evidence",
                "`TODO`",
            )
            prd_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("GATE_B_READINESS_CARD", codes(report))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "### Gate B — readiness card",
                "## 28. Construction envelope",
                "Validation/evidence",
                "`TBD`",
            )
            prd_path.write_text(text, encoding="utf-8")

            tbd_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_READINESS_CARD", codes(tbd_report))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Mandatory stop conditions",
                "`UNKNOWN`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")

            unknown_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_ENVELOPE", codes(unknown_report))

    def test_task_ids_must_be_subsets_of_authorized_ids(self) -> None:
        cases = {
            "requirements": {"requirements": "REQ-0001; FR-999"},
            "design": {"design": "DES-0001; ADR-999"},
            "outcome": {"outcome": "Deliver OUT-999 without scope expansion."},
        }
        for label, task_options in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                project = self.copy_project(Path(directory))
                self.approve_project(project)
                self.initialize_task_plan(project, ready_task(**task_options))

                report = doctor.inspect_project(project)

                self.assertIn("TASK_ID_OUTSIDE_AUTH", codes(report))

    def test_external_state_and_paths_use_case_insensitive_authorized_containment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Allowed external-state targets",
                "`TARGETS: AWS:stack/dev`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            self.initialize_task_plan(
                project,
                ready_task("APP/main.py", external_state="aws:STACK/dev/resource"),
            )

            allowed_report = doctor.inspect_project(project)

        self.assertTrue(allowed_report["ok"], allowed_report["diagnostics"])

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Allowed external-state targets",
                "`TARGETS: aws:stack/dev`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            self.initialize_task_plan(project, ready_task(external_state="aws:stack/prod"))

            denied_report = doctor.inspect_project(project)

        self.assertIn("TASK_EXTERNAL_STATE_BOUNDARY", codes(denied_report))

    def test_validation_commands_are_prefix_bound_and_reject_shell_control(self) -> None:
        for command in ("python setup.py", "python -m unittest && curl https://example.test"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                project = self.copy_project(Path(directory))
                self.approve_project(project)
                self.initialize_task_plan(project, ready_task(command=command))

                report = doctor.inspect_project(project)

                self.assertIn("TASK_COMMAND_BOUNDARY", codes(report))

    def test_github_issue_url_must_match_exact_authorized_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            for field, value in {
                "GitHub boundary": "`ISSUES`",
                "GitHub repository, branch, and merge constraints": (
                    "`REPO: Levi-Breedlove/aws-bootstrap; BRANCH: main; MERGE: PROHIBITED`"
                ),
            }.items():
                text = set_table_value(
                    text,
                    "## 28. Construction envelope",
                    "## 29. Gate B owner authorization record",
                    field,
                    value,
                )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            self.initialize_task_plan(
                project,
                ready_task(github_issue="https://github.com/example/other/issues/12"),
            )

            report = doctor.inspect_project(project)

        self.assertIn("TASK_GITHUB_BOUNDARY", codes(report))

    def test_task_boundary_is_exact_and_authorization_must_be_unexpired(self) -> None:
        cases = {
            "substring boundary": (
                "Task boundary",
                "`NOT_DERIVED_FROM_AUTHORIZED_IDS_AND_WRITE_SET`",
            ),
            "expired": (
                "Authorization expiry or completion condition",
                "`Expires at 2020-01-01T00:00:00Z`",
            ),
        }
        for label, (field, value) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                project = self.copy_project(Path(directory))
                self.approve_project(project)
                prd_path = project / "docs/project/PRD.md"
                text = set_table_value(
                    prd_path.read_text(encoding="utf-8"),
                    "## 28. Construction envelope",
                    "## 29. Gate B owner authorization record",
                    field,
                    value,
                )
                prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")

                report = doctor.inspect_project(project)

                self.assertIn("GATE_B_ENVELOPE", codes(report))

    def test_brownfield_baseline_is_deferred_until_gate_a_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            setup = subprocess.run(
                [
                    sys.executable,
                    str(project / "bootstrap.py"),
                    "--target",
                    str(project),
                    "--project-name",
                    "Brownfield Doctor Test",
                    "--region",
                    "us-west-2",
                    "--cost-posture",
                    "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED",
                    "--in-place-template-instance",
                ],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project"].update(
                {
                    "mode": "brownfield",
                    "delivery_profile": "quick-mvp",
                    "effective_risk": "low",
                    "aws_lane": "documentation-only",
                    "brownfield_baseline": "UNASSESSED",
                }
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            prd_path = project / "docs/project/PRD.md"
            text = prd_path.read_text(encoding="utf-8")
            for field, value in {
                "Project mode": "`brownfield`",
                "Delivery profile": "`quick-mvp`",
                "Effective risk": "`low`",
                "AWS lane": "`documentation-only`",
            }.items():
                text = set_table_value(text, "## Document status", "## 1. Workload profile", field, value)
            prd_path.write_text(text, encoding="utf-8")

            blocked_report = doctor.inspect_project(project)

            text = approve_gate_a(prd_path.read_text(encoding="utf-8"))
            text = set_table_value(
                text, "## Document status", "## 1. Workload profile", "Project mode", "`brownfield`"
            )
            prd_path.write_text(text, encoding="utf-8")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["lifecycle"]["gate_a"] = "APPROVED_FOR_DESIGN"
            state["project"]["brownfield_baseline"] = "RECORDED"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            approval_report = doctor.inspect_project(project)

        self.assertTrue(blocked_report["ok"], blocked_report["diagnostics"])
        self.assertIn("BROWNFIELD_PRD_BASELINE", codes(approval_report))
        self.assertIn("BROWNFIELD_PRD_PRESERVATION", codes(approval_report))

    def test_stale_gates_route_to_repair_prompts(self) -> None:
        self.assertEqual(
            doctor.derive_route("STALE", "STALE", True, False, doctor.TaskSummary(), False, "NONE")[1],
            "REQ-10",
        )
        self.assertEqual(
            doctor.derive_route(
                "APPROVED_FOR_DESIGN",
                "STALE",
                True,
                False,
                doctor.TaskSummary(),
                False,
                "NONE",
            )[1],
            "DESIGN-10",
        )

    def test_uninitialized_snapshot_is_still_structurally_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            tasks_path = project / "docs/project/TASKS.md"
            text = tasks_path.read_text(encoding="utf-8").replace(
                "| Maximum workers | `1` |\n", "", 1
            )
            tasks_path.write_text(text, encoding="utf-8")

            report = doctor.inspect_project(project)

        self.assertIn("TASK_SNAPSHOT", codes(report))

    def test_task_write_set_is_bound_to_gate_b_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            self.initialize_task_plan(project, ready_task("infrastructure/**"))

            report = doctor.inspect_project(project)

        self.assertIn("TASK_OUTSIDE_WRITE_BOUNDARY", codes(report))

    def test_paused_resume_requires_git_and_worktree_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Doctor Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "doctor@example.test"], check=True)
            tracked = root / "tracked.txt"
            tracked.write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
            head = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            snapshot = {
                "Baseline commit": head,
                "Last known-green commit": head,
                "Protected dirty paths": "NONE",
            }
            clean_context = doctor.Context(root=root)
            doctor.validate_resume_repository(clean_context, snapshot)
            tracked.write_text("unexpected\n", encoding="utf-8")
            dirty_context = doctor.Context(root=root)
            doctor.validate_resume_repository(dirty_context, snapshot)

        self.assertFalse(clean_context.diagnostics)
        self.assertIn("CONSTRUCTION_WORKTREE_DRIFT", {item.code for item in dirty_context.diagnostics})

    def test_current_gate_b_and_checkpoint_states_require_real_git_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            prd_path = project / "docs/project/PRD.md"
            prd_path.write_text(
                approve_gate_b(approve_gate_a(prd_path.read_text(encoding="utf-8"))),
                encoding="utf-8",
            )
            state_path = project / "bootstrap.yaml"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            current_greenfield_state(state, gate_b=True)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            tasks_path = project / "docs/project/TASKS.md"
            tasks_path.write_text(
                current_task_snapshot(tasks_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )

            no_git_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_GIT_UNVERIFIED", codes(no_git_report))
        self.assertIn("CONSTRUCTION_GIT_UNVERIFIED", codes(no_git_report))

        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            prd_path = project / "docs/project/PRD.md"
            text = set_table_value(
                prd_path.read_text(encoding="utf-8"),
                "## 28. Construction envelope",
                "## 29. Gate B owner authorization record",
                "Authorized baseline commit",
                "`ffffffffffffffffffffffffffffffffffffffff`",
            )
            prd_path.write_text(rebind_gate_b_envelope(text), encoding="utf-8")
            tasks_path = project / "docs/project/TASKS.md"
            tasks_path.write_text(
                set_table_value(
                    tasks_path.read_text(encoding="utf-8"),
                    "## Active execution snapshot",
                    "## Coordinator and worker contract",
                    "Baseline commit",
                    "`ffffffffffffffffffffffffffffffffffffffff`",
                ),
                encoding="utf-8",
            )

            fabricated_report = doctor.inspect_project(project)

        self.assertIn("GATE_B_GIT_UNVERIFIED", codes(fabricated_report))
        self.assertIn("CONSTRUCTION_GIT_UNVERIFIED", codes(fabricated_report))

    def test_real_paused_checkpoint_accepts_ledger_dirt_and_rejects_code_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_project(Path(directory))
            self.approve_project(project)
            self.pause_project_at_real_checkpoint(project)

            paused_report = doctor.inspect_project(project)

            tasks_path = project / "docs/project/TASKS.md"
            tasks_text = tasks_path.read_text(encoding="utf-8")
            prefixed_evidence = tasks_text.replace(
                "- Evidence: `NONE`", "- Evidence: `EV-0001`", 1
            ).replace("Evidence: NONE; External:", "Evidence: EV-00010; External:", 1)
            tasks_path.write_text(prefixed_evidence, encoding="utf-8")
            evidence_prefix_report = doctor.inspect_project(project)
            tasks_path.write_text(tasks_text, encoding="utf-8")

            tasks_path.write_text(
                tasks_text.replace("attempts=0/3", "attempts=0/99", 1),
                encoding="utf-8",
            )
            wrong_attempt_report = doctor.inspect_project(project)
            tasks_path.write_text(tasks_text, encoding="utf-8")

            verify_path = project / "docs/project/VERIFY.md"
            verify_text = verify_path.read_text(encoding="utf-8")
            verify_path.write_text(
                verify_text.replace("CP-0001", "CP-9999")
                + "\n```text\nCP-0001\n```\n",
                encoding="utf-8",
            )
            missing_receipt_report = doctor.inspect_project(project)
            verify_path.write_text(verify_text, encoding="utf-8")

            drift_path = project / "app" / "drift.py"
            drift_path.write_text("DRIFT = True\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(project), "add", "app/drift.py"], check=True
            )
            subprocess.run(
                ["git", "-C", str(project), "commit", "-qm", "unauthorized drift"],
                check=True,
            )
            drift_report = doctor.inspect_project(project)

        self.assertNotIn("CONSTRUCTION_GIT_UNVERIFIED", codes(paused_report))
        self.assertNotIn("CONSTRUCTION_CHECKPOINT_UNVERIFIED", codes(paused_report))
        self.assertNotIn("CONSTRUCTION_WORKTREE_DRIFT", codes(paused_report))
        self.assertIn("CONSTRUCTION_CHECKPOINT_UNVERIFIED", codes(evidence_prefix_report))
        self.assertIn("CONSTRUCTION_CHECKPOINT_UNVERIFIED", codes(wrong_attempt_report))
        self.assertIn("CONSTRUCTION_CHECKPOINT_UNVERIFIED", codes(missing_receipt_report))
        self.assertIn("CONSTRUCTION_GIT_DRIFT", codes(drift_report))

    def test_route_function_handles_construction_modes(self) -> None:
        uninitialized = doctor.TaskSummary(plan_revision=None)
        self.assertEqual(
            doctor.derive_route(
                "APPROVED_FOR_DESIGN",
                "APPROVED_FOR_CONSTRUCTION",
                True,
                True,
                uninitialized,
                True,
                "NONE",
            )[1],
            "TASK-10",
        )
        multiple = doctor.TaskSummary(
            plan_revision="PLAN-0001",
            plan_state="CURRENT",
            statuses={"TASK-001": "READY", "TASK-002": "READY"},
            ready=["TASK-001", "TASK-002"],
        )
        self.assertEqual(
            doctor.derive_route(
                "APPROVED_FOR_DESIGN",
                "APPROVED_FOR_CONSTRUCTION",
                True,
                True,
                multiple,
                True,
                "NONE",
            )[1],
            "BUILD-20",
        )

    def test_plan_state_and_release_state_have_explicit_routes(self) -> None:
        stale = doctor.TaskSummary(plan_revision="PLAN-0001", plan_state="STALE")
        self.assertEqual(
            doctor.derive_route(
                "APPROVED_FOR_DESIGN",
                "APPROVED_FOR_CONSTRUCTION",
                True,
                True,
                stale,
                True,
                "NONE",
            )[1],
            "TASK-10",
        )
        terminal = doctor.TaskSummary(
            plan_revision="PLAN-0001",
            plan_state="CURRENT",
            statuses={"TASK-001": "DONE"},
        )
        expected = {
            "NOT_READY": "RELEASE-10",
            "READY_TO_DEPLOY": "AWS-10",
            "RELEASE_VERIFIED": "STOP",
        }
        for release_state, prompt in expected.items():
            with self.subTest(release_state=release_state):
                self.assertEqual(
                    doctor.derive_route(
                        "APPROVED_FOR_DESIGN",
                        "APPROVED_FOR_CONSTRUCTION",
                        True,
                        True,
                        terminal,
                        True,
                        "NONE",
                        release_state,
                    )[1],
                    prompt,
                )


if __name__ == "__main__":
    unittest.main()
