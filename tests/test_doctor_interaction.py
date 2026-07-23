from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "bootstrap_doctor.py"
SPEC = importlib.util.spec_from_file_location("doctor_interaction_under_test", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
doctor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = doctor
SPEC.loader.exec_module(doctor)


def interaction(
    lifecycle: str,
    prompt: str,
    *,
    errors: bool = False,
    diagnostics: list[str] | None = None,
    design_ready: bool = False,
    aws_ready: bool = False,
) -> dict[str, object]:
    return doctor.derive_interaction(
        lifecycle,
        prompt,
        has_errors=errors,
        diagnostic_codes=diagnostics or [],
        design_aws_core_ready=design_ready,
        aws_execution_planning_ready=aws_ready,
    )


class DoctorInteractionTests(unittest.TestCase):
    def test_template_report_keeps_existing_fields_and_adds_interaction(self) -> None:
        report = doctor.inspect_project(REPOSITORY_ROOT, template_source=True)
        self.assertEqual(report["schema_version"], 2)
        for field in (
            "bootstrap_version",
            "status",
            "classification",
            "ok",
            "lifecycle_state",
            "next_prompt",
            "project",
            "gates",
            "authorizations",
            "tasks",
            "diagnostics",
            "interaction",
        ):
            self.assertIn(field, report)
        self.assertIn(report["interaction"]["owner_stage"], {"DEFINE", "DESIGN", "DELIVER"})
        for task_field in (
            "completed",
            "skipped",
            "blocked",
            "ready_ids",
            "active_ids",
            "blocked_ids",
        ):
            self.assertIn(task_field, report["tasks"])


    def test_gate_modes_are_formal_and_revision_receipts_remain_separate(self) -> None:
        gate_a = interaction("WAITING_GATE_A", "INTAKE-20")
        gate_b = interaction("WAITING_GATE_B", "DESIGN-20", design_ready=True)
        self.assertEqual(gate_a["response_mode"], "GATE_A")
        self.assertEqual(gate_a["owner_action_kind"], "APPROVE_GATE_A")
        self.assertTrue(gate_a["formal_receipt_required"])
        self.assertEqual(gate_b["response_mode"], "GATE_B")
        self.assertEqual(gate_b["owner_action_kind"], "APPROVE_GATE_B")
        self.assertTrue(gate_b["formal_receipt_required"])

    def test_safe_internal_routes_continue_without_owner_action(self) -> None:
        for lifecycle, prompt, stage in (
            ("REQUIREMENTS_ANALYSIS", "REQ-10", "DEFINE"),
            ("DESIGN_REQUIRED", "DESIGN-10", "DESIGN"),
            ("TASK_PLAN_REQUIRED", "TASK-10", "DELIVER"),
            ("CONSTRUCTION_AUTONOMOUS", "BUILD-20", "DELIVER"),
            ("RELEASE_REVIEW", "RELEASE-10", "DELIVER"),
        ):
            with self.subTest(lifecycle=lifecycle):
                result = interaction(lifecycle, prompt)
                self.assertEqual(result["owner_stage"], stage)
                self.assertEqual(result["owner_action_kind"], "NONE_CONTINUE_AUTOMATICALLY")
                self.assertFalse(result["owner_action_required"])
                self.assertTrue(result["automatic_continuation_allowed"])

    def test_accepted_gates_route_immediately_to_safe_internal_work(self) -> None:
        empty = doctor.TaskSummary()
        design_route = doctor.derive_route(
            "APPROVED_FOR_DESIGN",
            "BLOCKED",
            True,
            False,
            empty,
            False,
            "NONE",
        )
        self.assertEqual(design_route, ("DESIGN_REQUIRED", "DESIGN-10"))

        task_route = doctor.derive_route(
            "APPROVED_FOR_DESIGN",
            "APPROVED_FOR_CONSTRUCTION",
            True,
            True,
            empty,
            True,
            "NONE",
        )
        self.assertEqual(task_route, ("TASK_PLAN_REQUIRED", "TASK-10"))

        planned = doctor.TaskSummary(
            plan_state="CURRENT",
            statuses={"TASK-0001": "READY"},
            ready=["TASK-0001"],
        )
        build_route = doctor.derive_route(
            "APPROVED_FOR_DESIGN",
            "APPROVED_FOR_CONSTRUCTION",
            True,
            True,
            planned,
            False,
            "SINGLE_TASK",
        )
        self.assertEqual(build_route, ("CONSTRUCTION_SINGLE", "BUILD-10"))

        for lifecycle, prompt in (design_route, task_route, build_route):
            routed = interaction(lifecycle, prompt, design_ready=True)
            self.assertEqual(
                routed["owner_action_kind"], "NONE_CONTINUE_AUTOMATICALLY"
            )
            self.assertTrue(routed["automatic_continuation_allowed"])


    def test_intake_current_aws_and_validation_each_have_one_stable_action(self) -> None:
        intake = interaction("INTAKE_REQUIRED", "INTAKE-10")
        aws = interaction("AWS_PREFLIGHT_REQUIRED", "AWS-10", aws_ready=True)
        blocked = interaction("BLOCKED", "STOP", errors=True, diagnostics=["PRD_PARSE"])
        aws_blocked = interaction(
            "BLOCKED",
            "STOP",
            errors=True,
            diagnostics=["AWS_CORE_EVIDENCE_REQUIRED"],
        )
        self.assertEqual(intake["owner_action_kind"], "ANSWER_OPEN_DECISIONS")
        self.assertEqual(aws["owner_action_kind"], "AUTHORIZE_AWS_OPERATION")
        self.assertEqual(blocked["owner_action_kind"], "FIX_VALIDATION_FAILURE")
        self.assertEqual(aws_blocked["owner_action_kind"], "ENABLE_AWS_CORE")
        for value in (intake, aws, blocked, aws_blocked):
            self.assertTrue(value["owner_action_required"])

    def test_aws_preflight_collects_evidence_before_requesting_authority(self) -> None:
        result = interaction("AWS_PREFLIGHT_REQUIRED", "AWS-10")
        self.assertEqual(result["response_mode"], "OWNER_UPDATE")
        self.assertEqual(result["state"], "WORKING")
        self.assertEqual(result["owner_action_kind"], "NONE_CONTINUE_AUTOMATICALLY")
        self.assertFalse(result["formal_receipt_required"])
        self.assertTrue(result["automatic_continuation_allowed"])

    def test_aws_core_materiality_and_evidence_are_machine_derived(self) -> None:
        define = interaction("INTAKE_REQUIRED", "INTAKE-10")
        design_missing = interaction("DESIGN_REQUIRED", "DESIGN-10")
        design_current = interaction(
            "DESIGN_REQUIRED", "DESIGN-10", design_ready=True
        )
        aws_missing = interaction("AWS_PREFLIGHT_REQUIRED", "AWS-10")
        self.assertEqual(
            define["aws_core"],
            {"materiality": "NOT_MATERIAL", "evidence_status": "NOT_REQUIRED"},
        )
        self.assertEqual(design_missing["aws_core"]["evidence_status"], "REQUIRED")
        self.assertEqual(design_current["aws_core"]["evidence_status"], "CURRENT")
        self.assertEqual(aws_missing["aws_core"]["evidence_status"], "REQUIRED")

    def test_blocking_ids_are_stable_codes_only_when_blocked(self) -> None:
        blocked = interaction(
            "BLOCKED",
            "STOP",
            errors=True,
            diagnostics=["Z_LAST", "A_FIRST", "A_FIRST"],
        )
        working = interaction(
            "DESIGN_REQUIRED",
            "DESIGN-10",
            diagnostics=["NON_BLOCKING_WARNING"],
        )
        self.assertEqual(blocked["blocking_ids"], ["A_FIRST", "Z_LAST"])
        self.assertEqual(working["blocking_ids"], [])


if __name__ == "__main__":
    unittest.main()
