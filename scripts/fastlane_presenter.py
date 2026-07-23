#!/usr/bin/env python3
"""Render deterministic Fastlane owner updates from machine-derived state."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


class PresentationError(RuntimeError):
    """Raised when state cannot be rendered as a routine owner update."""


STATUS_TEXT = {
    "INTAKE_REQUIRED": "Ready to define the project.",
    "REQUIREMENTS_ANALYSIS": "Requirements are ready for analysis.",
    "REQUIREMENTS_STALE": "Approved requirements need review after a change.",
    "WAITING_GATE_A": "Requirements are ready for your Gate A decision.",
    "DESIGN_REQUIRED": "The technical design is ready to be developed.",
    "DESIGN_STALE": "The technical design must be refreshed.",
    "WAITING_GATE_B": "The design is ready for your Gate B decision.",
    "TASK_PLAN_REQUIRED": "The approved design is ready for task planning.",
    "CONSTRUCTION_SINGLE": "Approved local construction can continue.",
    "CONSTRUCTION_AUTONOMOUS": "Approved local construction is in progress.",
    "RELEASE_REVIEW": "Local construction is ready for release review.",
    "AWS_PREFLIGHT_REQUIRED": "Deployment planning needs current AWS evidence.",
    "RELEASE_VERIFIED": "The approved local workflow is complete.",
    "BLOCKED": "Fastlane stopped at a validation boundary.",
}

ACTION_TEXT = {
    "ANSWER_OPEN_DECISIONS": "Answer the next one to three project questions.",
    "APPROVE_GATE_A": "Review and decide the Gate A requirements receipt.",
    "ENABLE_AWS_CORE": "Enable official AWS Core, then continue the affected AWS step.",
    "APPROVE_GATE_B": "Review and decide the Gate B design and construction receipt.",
    "AUTHORIZE_AWS_OPERATION": "Review the exact AWS authority receipt before any AWS action.",
    "FIX_VALIDATION_FAILURE": "Resolve the listed validation failure, then continue Fastlane.",
    "NONE_CONTINUE_AUTOMATICALLY": "Nothing.",
}

NEXT_TEXT = {
    "INTAKE_REQUIRED": "Codex will record your answers and continue guided definition.",
    "REQUIREMENTS_ANALYSIS": "Codex will analyze the complete requirement set.",
    "REQUIREMENTS_STALE": "Codex will reconcile the changed requirement basis.",
    "WAITING_GATE_A": "After approval, Codex will begin technical design.",
    "DESIGN_REQUIRED": "Codex will compare complete architecture candidates.",
    "DESIGN_STALE": "Codex will refresh design evidence and the proposal.",
    "WAITING_GATE_B": "After approval, Codex will generate tasks and build locally.",
    "TASK_PLAN_REQUIRED": "Codex will generate the dependency-aware task plan.",
    "CONSTRUCTION_SINGLE": "Codex will execute the next ready local task.",
    "CONSTRUCTION_AUTONOMOUS": "Codex will continue approved local tasks.",
    "RELEASE_REVIEW": "Codex will validate evidence and release readiness.",
    "AWS_PREFLIGHT_REQUIRED": "Codex will collect documentation evidence without accessing an AWS account.",
    "RELEASE_VERIFIED": "No further action is required.",
    "BLOCKED": "Codex will resume only after the named blocker is resolved.",
}

COPYABLE_REPLIES = {
    "ANSWER_OPEN_DECISIONS": "Reply with your answers to the questions below.",
    "ENABLE_AWS_CORE": "CONTINUE FASTLANE",
    "FIX_VALIDATION_FAILURE": "CONTINUE FASTLANE",
}


def _interaction(report: Mapping[str, Any]) -> Mapping[str, Any]:
    value = report.get("interaction")
    if not isinstance(value, Mapping):
        raise PresentationError("doctor report is missing interaction state")
    return value


def render_owner_update(
    report: Mapping[str, Any],
    *,
    updated: str = "Nothing.",
    audit: str | None = None,
) -> str:
    """Render one concise non-receipt lifecycle update."""

    interaction = _interaction(report)
    if interaction.get("formal_receipt_required") is True:
        raise PresentationError("formal gate and AWS receipts use canonical receipt renderers")
    stage = str(interaction.get("owner_stage", ""))
    if stage not in {"DEFINE", "DESIGN", "DELIVER"}:
        raise PresentationError("invalid owner stage")
    reason = str(interaction.get("route_reason_code", ""))
    action_kind = str(interaction.get("owner_action_kind", ""))
    if reason not in STATUS_TEXT or reason not in NEXT_TEXT:
        raise PresentationError("unknown route reason code")
    if action_kind not in ACTION_TEXT:
        raise PresentationError("unknown owner action kind")
    required = interaction.get("owner_action_required") is True
    if required == (action_kind == "NONE_CONTINUE_AUTOMATICALLY"):
        raise PresentationError("owner action requirement conflicts with action kind")

    lines = [
        f"FASTLANE · {stage}",
        "",
        f"Status: {STATUS_TEXT[reason]}",
        f"Updated: {updated}",
        f"Need from you: {ACTION_TEXT[action_kind]}",
        f"Next: {NEXT_TEXT[reason]}",
    ]
    if audit:
        lines.append(f"Audit: {audit}")
    reply = COPYABLE_REPLIES.get(action_kind)
    if required and reply:
        lines.extend(("", "Copyable reply:", reply))
    return "\n".join(lines)


def render_prerequisite_update(report: Mapping[str, Any]) -> str:
    """Render one prerequisite action with one complete owner checklist."""

    state = str(report.get("state", ""))
    if state == "PREREQUISITES_READY":
        raise PresentationError("ready prerequisites route to the welcome renderer")
    checklist = report.get("checklist")
    if not isinstance(checklist, Sequence) or isinstance(checklist, (str, bytes)):
        raise PresentationError("prerequisite report is missing its checklist")
    steps = [item for item in checklist if isinstance(item, Mapping)]
    if not steps:
        raise PresentationError("blocked prerequisites require at least one checklist step")
    lines = [
        "FASTLANE · PREREQUISITES",
        "",
        "Status: Required local setup is incomplete.",
        "Updated: Nothing.",
        "Need from you: Complete the checklist below, then send `init template` again.",
        "Next: Codex will verify everything together before asking project questions.",
        "",
        "Checklist:",
    ]
    for index, step in enumerate(steps, start=1):
        label = str(step.get("label", "Required step"))
        lines.append(f"{index}. {label}")
        commands = step.get("commands", [])
        if isinstance(commands, Sequence) and not isinstance(commands, (str, bytes)):
            for command in commands:
                lines.append(f"   `{command}`")
        guide = step.get("guide")
        if guide:
            lines.append(f"   Official guide: {guide}")
        instruction = step.get("instruction")
        if instruction:
            lines.append(f"   {instruction}")
    return "\n".join(lines)
