#!/usr/bin/env python3
"""Read-only structural and lifecycle checks for AWS Codex Fastlane projects.

``bootstrap.yaml`` intentionally uses JSON syntax. JSON is a YAML 1.2 subset,
so the state ledger remains portable while this doctor can use only Python's
standard library and reject ambiguous YAML constructs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


STATE_FILE = "bootstrap.yaml"
MANIFEST_FILE = "bootstrap.manifest.json"
PROJECT_DOCUMENT_DIRECTORY = "docs/project"
BUGFIX_FILE = f"{PROJECT_DOCUMENT_DIRECTORY}/BUGFIX.md"
PRD_FILE = f"{PROJECT_DOCUMENT_DIRECTORY}/PRD.md"
RUNBOOK_FILE = f"{PROJECT_DOCUMENT_DIRECTORY}/RUNBOOK.md"
TASKS_FILE = f"{PROJECT_DOCUMENT_DIRECTORY}/TASKS.md"
VERIFY_FILE = f"{PROJECT_DOCUMENT_DIRECTORY}/VERIFY.md"
PROMPT_FILE = "prompts/CODEX-PROMPTS.md"
REQ_ID = re.compile(r"REQ-\d{4,}")
DES_ID = re.compile(r"DES-\d{4,}")
AUTH_ID = re.compile(r"AUTH-\d{4,}")
PLAN_ID = re.compile(r"PLAN-\d{4,}")
TASK_ID = re.compile(r"TASK-\d+")
RUN_ID = re.compile(r"RUN-\d{4,}")
CHECKPOINT_ID = re.compile(r"CP-\d{4,}")
COST_AMOUNT = r"[1-9]\d*(?:\.\d{1,2})?"
AWS_COST_CEILING = re.compile(
    rf"(?P<currency>[A-Z]{{3}}): (?P<amount>{COST_AMOUNT})"
)
COST_POSTURE_WITH_CAP = re.compile(
    rf"MINIMIZE_TOTAL_COST; HARD_CAP: (?P<currency>[A-Z]{{3}}) (?P<amount>{COST_AMOUNT})"
)
DEFAULT_COST_POSTURE = "MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED"
# Current ISO 4217 List One currency and fund codes, excluding the testing
# code XTS and no-currency code XXX. Keep this equal to bootstrap.py so setup
# and machine-derived authorization enforce the same dependency-free grammar.
ISO_4217_CURRENCY_CODES = frozenset(
    """AED AFN ALL AMD AOA ARS AUD AWG AZN BAM BBD BDT BHD BIF BMD BND BOB BOV BRL BSD BTN BWP BYN BZD CAD CDF CHE CHF CHW CLF CLP CNY COP COU CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD USN UYI UYU UYW UZS VED VES VND VUV WST XAD XAF XAG XAU XBA XBB XBC XBD XCD XCG XDR XOF XPD XPF XPT XSU XUA YER ZAR ZMW ZWG""".split()
)

PROJECT_MODES = {"greenfield", "brownfield"}
DELIVERY_PROFILES = {"quick-mvp", "standard", "high-risk"}
RISK_LEVELS = {"low", "moderate", "high", "critical"}
AWS_LANES = {"documentation-only", "read-only", "fast-dev", "explicit-gate"}
GATE_A_STATES = {
    "BLOCKED",
    "PENDING_OWNER_APPROVAL",
    "APPROVED_FOR_DESIGN",
    "STALE",
}
GATE_B_STATES = {
    "BLOCKED",
    "PENDING_OWNER_APPROVAL",
    "APPROVED_FOR_CONSTRUCTION",
    "STALE",
}
RUN_MODES = {"NONE", "SINGLE_TASK", "AUTONOMOUS"}
RUN_STATES = {"IDLE", "RUNNING", "CHECKPOINTED", "BLOCKED", "COMPLETE"}
BROWNFIELD_STATES = {"UNASSESSED", "NOT_APPLICABLE", "RECORDED", "STALE"}
CANONICAL_PLACEHOLDERS = {
    "My AWS Project",
    "{{AWS_REGION}}",
    "{{COST_POSTURE}}",
    "{{SETUP_METHOD}}",
    "{{SETUP_STATUS}}",
}
MANDATORY_REQUIRED_FILES = {
    ".github/ISSUE_TEMPLATE/aws-vertical-slice.yml",
    ".github/ISSUE_TEMPLATE/bugfix.yml",
    ".github/ISSUE_TEMPLATE/waf-risk.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".gitignore",
    ".agents/skills/build-fastlane/SKILL.md",
    ".agents/skills/launch-fastlane/SKILL.md",
    ".agents/skills/operate-fastlane-aws/SKILL.md",
    ".agents/skills/plan-fastlane/SKILL.md",
    ".codex/agents/fastlane-aws-advisor.toml",
    ".codex/agents/fastlane-evidence-reviewer.toml",
    ".codex/agents/fastlane-requirements-reviewer.toml",
    "AGENTS.md",
    BUGFIX_FILE,
    "LICENSE",
    PRD_FILE,
    "README.md",
    RUNBOOK_FILE,
    "SECURITY.md",
    TASKS_FILE,
    VERIFY_FILE,
    "app/AGENTS.md",
    "bootstrap.manifest.json",
    "bootstrap.py",
    "bootstrap.yaml",
    "docs/adr/0000-template.md",
    "docs/DEPENDENCY-POLICY.md",
    "docs/EXISTING-AWS-CORE.md",
    "docs/SETUP.md",
    "docs/TROUBLESHOOTING.md",
    "docs/WORKFLOW.md",
    "infrastructure/AGENTS.md",
    "prompts/CODEX-PROMPTS.md",
    "scripts/bootstrap_doctor.py",
    "scripts/bootstrap_dependencies.py",
    "scripts/setup_assistant.py",
    "scripts/task_waves.py",
    "tests/AGENTS.md",
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str | None = None
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        result = {"code": self.code, "severity": self.severity, "message": self.message}
        if self.path is not None:
            result["path"] = self.path
        return result


@dataclass
class Context:
    root: Path
    template_source: bool = False
    diagnostics: list[Diagnostic] = field(default_factory=list)
    texts: dict[str, str] = field(default_factory=dict)

    def error(self, code: str, message: str, path: str | None = None) -> None:
        self.diagnostics.append(Diagnostic(code, message, path))

    def warning(self, code: str, message: str, path: str | None = None) -> None:
        self.diagnostics.append(Diagnostic(code, message, path, "WARNING"))

    @property
    def has_errors(self) -> bool:
        return any(item.severity == "ERROR" for item in self.diagnostics)


@dataclass
class TaskSummary:
    plan_revision: str | None = None
    plan_state: str = "UNINITIALIZED"
    statuses: dict[str, str] = field(default_factory=dict)
    ready: list[str] = field(default_factory=list)
    active: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.statuses)

    @property
    def terminal(self) -> bool:
        return bool(self.statuses) and all(
            status in {"DONE", "SKIPPED"} for status in self.statuses.values()
        )


TASK_METADATA_KEYS = (
    "Status",
    "Requirements",
    "Design",
    "Authorization",
    "Depends on",
    "Dependency waivers",
    "Owner",
    "Run ID",
    "Risk",
    "Write set",
    "External state",
    "AWS mode",
    "Attempt budget",
    "Attempts used",
    "Evidence",
    "Blocker",
    "Skip record",
    "GitHub issue",
    "Last checkpoint",
    "Last updated",
)
TASK_HEADER_PATTERN = re.compile(r"^###\s+(TASK-\d+)\s+[—-]\s+(.+?)\s*$", re.MULTILINE)
TASK_META_PATTERN = re.compile(
    rf"^- (?P<key>{'|'.join(re.escape(key) for key in TASK_METADATA_KEYS)}):"
    r"\s*(?P<value>.+?)\s*$",
    re.MULTILINE,
)
TASK_STATUSES = {"BACKLOG", "READY", "IN_PROGRESS", "BLOCKED", "DONE", "SKIPPED"}
TASK_AWS_MODES = {"NONE", "DOCS_ONLY", "READ_ONLY", "MUTATION"}
EVIDENCE_PATTERN = re.compile(
    r"(?:\b(?:EV|EVIDENCE)-[A-Z0-9][A-Z0-9._-]*\b|"
    r"\bVERIFY\.md#[A-Za-z0-9._-]+\b|https?://\S+)",
    re.IGNORECASE,
)
LOCAL_EVIDENCE_ID = re.compile(r"\bEV-\d{4,}\b")
LOCAL_EVIDENCE_LIKE = re.compile(r"\b(?:EV|EVIDENCE)-[A-Za-z0-9._-]+\b", re.IGNORECASE)
TASK_COMPLETION_EVIDENCE_HEADERS = (
    "Evidence ID",
    "Task",
    "Command or observation",
    "Result",
    "Actor",
    "Observed at",
    "Commit / worktree / artifact",
    "Durable source",
    "Status",
)
TASK_COMPLETION_EVIDENCE_STATUSES = {"LOCAL_PASS", "VERIFIED"}
EVIDENCE_PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|TBC|UNKNOWN|UNASSIGNED|PENDING|PLACEHOLDER|"
    r"NOT[ _-]*STARTED|NONE|N/?A)\b|<[^>]+>",
    re.IGNORECASE,
)
UNRESOLVED_TOKEN = re.compile(
    r"(?<![A-Z0-9])(?:TODO|TBD|TBC|UNKNOWN|UNASSIGNED)(?![A-Z0-9])",
    re.IGNORECASE,
)
CHECKPOINT_HEADERS = (
    "Checkpoint",
    "Run",
    "Time",
    "REQ / DES / AUTH",
    "Commit and protected dirty paths",
    "Task outcomes and attempts",
    "Evidence and external actions",
    "Blockers and next safe action",
)
SNAPSHOT_FIELDS = {
    "Task-plan revision",
    "Task-plan state",
    "Requirements revision",
    "Design revision",
    "Construction authorization",
    "Gate B state",
    "Run state",
    "Active run ID",
    "Baseline commit",
    "Protected dirty paths",
    "Coordinator",
    "Maximum workers",
    "Current wave",
    "Last checkpoint",
    "Last known-green commit",
    "Next safe action",
}
SNAPSHOT_RUN_STATES = {"NOT_STARTED", "RUNNING", "PAUSED", "BLOCKED", "COMPLETE"}
GITHUB_BOUNDARIES = {"NONE", "READ_ONLY", "ISSUES", "BRANCH_AND_PR", "MERGE_WHEN_GREEN"}
AWS_BOUNDARIES = {"NONE", "DOCS_ONLY", "READ_ONLY", "MUTATE_LISTED_RESOURCES"}
AWS_DETAIL_FIELDS = {
    "AWS account",
    "AWS role or profile",
    "AWS Region",
    "AWS environment",
    "AWS stack or application",
    "AWS resource allowlist",
    "AWS allowed operations",
    "AWS cost ceiling",
    "AWS prohibited operations",
    "AWS artifact authorization and provenance",
    "AWS rollback boundary",
    "AWS authorization validity",
}
CONTROL_HASH_FILES = {
    "bootstrap.py",
    "scripts/bootstrap_dependencies.py",
    "scripts/bootstrap_doctor.py",
    "scripts/setup_assistant.py",
    "scripts/task_waves.py",
}
COORDINATOR_LEDGER_PATHS = {TASKS_FILE, VERIFY_FILE, STATE_FILE}
AUTHORIZED_ID = re.compile(r"[A-Z][A-Z0-9_]*-\d+")
ID_LIKE = re.compile(r"\b[A-Za-z][A-Za-z0-9_]*-\d+\b")
GITHUB_CONSTRAINT = re.compile(
    r"REPO: (?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+); "
    r"BRANCH: (?P<branch>[A-Za-z0-9._/-]+); MERGE: (?P<merge>ALLOWED|PROHIBITED)"
)
GITHUB_ISSUE_URL = re.compile(
    r"https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/[1-9]\d*"
)
AWS_ENVIRONMENT = re.compile(
    r"ENVIRONMENT: (?P<name>[^;\r\n]+); CLASS: (?P<class>NON_PRODUCTION|PRODUCTION)"
)
AWS_EXACT_ARTIFACT = re.compile(r"EXACT_DIGEST: sha256:[0-9a-f]{64}")
AWS_DERIVED_ARTIFACT = re.compile(
    r"DERIVED_FROM_AUTHORIZED_SOURCE: (?P<rule>[^\r\n]+)"
)
TASK_BOUNDARY_DERIVED = "DERIVED_FROM_AUTHORIZED_IDS_AND_WRITE_SET"
SHELL_CONTROL = re.compile(r"[;&|><`$()\\\r\n]")
NON_HUMAN_APPROVER = re.compile(
    r"(?:^|[^a-z0-9])(?:ai|agent|assistant|automated|automation|bot|chatbot|"
    r"chatgpt|codex|gpt(?:-[0-9]+)?|llm|model|openai|robot|system|workflow|"
    r"service[ _-]*account|pending|placeholder|not[ _-]*started)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)
ENVELOPE_EXPLICIT_FIELDS = {
    "Project mode",
    "Delivery profile and effective risk",
    "Project AWS lane",
    "Authorized outcome",
    "Authorized requirement and design IDs",
    "Authorized baseline commit",
    "Protected dirty paths",
    "In-scope components and environments",
    "Allowed repository write set",
    "Excluded or owner-only write set",
    "Allowed external-state targets",
    "Task boundary",
    "Parallelism rule",
    "Checkpoint cadence",
    "Required checkpoint contents",
    "Local command boundary",
    "GitHub repository, branch, and merge constraints",
    *AWS_DETAIL_FIELDS,
    "Rollback, recovery, and teardown boundary",
    "Mandatory stop conditions",
    "Authorization expiry or completion condition",
}
BROWNFIELD_BASELINE_FIELDS = {
    "Repository and baseline commit",
    "Deployed environments and observed versions",
    "Existing architecture and ownership",
    "Current interfaces, schemas, and consumers",
    "Current data stores and migration constraints",
    "Existing security and compliance controls",
    "Baseline verification commands",
    "Baseline evidence location",
    "Known defects and accepted debt",
    "Repository-to-environment drift",
    "Dirty or user-owned working-tree changes",
    "Protected files and components",
    "Unresolved bootstrap overlay collisions",
}
GATE_A_READINESS_FIELDS = {
    "Outcome",
    "Owner and users",
    "Scope and non-goals",
    "Measurable requirement/acceptance IDs",
    "Data boundary",
    "Identity/security boundary",
    "Environment/Region",
    "Failure/recovery",
    "Cost posture",
    "Intake provenance",
}
GATE_B_READINESS_FIELDS = {
    "Design basis IDs",
    "Architecture/components",
    "Interfaces/data flow",
    "Identity/secrets",
    "Failure/retry/concurrency",
    "Deployment/operations",
    "Validation/evidence",
    "Rollback/recovery/teardown",
    "Brownfield compatibility/migration",
    "Outstanding gaps",
}
AWS_CORE_EVIDENCE_HEADERS = (
    "Phase",
    "Plugin source",
    "Invoked plugin identity",
    "Capability",
    "Retrieved skill",
    "Documentation topic",
    "Source references",
    "Design decision influenced",
    "Observed at",
    "Evidence binding",
    "Observed status",
)
AWS_CORE_EVIDENCE_PHASES = ("BOOT-00", "DESIGN-10", "AWS-10")
AWS_CORE_REQUIRED_CAPABILITY = "retrieve_skill + search_documentation"
AWS_CORE_OFFICIAL_SOURCE = "aws/agent-toolkit-for-aws"
AWS_CORE_OFFICIAL_IDENTITY = "aws-core@agent-toolkit-for-aws"
AWS_CORE_EVIDENCE_STATUSES = {
    "NOT_STARTED",
    "PASS",
    "VERIFIED",
    "FAILED",
    "BLOCKED",
    "STALE",
}


@dataclass
class InspectedTask:
    task_id: str
    title: str
    block: str
    metadata: dict[str, str]
    duplicates: set[str]

    @property
    def status(self) -> str:
        return clean_cell(self.metadata.get("Status", "")).upper()

    @property
    def dependencies(self) -> list[str]:
        raw = clean_cell(self.metadata.get("Depends on", "NONE"))
        return [] if raw in {"", "NONE", "-"} else [item.strip() for item in raw.split(",")]

    @property
    def attempts_used(self) -> int:
        return int(clean_cell(self.metadata["Attempts used"]))

    @property
    def attempt_budget(self) -> int:
        return int(clean_cell(self.metadata["Attempt budget"]))


@dataclass(frozen=True)
class TaskCompletionEvidenceRow:
    evidence_id: str
    task_id: str
    command_or_observation: str
    result: str
    actor: str
    observed_at: str
    commit_worktree_artifact: str
    durable_source: str
    status: str


@dataclass(frozen=True)
class AwsCoreEvidenceRow:
    phase: str
    plugin_source: str
    invoked_plugin_identity: str
    capability: str
    retrieved_skill: str
    documentation_topic: str
    source_references: str
    design_decision_influenced: str
    observed_at: str
    evidence_binding: str
    observed_status: str


@dataclass(frozen=True)
class CheckpointReceiptRow:
    checkpoint_id: str
    run_id: str
    recorded_at: str
    basis: str
    commit_and_dirty: str
    task_outcomes: str
    evidence_and_external: str
    blockers_and_next: str


def without_fenced_code(text: str) -> str:
    """Hide fenced examples while preserving offsets for structural parsing."""

    result: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else "~~~" if stripped.startswith("~~~") else None
        if marker is not None:
            fence = None if fence == marker else marker if fence is None else fence
            result.append(" " * (len(line.rstrip("\r\n"))) + line[len(line.rstrip("\r\n")) :])
        elif fence is None:
            result.append(line)
        else:
            result.append(" " * (len(line.rstrip("\r\n"))) + line[len(line.rstrip("\r\n")) :])
    return "".join(result)


def inspect_task_blocks(text: str) -> list[InspectedTask]:
    structural = without_fenced_code(text)
    matches = list(TASK_HEADER_PATTERN.finditer(structural))
    tasks: list[InspectedTask] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end]
        structural_block = structural[match.start() : end]
        metadata: dict[str, str] = {}
        duplicates: set[str] = set()
        for found in TASK_META_PATTERN.finditer(structural_block):
            key = found.group("key")
            if key in metadata:
                duplicates.add(key)
            metadata[key] = found.group("value")
        tasks.append(InspectedTask(match.group(1), match.group(2).strip(), block, metadata, duplicates))
    return tasks


def inspect_task_sections(block: str) -> tuple[dict[str, str], set[str]]:
    structural = without_fenced_code(block)
    pattern = re.compile(
        r"^####[ \t]+(Outcome|Acceptance criteria|Validation|Execution log)[ \t]*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(structural))
    sections: dict[str, str] = {}
    duplicates: set[str] = set()
    for index, match in enumerate(matches):
        name = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        if name in sections:
            duplicates.add(name)
        sections[name] = block[match.end() : end]
    return sections, duplicates


def split_markdown_table_row(line: str) -> list[str] | None:
    """Split a pipe table row while honoring Markdown escaped pipes."""

    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for character in stripped[1:-1]:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return cells


def parse_task_completion_evidence(text: str) -> list[TaskCompletionEvidenceRow]:
    structural = without_fenced_code(text)
    headings = list(
        re.finditer(r"^## Task completion evidence[ \t]*$", structural, re.MULTILINE)
    )
    if len(headings) != 1:
        raise ValueError("VERIFY.md requires exactly one Task completion evidence section")
    following = re.search(r"^##\s+", structural[headings[0].end() :], re.MULTILINE)
    end = headings[0].end() + following.start() if following else len(structural)
    lines = structural[headings[0].end() : end].splitlines()
    header_indexes = [
        index
        for index, line in enumerate(lines)
        if split_markdown_table_row(line) == list(TASK_COMPLETION_EVIDENCE_HEADERS)
    ]
    if len(header_indexes) != 1:
        raise ValueError("VERIFY.md requires one exact Task completion evidence table")
    header = header_indexes[0]
    separator = split_markdown_table_row(lines[header + 1]) if header + 1 < len(lines) else None
    if (
        separator is None
        or len(separator) != len(TASK_COMPLETION_EVIDENCE_HEADERS)
        or any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in separator)
    ):
        raise ValueError("VERIFY.md Task completion evidence separator is invalid")
    rows: list[TaskCompletionEvidenceRow] = []
    for line in lines[header + 2 :]:
        if not line.strip():
            if rows:
                break
            continue
        cells = split_markdown_table_row(line)
        if cells is None:
            if rows:
                break
            raise ValueError("VERIFY.md Task completion evidence row is missing")
        if len(cells) != len(TASK_COMPLETION_EVIDENCE_HEADERS):
            raise ValueError("VERIFY.md Task completion evidence row must have nine cells")
        row = TaskCompletionEvidenceRow(*(clean_cell(cell) for cell in cells))
        if re.fullmatch(r"EV-\d{4,}", row.evidence_id) is None:
            raise ValueError("VERIFY.md Task completion Evidence ID must be EV-nnnn")
        rows.append(row)
    identifiers = [row.evidence_id for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("VERIFY.md Task completion Evidence IDs must be unique")
    return rows


def parse_aws_core_evidence(text: str) -> dict[str, AwsCoreEvidenceRow]:
    """Parse the one machine-checked AWS Core evidence row for each phase."""

    structural = without_fenced_code(text)
    headings = list(re.finditer(r"^## AWS Core evidence[ \t]*$", structural, re.MULTILINE))
    if len(headings) != 1:
        raise ValueError("VERIFY.md requires exactly one AWS Core evidence section")
    following = re.search(r"^##\s+", structural[headings[0].end() :], re.MULTILINE)
    end = headings[0].end() + following.start() if following else len(structural)
    lines = structural[headings[0].end() : end].splitlines()
    header_indexes = [
        index
        for index, line in enumerate(lines)
        if split_markdown_table_row(line) == list(AWS_CORE_EVIDENCE_HEADERS)
    ]
    if len(header_indexes) != 1:
        raise ValueError("VERIFY.md requires one exact AWS Core evidence table")
    header = header_indexes[0]
    separator = split_markdown_table_row(lines[header + 1]) if header + 1 < len(lines) else None
    if (
        separator is None
        or len(separator) != len(AWS_CORE_EVIDENCE_HEADERS)
        or any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in separator)
    ):
        raise ValueError("VERIFY.md AWS Core evidence separator is invalid")
    rows: dict[str, AwsCoreEvidenceRow] = {}
    for line in lines[header + 2 :]:
        if not line.strip():
            if rows:
                break
            continue
        cells = split_markdown_table_row(line)
        if cells is None:
            if rows:
                break
            raise ValueError("VERIFY.md AWS Core evidence row is missing")
        if len(cells) != len(AWS_CORE_EVIDENCE_HEADERS):
            raise ValueError(
                "VERIFY.md AWS Core evidence row must have "
                f"{len(AWS_CORE_EVIDENCE_HEADERS)} cells"
            )
        row = AwsCoreEvidenceRow(*(clean_cell(cell) for cell in cells))
        if row.phase not in AWS_CORE_EVIDENCE_PHASES:
            raise ValueError(f"VERIFY.md AWS Core evidence has unknown phase {row.phase!r}")
        if row.phase in rows:
            raise ValueError(f"VERIFY.md AWS Core evidence duplicates phase {row.phase}")
        normalized_capability = row.capability.replace("`", "").strip()
        if normalized_capability != AWS_CORE_REQUIRED_CAPABILITY:
            raise ValueError(
                f"{row.phase} AWS Core evidence must require retrieve_skill and search_documentation"
            )
        if row.observed_status not in AWS_CORE_EVIDENCE_STATUSES:
            raise ValueError(f"{row.phase} AWS Core evidence has invalid status")
        rows[row.phase] = row
    missing = sorted(set(AWS_CORE_EVIDENCE_PHASES) - set(rows))
    if missing:
        raise ValueError("VERIFY.md AWS Core evidence is missing phases: " + ", ".join(missing))
    return rows


def aws_core_phase_evidence_issues(
    rows: dict[str, AwsCoreEvidenceRow],
    phase: str,
    *,
    expected_binding: str | None = None,
) -> list[str]:
    """Return deterministic reasons that current official evidence is not ready."""

    issues: list[str] = []
    row = rows.get(phase)
    if row is None or row.observed_status not in {"PASS", "VERIFIED"}:
        return [
            f"{phase} requires fresh PASS evidence from retrieve_skill and search_documentation"
        ]
    if row.plugin_source != AWS_CORE_OFFICIAL_SOURCE:
        issues.append(
            f"{phase} plugin source must be {AWS_CORE_OFFICIAL_SOURCE}"
        )
    if row.invoked_plugin_identity != AWS_CORE_OFFICIAL_IDENTITY:
        issues.append(
            f"{phase} invoked plugin identity must be {AWS_CORE_OFFICIAL_IDENTITY}"
        )
    for label, value in (
        ("Retrieved skill", row.retrieved_skill),
        ("Documentation topic", row.documentation_topic),
        ("Source references", row.source_references),
        ("Design decision influenced", row.design_decision_influenced),
    ):
        try:
            require_explicit_evidence_value(value, f"{phase} {label}")
        except ValueError as exc:
            issues.append(str(exc))
    if not explicit_timestamp(row.observed_at):
        issues.append(f"{phase} Observed at must be ISO 8601 with timezone")
    try:
        binding = require_explicit_evidence_value(
            row.evidence_binding, f"{phase} Evidence binding"
        )
    except ValueError as exc:
        issues.append(str(exc))
    else:
        if expected_binding is not None and binding != clean_cell(expected_binding):
            issues.append(
                f"{phase} Evidence binding does not match current {clean_cell(expected_binding)}"
            )
    return issues


def require_aws_core_phase_evidence(
    ctx: Context,
    rows: dict[str, AwsCoreEvidenceRow],
    phase: str,
    *,
    expected_binding: str | None = None,
) -> None:
    """Block a phase boundary unless both official AWS Core calls are evidenced."""

    for issue in aws_core_phase_evidence_issues(
        rows, phase, expected_binding=expected_binding
    ):
        ctx.error("AWS_CORE_EVIDENCE_REQUIRED", issue, VERIFY_FILE)


def require_explicit_evidence_value(value: str, label: str) -> str:
    cleaned = clean_cell(value)
    if (
        not cleaned
        or any(character in cleaned for character in "\r\n")
        or EVIDENCE_PLACEHOLDER_PATTERN.search(cleaned) is not None
    ):
        raise ValueError(f"{label} is unresolved or placeholder evidence")
    return cleaned


def validate_done_evidence(verify_text: str | None, task: InspectedTask) -> None:
    evidence = clean_cell(task.metadata.get("Evidence", ""))
    references = [match.group(0) for match in EVIDENCE_PATTERN.finditer(evidence)]
    local = [reference for reference in references if re.fullmatch(r"EV-\d{4,}", reference)]
    invalid_local = [
        reference
        for reference in references
        if LOCAL_EVIDENCE_LIKE.fullmatch(reference) is not None
        and re.fullmatch(r"EV-\d{4,}", reference) is None
    ]
    if invalid_local:
        raise ValueError(
            f"{task.task_id}: invalid local Evidence ID: {', '.join(invalid_local)}"
        )
    if not local:
        raise ValueError(f"{task.task_id}: DONE requires at least one local Evidence reference")
    if len(local) != len(set(local)):
        raise ValueError(f"{task.task_id}: local Evidence references must be unique")
    if verify_text is None:
        raise ValueError(f"{task.task_id}: local Evidence requires VERIFY.md")
    rows = parse_task_completion_evidence(verify_text)
    for reference in local:
        matching = [row for row in rows if row.evidence_id == reference]
        if len(matching) != 1:
            raise ValueError(
                f"{task.task_id}: Evidence is not recorded in VERIFY.md: {reference}"
            )
        row = matching[0]
        if row.task_id != task.task_id:
            raise ValueError(
                f"{task.task_id}: Evidence row names the wrong task {row.task_id!r}"
            )
        label = f"{task.task_id} Evidence {row.evidence_id}"
        require_explicit_evidence_value(row.command_or_observation, f"{label} command")
        require_explicit_evidence_value(row.result, f"{label} result")
        require_explicit_evidence_value(row.actor, f"{label} actor")
        if not explicit_timestamp(row.observed_at):
            raise ValueError(f"{label} observed time must be ISO 8601 with timezone")
        material = require_explicit_evidence_value(
            row.commit_worktree_artifact, f"{label} commit/worktree/artifact"
        )
        if (
            re.search(r"\b[0-9a-fA-F]{7,64}\b", material) is None
            and re.search(
                r"\b(?:worktree|artifact)\s*[:=]\s*\S+", material, re.IGNORECASE
            )
            is None
        ):
            raise ValueError(f"{label} requires an explicit commit, worktree, or artifact")
        source = require_explicit_evidence_value(
            row.durable_source, f"{label} durable source"
        )
        candidate = re.sub(
            r"^artifact\s*:\s*", "", source, flags=re.IGNORECASE
        )
        candidate_path = candidate.split("#", 1)[0]
        path_source = bool(
            re.fullmatch(
                r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+(?:#[A-Za-z0-9._-]+)?",
                candidate,
            )
            and ".." not in PurePosixPath(candidate_path).parts
        )
        if (
            re.fullmatch(r"VERIFY\.md#[A-Za-z0-9._-]+", source) is None
            and re.fullmatch(r"git:[0-9a-fA-F]{7,64}", source, re.IGNORECASE) is None
            and re.fullmatch(r"(?:https?|s3)://\S+", source, re.IGNORECASE) is None
            and not path_source
        ):
            raise ValueError(f"{label} durable source is not a local durable reference")
        if row.status not in TASK_COMPLETION_EVIDENCE_STATUSES:
            raise ValueError(f"{label} status must be LOCAL_PASS or VERIFIED")


def parse_task_write_set(value: str, task_id: str) -> list[str]:
    value = clean_cell(value)
    if value in {"", "TODO", "TBD", "UNKNOWN"}:
        raise ValueError(f"{task_id}: unresolved Write set")
    if value == "NONE":
        return []
    result: list[str] = []
    for item in (part.strip() for part in value.split(",")):
        broad = item.endswith("/**")
        base = item[:-3] if broad else item
        pure = PurePosixPath(base)
        if (
            not base
            or pure.is_absolute()
            or "\\" in item
            or any(part.casefold() in {"", ".", "..", ".git"} for part in pure.parts)
            or any(character in base for character in "*?[]{}")
            or pure.as_posix() != base
        ):
            raise ValueError(f"{task_id}: unsafe Write set entry {item!r}")
        result.append(item)
    if len(result) != len({item.casefold() for item in result}):
        raise ValueError(f"{task_id}: duplicate Write set entry")
    return result


def parse_task_external_state(value: str, task_id: str) -> list[str]:
    value = clean_cell(value)
    if value in {"", "TODO", "TBD", "UNKNOWN"}:
        raise ValueError(f"{task_id}: unresolved External state")
    if value == "NONE":
        return []
    values = [item.strip() for item in value.split(",")]
    if any(not item or any(character in item for character in "*?[]{}") for item in values):
        raise ValueError(f"{task_id}: ambiguous External state")
    if len(values) != len({item.casefold() for item in values}):
        raise ValueError(f"{task_id}: duplicate External state entry")
    return values


def task_waiver_rows(text: str) -> dict[str, tuple[str, str, str, str, str]]:
    marker = "### Dependency waiver registry"
    if text.count(marker) != 1:
        raise ValueError("Expected exactly one dependency waiver registry")
    body = text.split(marker, 1)[1].split("\n## ", 1)[0]
    result: dict[str, tuple[str, str, str, str, str]] = {}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [clean_cell(item) for item in split_table_row(line)]
        if len(cells) != 6 or cells[0] in {"Waiver ID", "---", "NONE"}:
            continue
        if re.fullmatch(r"WAIVER-\d+", cells[0]) is None:
            continue
        if cells[0] in result:
            raise ValueError(f"Duplicate waiver ID: {cells[0]}")
        result[cells[0]] = (cells[1], cells[2], cells[3], cells[4], cells[5])
    return result


def declared_task_waivers(task: InspectedTask) -> dict[str, str]:
    raw = clean_cell(task.metadata.get("Dependency waivers", "NONE"))
    if raw in {"", "NONE", "-"}:
        return {}
    result: dict[str, str] = {}
    for entry in raw.split(","):
        pair = [item.strip() for item in entry.split("=", 1)]
        if len(pair) != 2 or re.fullmatch(r"TASK-\d+", pair[0]) is None or re.fullmatch(
            r"WAIVER-\d+", pair[1]
        ) is None:
            raise ValueError(f"{task.task_id}: invalid dependency waiver {entry!r}")
        result[pair[0]] = pair[1]
    return result


def validate_task_records(
    text: str,
    snapshot: dict[str, str],
    verify_text: str | None = None,
) -> tuple[list[InspectedTask], dict[str, InspectedTask], list[str]]:
    tasks = inspect_task_blocks(text)
    by_id: dict[str, InspectedTask] = {}
    errors: list[str] = []
    waivers = task_waiver_rows(text)
    current_req = snapshot.get("Requirements revision", "")
    current_des = snapshot.get("Design revision", "")
    current_auth = snapshot.get("Construction authorization", "")

    for task in tasks:
        if task.task_id in by_id:
            errors.append(f"Duplicate task ID: {task.task_id}")
        by_id[task.task_id] = task
        for key in sorted(task.duplicates):
            errors.append(f"{task.task_id}: duplicate {key} metadata")
        for key in TASK_METADATA_KEYS:
            if key not in task.metadata:
                errors.append(f"{task.task_id}: missing {key} metadata")
        if task.status not in TASK_STATUSES:
            errors.append(f"{task.task_id}: invalid status {task.status!r}")
            continue
        try:
            budget = int(clean_cell(task.metadata.get("Attempt budget", "")))
            used = int(clean_cell(task.metadata.get("Attempts used", "")))
            if budget < 1 or used < 0 or used > budget:
                raise ValueError
        except ValueError:
            errors.append(f"{task.task_id}: invalid attempt counters")
            budget = used = 0
        aws_mode = clean_cell(task.metadata.get("AWS mode", "")).upper()
        if aws_mode not in TASK_AWS_MODES:
            errors.append(f"{task.task_id}: invalid AWS mode {aws_mode!r}")
        for field, expected, pattern in (
            ("Requirements", current_req, REQ_ID),
            ("Design", current_des, DES_ID),
            ("Authorization", current_auth, AUTH_ID),
        ):
            match = pattern.search(clean_cell(task.metadata.get(field, "")))
            if match is None or match.group(0) != expected:
                errors.append(f"{task.task_id}: {field} does not match current execution basis")
        if task.status in {"READY", "IN_PROGRESS"} and snapshot.get("Gate B state") != "APPROVED_FOR_CONSTRUCTION":
            errors.append(f"{task.task_id}: Gate B is not approved for construction")
        if task.status in {"READY", "IN_PROGRESS"} and snapshot.get("Task-plan state") != "CURRENT":
            errors.append(f"{task.task_id}: task plan is not CURRENT")
        try:
            parse_task_write_set(task.metadata.get("Write set", ""), task.task_id)
            parse_task_external_state(task.metadata.get("External state", ""), task.task_id)
        except ValueError as exc:
            errors.append(str(exc))
        run_id = clean_cell(task.metadata.get("Run ID", "NONE"))
        if task.status == "IN_PROGRESS":
            if (
                run_id != snapshot.get("Active run ID")
                or snapshot.get("Run state") != "RUNNING"
                or clean_cell(task.metadata.get("Owner", "")) in {"", "NONE", "UNASSIGNED"}
                or used < 1
                or CHECKPOINT_ID.fullmatch(clean_cell(task.metadata.get("Last checkpoint", ""))) is None
            ):
                errors.append(f"{task.task_id}: invalid IN_PROGRESS claim")
        elif run_id != "NONE":
            errors.append(f"{task.task_id}: non-IN_PROGRESS task must use Run ID NONE")
        if task.status == "READY" and used >= budget:
            errors.append(f"{task.task_id}: attempt budget exhausted")
        if task.status == "DONE":
            evidence = clean_cell(task.metadata.get("Evidence", ""))
            if evidence in {"", "NONE", "TODO"} or EVIDENCE_PATTERN.search(evidence) is None:
                errors.append(f"{task.task_id}: DONE requires Evidence")
            try:
                validate_done_evidence(verify_text, task)
            except ValueError as exc:
                errors.append(str(exc))
        if task.status == "BLOCKED" and clean_cell(task.metadata.get("Blocker", "")) in {"", "NONE", "TODO"}:
            errors.append(f"{task.task_id}: BLOCKED requires a blocker")
        if task.status == "SKIPPED" and clean_cell(task.metadata.get("Skip record", "")) in {"", "NONE", "TODO"}:
            errors.append(f"{task.task_id}: SKIPPED requires a skip record")
        updated = clean_cell(task.metadata.get("Last updated", ""))
        if updated not in {"", "TODO"} and not explicit_timestamp(updated):
            errors.append(f"{task.task_id}: Last updated must be ISO 8601 with timezone")
        try:
            declared = declared_task_waivers(task)
            for dependency_id, waiver_id in declared.items():
                waiver = waivers.get(waiver_id)
                if waiver is None:
                    errors.append(f"{task.task_id}: unknown dependency waiver {waiver_id}")
                elif waiver[0] != dependency_id or waiver[1] != task.task_id:
                    errors.append(f"{task.task_id}: waiver {waiver_id} does not match its task pair")
        except ValueError as exc:
            errors.append(str(exc))
        if task.status in {"READY", "IN_PROGRESS", "DONE"}:
            sections, duplicate_sections = inspect_task_sections(task.block)
            for name in sorted(duplicate_sections):
                errors.append(f"{task.task_id}: duplicate required section #### {name}")
            for name in ("Outcome", "Acceptance criteria", "Validation", "Execution log"):
                if name not in sections:
                    errors.append(f"{task.task_id}: missing required section #### {name}")
            outcome = sections.get("Outcome", "")
            if not outcome.strip() or "TODO" in outcome.upper():
                errors.append(f"{task.task_id}: unresolved Outcome")
            acceptance = sections.get("Acceptance criteria", "")
            if "- [" not in acceptance or "TODO" in acceptance.upper():
                errors.append(f"{task.task_id}: objective acceptance criteria are required")
            validation = sections.get("Validation", "")
            if "```" not in validation or "TODO" in validation.upper():
                errors.append(f"{task.task_id}: executable validation commands are required")
            execution_log = sections.get("Execution log", "")
            normalized_log = execution_log.strip().upper().replace("_", " ")
            if not execution_log.strip() or "TODO" in execution_log.upper():
                errors.append(f"{task.task_id}: execution log must be explicit")
            if task.status == "DONE" and any(
                marker in normalized_log
                for marker in (
                    "TODO",
                    "TBD",
                    "NOT STARTED",
                    "NO EXECUTION HAS BEEN RECORDED",
                )
            ):
                errors.append(f"{task.task_id}: DONE requires an observed Execution log")
            if task.status == "DONE" and "- [ ]" in acceptance:
                errors.append(f"{task.task_id}: DONE has incomplete acceptance criteria")

    for task in tasks:
        for dependency in task.dependencies:
            if dependency not in by_id:
                errors.append(f"{task.task_id}: missing dependency {dependency}")
            elif dependency == task.task_id:
                errors.append(f"{task.task_id}: cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            start = stack.index(task_id)
            raise ValueError("Dependency cycle detected: " + " -> ".join([*stack[start:], task_id]))
        visiting.add(task_id)
        stack.append(task_id)
        for dependency in by_id[task_id].dependencies:
            if dependency in by_id:
                visit(dependency)
        stack.pop()
        visiting.remove(task_id)
        visited.add(task_id)
    try:
        for task_id in sorted(by_id):
            visit(task_id)
    except ValueError as exc:
        errors.append(str(exc))

    for waiver_id, waiver in waivers.items():
        skipped_id, applies_to, authority, rationale, recorded_at = waiver
        if skipped_id not in by_id or applies_to not in by_id:
            errors.append(f"{waiver_id}: references an unknown task")
            continue
        if by_id[skipped_id].status != "SKIPPED":
            errors.append(f"{waiver_id}: dependency is not SKIPPED")
        if skipped_id not in by_id[applies_to].dependencies:
            errors.append(f"{waiver_id}: skipped task is not a dependency")
        authority_is_current = bool(
            re.fullmatch(rf"{re.escape(current_auth)}(?:\s+clause\s+[A-Za-z0-9._:-]+)?", authority)
            or re.fullmatch(r"OWNER-DECISION-\d+", authority)
        )
        if not authority_is_current:
            errors.append(f"{waiver_id}: authority is not an exact current authority")
        if not explicit_value(rationale) or EVIDENCE_PATTERN.search(rationale) is None:
            errors.append(f"{waiver_id}: missing rationale or preserved evidence")
        if not explicit_timestamp(recorded_at):
            errors.append(f"{waiver_id}: Recorded at must be ISO 8601 with timezone")

    ready: list[str] = []
    for task in tasks:
        if task.status != "READY":
            continue
        declared = declared_task_waivers(task)
        satisfied = True
        for dependency_id in task.dependencies:
            dependency = by_id.get(dependency_id)
            if dependency is None:
                satisfied = False
            elif dependency.status == "DONE":
                continue
            elif dependency.status == "SKIPPED":
                waiver_id = declared.get(dependency_id)
                waiver = waivers.get(waiver_id or "")
                if waiver is None or waiver[0] != dependency_id or waiver[1] != task.task_id:
                    satisfied = False
                else:
                    authority, rationale, recorded_at = waiver[2], waiver[3], waiver[4]
                    current_auth_match = re.search(
                        rf"(?<![A-Z0-9-]){re.escape(current_auth)}(?!\d)", authority
                    )
                    owner_match = re.search(r"\bOWNER-DECISION-\d+\b", authority)
                    if (
                        (current_auth_match is None and owner_match is None)
                        or unresolved(rationale)
                        or rationale == "NONE"
                        or unresolved(recorded_at)
                    ):
                        satisfied = False
            else:
                satisfied = False
        if satisfied:
            ready.append(task.task_id)
    if errors:
        raise ValueError("\n".join(errors))
    return tasks, by_id, ready


def clean_cell(value: Any) -> str:
    text = str(value).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text


def unresolved(value: str) -> bool:
    cleaned = clean_cell(value)
    return (
        not cleaned
        or UNRESOLVED_TOKEN.search(cleaned) is not None
        or "<" in cleaned
        or ">" in cleaned
    )


def explicit_value(value: str, *, allow_none: bool = False) -> bool:
    cleaned = clean_cell(value)
    if unresolved(cleaned):
        return False
    return allow_none or cleaned not in {"NONE", "NOT_RECORDED", "UNASSIGNED"}


def parse_positive_cost(
    value: str,
    pattern: re.Pattern[str],
    field_name: str,
) -> tuple[str, Decimal]:
    """Parse one finite positive ISO-currency amount in canonical form."""

    cleaned = clean_cell(value)
    match = pattern.fullmatch(cleaned)
    if match is None:
        raise ValueError(
            f"{field_name} must use a finite positive currency amount such as "
            "USD: 20.00"
        )
    try:
        amount = Decimal(match.group("amount"))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} amount is invalid") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"{field_name} amount must be finite and positive")
    currency = match.group("currency")
    if currency not in ISO_4217_CURRENCY_CODES:
        raise ValueError(
            f"{field_name} currency must be a current ISO 4217 List One code"
        )
    return currency, amount


def parse_cost_posture(value: str) -> tuple[str, Decimal] | None:
    """Return an optional owner hard cap from the canonical Gate A posture."""

    cleaned = clean_cell(value)
    if cleaned == DEFAULT_COST_POSTURE:
        return None
    match = COST_POSTURE_WITH_CAP.fullmatch(cleaned)
    if match is None:
        raise ValueError(
            "Cost posture must be MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED or "
            "MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00"
        )
    return parse_positive_cost(
        f"{match.group('currency')}: {match.group('amount')}",
        AWS_COST_CEILING,
        "Cost posture hard cap",
    )


def validate_aws_cost_ceiling(value: str, cost_posture: str) -> None:
    """Require a finite mutation ceiling and honor any Gate A owner cap."""

    currency, amount = parse_positive_cost(
        value,
        AWS_COST_CEILING,
        "AWS cost ceiling",
    )
    owner_cap = parse_cost_posture(cost_posture)
    if owner_cap is None:
        return
    cap_currency, cap_amount = owner_cap
    if currency != cap_currency:
        raise ValueError(
            "AWS cost ceiling currency must match the Gate A owner hard cap"
        )
    if amount > cap_amount:
        raise ValueError("AWS cost ceiling exceeds the Gate A owner hard cap")


def explicit_timestamp(value: str) -> bool:
    cleaned = clean_cell(value)
    if unresolved(cleaned):
        return False
    candidate = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def explicit_human_approver(value: str) -> bool:
    """Require an explicit owner identity that is not an agent or automation."""

    cleaned = clean_cell(value)
    return explicit_value(cleaned) and NON_HUMAN_APPROVER.search(cleaned) is None


def parse_exact_id_list(value: str, pattern: re.Pattern[str], field_name: str) -> list[str]:
    cleaned = clean_cell(value)
    if cleaned == "NONE":
        return []
    if unresolved(cleaned):
        raise ValueError(f"{field_name} is unresolved")
    items = [item.strip() for item in cleaned.split(",")]
    if any(pattern.fullmatch(item) is None for item in items):
        raise ValueError(f"{field_name} must contain comma-separated {pattern.pattern} IDs or NONE")
    if len(items) != len(set(items)):
        raise ValueError(f"{field_name} contains duplicate IDs")
    return items


def markdown_tables(text: str) -> list[list[list[str]]]:
    """Return simple Markdown tables without evaluating any project content."""

    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    structural = without_fenced_code(text)
    for raw_line, structural_line in zip(text.splitlines(), structural.splitlines()):
        if structural_line.strip().startswith("|"):
            current.append([clean_cell(cell) for cell in split_table_row(raw_line)])
        elif current:
            if len(current) >= 3:
                tables.append(current)
            current = []
    if len(current) >= 3:
        tables.append(current)
    return tables


def canonical_envelope_sha256(prd_text: str) -> str:
    heading = "## 28. Construction envelope"
    structural = without_fenced_code(prd_text)
    matches = list(
        re.finditer(rf"^{re.escape(heading)}[ \t]*$", structural, re.MULTILINE)
    )
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one heading {heading!r}")
    lines = prd_text[matches[0].end() :].splitlines()
    structural_lines = structural[matches[0].end() :].splitlines()
    start = next(
        (index for index, line in enumerate(structural_lines) if line.startswith("|")),
        None,
    )
    if start is None:
        raise ValueError("Construction envelope Markdown table is missing")
    table_lines: list[str] = []
    for line, structural_line in zip(lines[start:], structural_lines[start:]):
        if not structural_line.startswith("|"):
            break
        table_lines.append(line.rstrip())
    if len(table_lines) < 3:
        raise ValueError("Construction envelope Markdown table is malformed")
    payload = ("\n".join(table_lines) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def parse_authorized_ids(value: str) -> list[str]:
    cleaned = clean_cell(value)
    match = re.fullmatch(
        r"REQ: (?P<req>REQ-\d{4,}); DES: (?P<des>DES-\d{4,}); SCOPE_IDS: (?P<scope>.+)",
        cleaned,
    )
    if match is None:
        raise ValueError(
            "Authorized requirement and design IDs must use "
            "REQ: REQ-0001; DES: DES-0001; SCOPE_IDS: FR-001, SEC-001"
        )
    scope = parse_exact_id_list(
        match.group("scope"), AUTHORIZED_ID, "Authorized SCOPE_IDS"
    )
    if not scope:
        raise ValueError("Authorized SCOPE_IDS cannot be NONE")
    ids = [match.group("req"), match.group("des"), *scope]
    if len(ids) != len(set(ids)):
        raise ValueError("Authorized requirement and design IDs contain duplicates")
    return ids


def parse_envelope_paths(value: str, label: str, *, allow_none: bool) -> list[str]:
    cleaned = clean_cell(value)
    if allow_none and cleaned == "NONE":
        return []
    prefix = "PATHS: "
    if not cleaned.startswith(prefix):
        raise ValueError(f"{label} must use PATHS: path; path" + (" or NONE" if allow_none else ""))
    items = [item.strip() for item in cleaned[len(prefix) :].split(";")]
    return parse_task_write_set(",".join(items), label)


def parse_envelope_targets(value: str) -> list[str]:
    cleaned = clean_cell(value)
    if cleaned == "NONE":
        return []
    prefix = "TARGETS: "
    if not cleaned.startswith(prefix):
        raise ValueError("Allowed external-state targets must use TARGETS: target; target or NONE")
    items = [item.strip() for item in cleaned[len(prefix) :].split(";")]
    return parse_task_external_state(",".join(items), "Gate B envelope")


def parse_task_boundary(value: str) -> tuple[str, set[str]]:
    cleaned = clean_cell(value)
    if cleaned == TASK_BOUNDARY_DERIVED:
        return "DERIVED", set()
    prefix = "TASK_IDS: "
    if not cleaned.startswith(prefix):
        raise ValueError(
            "Task boundary must be exactly DERIVED_FROM_AUTHORIZED_IDS_AND_WRITE_SET "
            "or TASK_IDS: TASK-001, TASK-002"
        )
    values = [item.strip() for item in cleaned[len(prefix) :].split(",")]
    if not values or any(TASK_ID.fullmatch(item) is None for item in values):
        raise ValueError("TASK_IDS must contain only comma-separated TASK IDs")
    if len(values) != len(set(values)):
        raise ValueError("TASK_IDS contains duplicates")
    return "EXPLICIT", set(values)


def parse_command_prefixes(value: str) -> list[str]:
    cleaned = clean_cell(value)
    prefix = "ALLOW_PREFIXES: "
    if not cleaned.startswith(prefix):
        raise ValueError("Local command boundary must use ALLOW_PREFIXES: prefix; prefix")
    values = [item.strip() for item in cleaned[len(prefix) :].split(";")]
    if not values or any(not item for item in values):
        raise ValueError("Local command boundary contains an empty prefix")
    if any(SHELL_CONTROL.search(item) or item.startswith(("-", "#")) for item in values):
        raise ValueError("Local command prefixes cannot contain shell-control syntax")
    if len(values) != len(set(values)):
        raise ValueError("Local command boundary contains duplicate prefixes")
    return values


def validation_commands(section: str, task_id: str) -> list[str]:
    fences = re.findall(r"^```[^\r\n]*\r?\n(.*?)^```\s*$", section, re.MULTILINE | re.DOTALL)
    commands: list[str] = []
    for body in fences:
        for raw_line in body.splitlines():
            command = raw_line.strip()
            if not command or command.startswith("#"):
                continue
            if command.startswith("$ "):
                command = command[2:].strip()
            if SHELL_CONTROL.search(command):
                raise ValueError(f"{task_id}: Validation command contains shell-control syntax")
            commands.append(command)
    if not commands:
        raise ValueError(f"{task_id}: Validation requires at least one fenced command")
    return commands


def command_matches_prefix(command: str, prefix: str) -> bool:
    return command == prefix or command.startswith(prefix + " ")


def parse_github_constraints(value: str, boundary: str) -> str | None:
    cleaned = clean_cell(value)
    if boundary in {"NONE", "READ_ONLY"}:
        if cleaned != "NONE":
            raise ValueError(f"GitHub boundary {boundary} requires constraints NONE")
        return None
    match = GITHUB_CONSTRAINT.fullmatch(cleaned)
    if match is None:
        raise ValueError(
            "GitHub write constraints must be exactly "
            "REPO: owner/name; BRANCH: branch; MERGE: ALLOWED|PROHIBITED"
        )
    branch = match.group("branch")
    if (
        branch.startswith(("/", "-"))
        or branch.endswith("/")
        or "//" in branch
        or ".." in branch
        or "@{" in branch
    ):
        raise ValueError("GitHub branch constraint is unsafe")
    merge = match.group("merge")
    expected_merge = "ALLOWED" if boundary == "MERGE_WHEN_GREEN" else "PROHIBITED"
    if merge != expected_merge:
        raise ValueError(f"GitHub boundary {boundary} requires MERGE: {expected_merge}")
    return match.group("repo")


def parse_future_expiry(value: str) -> datetime:
    cleaned = clean_cell(value)
    match = re.fullmatch(
        r"Expires at (?P<timestamp>[^\s;]+); earlier completion: (?P<condition>[^\r\n]+)",
        cleaned,
    )
    if match is None:
        raise ValueError(
            "Authorization expiry must use Expires at <ISO8601>; earlier completion: <exact condition>"
        )
    if not explicit_value(match.group("condition"), allow_none=False):
        raise ValueError("Authorization earlier-completion condition must be explicit")
    candidate = match.group("timestamp")
    normalized = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
    try:
        expires_at = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("Authorization expiry timestamp is not ISO 8601") from exc
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        raise ValueError("Authorization expiry timestamp must include a timezone")
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("Construction authorization is expired")
    return expires_at


def parse_aws_environment(value: str) -> tuple[str, str]:
    cleaned = clean_cell(value)
    match = AWS_ENVIRONMENT.fullmatch(cleaned)
    if match is None or not explicit_value(match.group("name")):
        raise ValueError(
            "AWS environment must use "
            "ENVIRONMENT: <exact>; CLASS: NON_PRODUCTION|PRODUCTION"
        )
    return match.group("name"), match.group("class")


def validate_aws_artifact(value: str, baseline: str) -> None:
    cleaned = clean_cell(value)
    if AWS_EXACT_ARTIFACT.fullmatch(cleaned) is not None:
        return
    match = AWS_DERIVED_ARTIFACT.fullmatch(cleaned)
    if match is None:
        raise ValueError(
            "AWS artifact authorization must use EXACT_DIGEST: sha256:<64 lowercase> "
            "or DERIVED_FROM_AUTHORIZED_SOURCE: <deterministic rule>"
        )
    rule = match.group("rule")
    if (
        not explicit_value(rule)
        or baseline not in rule
        or "sha256" not in rule.casefold()
    ):
        raise ValueError(
            "Derived AWS artifact authorization must bind the authorized baseline "
            "commit and an exact SHA-256 derivation rule"
        )


def validate_relative_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    pure = PurePosixPath(value)
    if pure.is_absolute() or "\\" in value or any(part in {"", ".", ".."} for part in pure.parts):
        return None
    return value


def has_symlink_component(root: Path, relative: str) -> bool:
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def safe_read_text(ctx: Context, relative: str, *, required: bool = True) -> str | None:
    if validate_relative_path(relative) is None:
        ctx.error("MANIFEST_UNSAFE_PATH", f"Unsafe project-relative path: {relative!r}")
        return None
    if has_symlink_component(ctx.root, relative):
        ctx.error("REQUIRED_FILE_SYMLINK", "Required path contains a symbolic link", relative)
        return None
    path = ctx.root / relative
    if not path.exists():
        if required:
            ctx.error("REQUIRED_FILE_MISSING", "Required file is missing", relative)
        return None
    if not path.is_file():
        ctx.error("REQUIRED_FILE_NOT_REGULAR", "Required path is not a regular file", relative)
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        ctx.error("REQUIRED_FILE_UNREADABLE", f"Unable to read UTF-8 text: {exc}", relative)
        return None
    ctx.texts[relative] = text
    return text


def load_json_document(ctx: Context, relative: str, code: str) -> dict[str, Any] | None:
    text = safe_read_text(ctx, relative)
    if text is None:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        ctx.error(code, f"Expected JSON-compatible YAML: {exc}", relative)
        return None
    if not isinstance(value, dict):
        ctx.error(code, "Top-level value must be an object", relative)
        return None
    return value


def split_table_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def table_after_heading(text: str, heading: str) -> dict[str, str]:
    structural = without_fenced_code(text)
    matches = list(
        re.finditer(rf"^{re.escape(heading)}[ \t]*$", structural, re.MULTILINE)
    )
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one heading {heading!r}; found {len(matches)}")
    lines = text[matches[0].end() :].splitlines()
    structural_lines = structural[matches[0].end() :].splitlines()
    start = next(
        (
            index
            for index, line in enumerate(structural_lines)
            if line.strip().startswith("|")
        ),
        None,
    )
    if start is None:
        raise ValueError(f"No Markdown table after {heading!r}")
    table_lines: list[str] = []
    for line, structural_line in zip(lines[start:], structural_lines[start:]):
        if not structural_line.strip().startswith("|"):
            break
        table_lines.append(line)
    if len(table_lines) < 3:
        raise ValueError(f"Malformed Markdown table after {heading!r}")
    result: dict[str, str] = {}
    for line in table_lines[2:]:
        cells = split_table_row(line)
        if len(cells) < 2:
            continue
        key = clean_cell(cells[0])
        if key in result:
            raise ValueError(f"Duplicate field {key!r} after {heading!r}")
        result[key] = clean_cell(cells[1])
    return result


def marked_receipt(text: str, gate: str) -> str:
    start = f"<!-- bootstrap:{gate}-receipt:start -->"
    end = f"<!-- bootstrap:{gate}-receipt:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Expected exactly one marked {gate} receipt block")
    body = text.split(start, 1)[1].split(end, 1)[0].strip()
    match = re.fullmatch(r"```text\s*\n(?P<receipt>.*?)\n```", body, re.DOTALL)
    if match is None:
        raise ValueError(f"Marked {gate} receipt must contain one text fence")
    return match.group("receipt").replace("\r\n", "\n").strip()


def exact_selection(
    ctx: Context,
    value: str,
    allowed: set[str],
    code: str,
    field_name: str,
    *,
    allow_unselected: bool,
) -> str | None:
    cleaned = clean_cell(value)
    if cleaned in allowed:
        return cleaned
    if allow_unselected and any(item in cleaned for item in allowed):
        return None
    ctx.error(code, f"{field_name} must be exactly one of {sorted(allowed)}", PRD_FILE)
    return None


def validate_manifest(ctx: Context, manifest: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version",
        "bootstrap_version",
        "python_requires",
        "required_files",
        "canonical_prompt_ids",
        "template_placeholders",
        "control_sha256",
        "source_sha256",
    }
    if set(manifest) != expected_fields:
        ctx.error(
            "MANIFEST_SCHEMA",
            f"Manifest fields must be exactly {sorted(expected_fields)}",
            MANIFEST_FILE,
        )
    if manifest.get("schema_version") != 1:
        ctx.error("MANIFEST_SCHEMA", "Unsupported manifest schema_version", MANIFEST_FILE)
    version = manifest.get("bootstrap_version")
    if not isinstance(version, str) or re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        ctx.error("MANIFEST_VERSION", "bootstrap_version must be semantic version text", MANIFEST_FILE)

    files = manifest.get("required_files")
    if not isinstance(files, list):
        ctx.error("MANIFEST_REQUIRED_FILES", "required_files must be an array", MANIFEST_FILE)
        return
    seen: set[str] = set()
    folded: set[str] = set()
    for item in files:
        relative = validate_relative_path(item)
        if relative is None:
            ctx.error("MANIFEST_UNSAFE_PATH", f"Unsafe required_files entry: {item!r}", MANIFEST_FILE)
            continue
        if relative in seen or relative.casefold() in folded:
            ctx.error("MANIFEST_DUPLICATE_PATH", f"Duplicate required path: {relative}", MANIFEST_FILE)
            continue
        seen.add(relative)
        folded.add(relative.casefold())
        safe_read_text(ctx, relative)
    missing_mandatory = sorted(MANDATORY_REQUIRED_FILES - seen)
    if missing_mandatory:
        ctx.error(
            "MANIFEST_REQUIRED_BASELINE",
            "Manifest omits mandatory control files: " + ", ".join(missing_mandatory),
            MANIFEST_FILE,
        )
    if set(manifest.get("template_placeholders", [])) != CANONICAL_PLACEHOLDERS:
        ctx.error(
            "MANIFEST_PLACEHOLDERS",
            "template_placeholders must contain the canonical render tokens",
            MANIFEST_FILE,
        )
    source_hashes = manifest.get("source_sha256")
    expected_source_paths = seen - {MANIFEST_FILE}
    if not isinstance(source_hashes, dict) or set(source_hashes) != expected_source_paths:
        ctx.error(
            "MANIFEST_SOURCE_HASHES",
            "source_sha256 must map every required file except the manifest itself",
            MANIFEST_FILE,
        )
    else:
        for relative in sorted(expected_source_paths):
            expected = source_hashes.get(relative)
            if (
                not isinstance(expected, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected) is None
            ):
                ctx.error(
                    "MANIFEST_SOURCE_HASHES",
                    f"Invalid source SHA-256 for {relative}",
                    MANIFEST_FILE,
                )
                continue
            if ctx.template_source and not has_symlink_component(ctx.root, relative):
                try:
                    actual = hashlib.sha256((ctx.root / relative).read_bytes()).hexdigest()
                except OSError as exc:
                    ctx.error(
                        "MANIFEST_SOURCE_HASHES",
                        f"Unable to hash template source: {exc}",
                        relative,
                    )
                    continue
                if actual != expected:
                    ctx.error(
                        "MANIFEST_SOURCE_HASHES",
                        f"Template source hash mismatch for {relative}",
                        relative,
                    )
    controls = manifest.get("control_sha256")
    if not isinstance(controls, dict) or set(controls) != CONTROL_HASH_FILES:
        ctx.error(
            "MANIFEST_CONTROL_HASHES",
            "control_sha256 must map exactly the trusted runtime control files",
            MANIFEST_FILE,
        )
        return
    for relative in sorted(CONTROL_HASH_FILES):
        expected = controls.get(relative)
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            ctx.error(
                "MANIFEST_CONTROL_HASHES",
                f"Invalid SHA-256 for trusted control {relative}",
                MANIFEST_FILE,
            )
            continue
        if has_symlink_component(ctx.root, relative):
            continue
        try:
            actual = hashlib.sha256((ctx.root / relative).read_bytes()).hexdigest()
        except OSError as exc:
            ctx.error(
                "CONTROL_HASH_UNREADABLE",
                f"Unable to hash trusted control: {exc}",
                relative,
            )
            continue
        if actual != expected:
            ctx.error(
                "CONTROL_HASH_MISMATCH",
                f"Trusted runtime control hash mismatch: expected {expected}, observed {actual}",
                relative,
            )


def validate_prompt_pack(ctx: Context, manifest: dict[str, Any], state: dict[str, Any]) -> None:
    text = ctx.texts.get(PROMPT_FILE) or safe_read_text(ctx, PROMPT_FILE)
    if text is None:
        return
    version_match = re.search(r"^\*\*Pack version:\*\*\s*(\d+\.\d+\.\d+)\s*$", text, re.MULTILINE)
    if version_match is None:
        ctx.error("PROMPT_VERSION_MISSING", "Prompt pack version is missing", PROMPT_FILE)
    else:
        versions = {
            str(manifest.get("bootstrap_version")),
            str(state.get("bootstrap_version")),
            version_match.group(1),
        }
        if len(versions) != 1:
            ctx.error("BOOTSTRAP_VERSION_DRIFT", f"Version values disagree: {sorted(versions)}")

    expected = manifest.get("canonical_prompt_ids")
    actual = re.findall(r"^##\s+([A-Z]+-\d{2})\s+", text, re.MULTILINE)
    if not isinstance(expected, list) or not all(isinstance(item, str) for item in expected):
        ctx.error("PROMPT_IDS_MANIFEST", "canonical_prompt_ids must be an array of strings", MANIFEST_FILE)
    elif actual != expected:
        ctx.error("PROMPT_IDS_DRIFT", f"Prompt headings do not match manifest order: {actual}", PROMPT_FILE)
    elif len(actual) != len(set(actual)):
        ctx.error("PROMPT_IDS_DUPLICATE", "Canonical prompt IDs must be unique", PROMPT_FILE)


def validate_placeholders(ctx: Context) -> None:
    if ctx.template_source:
        return
    excluded = {MANIFEST_FILE, "bootstrap.py", "scripts/bootstrap_doctor.py"}
    for relative, text in sorted(ctx.texts.items()):
        if relative in excluded or relative.startswith("tests/"):
            continue
        for token in sorted(CANONICAL_PLACEHOLDERS):
            if token in text:
                ctx.error(
                    "PLACEHOLDER_UNRESOLVED",
                    f"Unresolved bootstrap placeholder {token!r}",
                    relative,
                )


def validate_state_schema(ctx: Context, state: dict[str, Any]) -> bool:
    expected_top = {
        "schema_version",
        "bootstrap_version",
        "setup",
        "project",
        "lifecycle",
        "execution",
    }
    if set(state) != expected_top:
        ctx.error("STATE_SCHEMA", f"State keys must be exactly {sorted(expected_top)}", STATE_FILE)
    if state.get("schema_version") != 1:
        ctx.error("STATE_SCHEMA", "Unsupported state schema_version", STATE_FILE)

    setup = state.get("setup")
    project = state.get("project")
    lifecycle = state.get("lifecycle")
    execution = state.get("execution")
    if (
        not isinstance(setup, dict)
        or not isinstance(project, dict)
        or not isinstance(lifecycle, dict)
        or not isinstance(execution, dict)
    ):
        ctx.error(
            "STATE_SCHEMA",
            "setup, project, lifecycle, and execution must be objects",
            STATE_FILE,
        )
        return False

    setup_expected = {"status", "method"}
    project_expected = {
        "name",
        "region",
        "cost_posture",
        "mode",
        "delivery_profile",
        "effective_risk",
        "aws_lane",
        "brownfield_baseline",
    }
    lifecycle_expected = {
        "requirements_revision",
        "design_revision",
        "construction_authorization",
        "gate_a",
        "gate_b",
    }
    execution_expected = {
        "plan_revision",
        "plan_state",
        "run_id",
        "coordinator",
        "mode",
        "state",
        "basis",
        "active_tasks",
        "attempts",
        "last_checkpoint",
    }
    for name, value, expected in (
        ("setup", setup, setup_expected),
        ("project", project, project_expected),
        ("lifecycle", lifecycle, lifecycle_expected),
        ("execution", execution, execution_expected),
    ):
        if set(value) != expected:
            ctx.error("STATE_SCHEMA", f"{name} keys must be exactly {sorted(expected)}", STATE_FILE)

    setup_status = setup.get("status")
    setup_method = setup.get("method")
    allowed_setup_statuses = {"UNCONFIGURED_TEMPLATE", "CONFIGURED"}
    if ctx.template_source:
        allowed_setup_statuses.add("{{SETUP_STATUS}}")
    if setup_status not in allowed_setup_statuses:
        ctx.error("STATE_SETUP", "Invalid setup.status", STATE_FILE)
    allowed_methods = {"IN_PLACE", "EXTERNAL_COPY"}
    if ctx.template_source:
        allowed_methods.add("{{SETUP_METHOD}}")
    if setup_method not in allowed_methods:
        ctx.error("STATE_SETUP", "Invalid setup.method", STATE_FILE)
    for key in ("name", "region", "cost_posture"):
        value = project.get(key)
        if not isinstance(value, str) or not value.strip():
            ctx.error("PROJECT_IDENTITY", f"project.{key} must be non-empty text", STATE_FILE)
    cost_posture = project.get("cost_posture")
    if isinstance(cost_posture, str) and not (
        ctx.template_source and cost_posture == "{{COST_POSTURE}}"
    ):
        try:
            parse_cost_posture(cost_posture)
        except ValueError as exc:
            ctx.error("PROJECT_COST_POSTURE", str(exc), STATE_FILE)

    for key, allowed in (
        ("mode", PROJECT_MODES),
        ("delivery_profile", DELIVERY_PROFILES),
        ("effective_risk", RISK_LEVELS),
        ("aws_lane", AWS_LANES),
    ):
        value = project.get(key)
        if value is not None and (not isinstance(value, str) or value not in allowed):
            ctx.error("PROJECT_VOCABULARY", f"Invalid project.{key}: {value!r}", STATE_FILE)
    baseline_state = project.get("brownfield_baseline")
    if not isinstance(baseline_state, str) or baseline_state not in BROWNFIELD_STATES:
        ctx.error("PROJECT_VOCABULARY", "Invalid brownfield_baseline state", STATE_FILE)

    if REQ_ID.fullmatch(str(lifecycle.get("requirements_revision"))) is None:
        ctx.error("STATE_REVISION_ID", "Invalid requirements revision", STATE_FILE)
    if DES_ID.fullmatch(str(lifecycle.get("design_revision"))) is None:
        ctx.error("STATE_REVISION_ID", "Invalid design revision", STATE_FILE)
    if AUTH_ID.fullmatch(str(lifecycle.get("construction_authorization"))) is None:
        ctx.error("STATE_REVISION_ID", "Invalid construction authorization", STATE_FILE)
    gate_a = lifecycle.get("gate_a")
    gate_b = lifecycle.get("gate_b")
    if (
        not isinstance(gate_a, str)
        or gate_a not in GATE_A_STATES
        or not isinstance(gate_b, str)
        or gate_b not in GATE_B_STATES
    ):
        ctx.error("STATE_GATE", "Invalid derived gate state", STATE_FILE)

    run_mode = execution.get("mode")
    run_state_value = execution.get("state")
    if (
        not isinstance(run_mode, str)
        or run_mode not in RUN_MODES
        or not isinstance(run_state_value, str)
        or run_state_value not in RUN_STATES
    ):
        ctx.error("STATE_RUN", "Invalid execution mode or state", STATE_FILE)
    plan = execution.get("plan_revision")
    if plan is not None and PLAN_ID.fullmatch(str(plan)) is None:
        ctx.error("STATE_RUN", "plan_revision must be null or PLAN-nnnn", STATE_FILE)
    plan_state = execution.get("plan_state")
    if not isinstance(plan_state, str) or plan_state not in {"UNINITIALIZED", "CURRENT", "STALE"}:
        ctx.error("STATE_RUN", "plan_state must be UNINITIALIZED, CURRENT, or STALE", STATE_FILE)
    if (plan is None) != (plan_state == "UNINITIALIZED"):
        ctx.error("STATE_RUN", "plan_revision and plan_state are inconsistent", STATE_FILE)
    active = execution.get("active_tasks")
    if not isinstance(active, list) or not all(isinstance(item, str) and TASK_ID.fullmatch(item) for item in active):
        ctx.error("STATE_RUN", "active_tasks must contain only TASK IDs", STATE_FILE)
    elif len(active) != len(set(active)):
        ctx.error("STATE_RUN", "active_tasks contains duplicates", STATE_FILE)
    attempts = execution.get("attempts")
    if not isinstance(attempts, dict) or any(
        TASK_ID.fullmatch(str(key)) is None or not isinstance(value, int) or isinstance(value, bool) or value < 0
        for key, value in (attempts.items() if isinstance(attempts, dict) else [])
    ):
        ctx.error("STATE_RUN", "attempts must map TASK IDs to non-negative integers", STATE_FILE)
    run_id = execution.get("run_id")
    coordinator = execution.get("coordinator")
    run_state = run_state_value if isinstance(run_state_value, str) else ""
    basis = execution.get("basis")
    if run_id is not None and RUN_ID.fullmatch(str(run_id)) is None:
        ctx.error("STATE_RUN", "run_id must be null or RUN-nnnn", STATE_FILE)
    if run_state == "IDLE":
        if (
            run_id is not None
            or coordinator is not None
            or execution.get("mode") != "NONE"
            or execution.get("active_tasks")
        ):
            ctx.error("STATE_RUN", "IDLE execution cannot have a coordinator, run ID, run mode, or active tasks", STATE_FILE)
    else:
        if run_id is None or coordinator is None or execution.get("mode") == "NONE":
            ctx.error("STATE_RUN", "A non-IDLE execution requires a coordinator, run ID, and run mode", STATE_FILE)
        expected_basis_keys = {
            "requirements_revision",
            "design_revision",
            "construction_authorization",
        }
        if not isinstance(basis, dict) or set(basis) != expected_basis_keys:
            ctx.error("STATE_RUN", "A non-IDLE execution requires a complete revision basis", STATE_FILE)
    checkpoint = execution.get("last_checkpoint")
    if checkpoint is not None:
        checkpoint_keys = {"id", "at", "evidence_ref"}
        if not isinstance(checkpoint, dict) or set(checkpoint) != checkpoint_keys:
            ctx.error("STATE_RUN", "last_checkpoint has an invalid shape", STATE_FILE)
        elif (
            CHECKPOINT_ID.fullmatch(str(checkpoint.get("id"))) is None
            or unresolved(str(checkpoint.get("at", "")))
            or unresolved(str(checkpoint.get("evidence_ref", "")))
        ):
            ctx.error("STATE_RUN", "last_checkpoint fields must be explicit", STATE_FILE)
    if run_state in {"CHECKPOINTED", "BLOCKED", "COMPLETE"} and checkpoint is None:
        ctx.error("STATE_RUN", f"{run_state} execution requires a checkpoint", STATE_FILE)
    if run_state == "COMPLETE" and execution.get("active_tasks"):
        ctx.error("STATE_RUN", "COMPLETE execution cannot have active tasks", STATE_FILE)
    if execution.get("state") == "RUNNING":
        ctx.error(
            "RUN_UNCLEAN_INTERRUPTION",
            "Persisted RUNNING state is not safe to resume; reconcile partial work and checkpoint first",
            STATE_FILE,
        )
    return True


def validate_brownfield_contract(ctx: Context, text: str) -> None:
    heading = "### 1.2 Brownfield baseline and preservation contract"
    matches = list(re.finditer(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE))
    if len(matches) != 1:
        ctx.error("BROWNFIELD_PRD_BASELINE", f"Expected exactly one {heading!r}", PRD_FILE)
        return
    next_heading = re.search(r"^##\s+2\.", text[matches[0].end() :], re.MULTILINE)
    end = matches[0].end() + next_heading.start() if next_heading else len(text)
    tables = markdown_tables(text[matches[0].end() : end])
    if len(tables) < 2:
        ctx.error(
            "BROWNFIELD_PRD_BASELINE",
            "Brownfield approval requires both baseline and preservation tables",
            PRD_FILE,
        )
        return

    baseline: dict[str, str] = {}
    for row in tables[0][2:]:
        if len(row) >= 2:
            if row[0] in baseline:
                ctx.error("BROWNFIELD_PRD_BASELINE", f"Duplicate brownfield field {row[0]!r}", PRD_FILE)
            baseline[row[0]] = row[1]
    missing = sorted(BROWNFIELD_BASELINE_FIELDS - set(baseline))
    if missing:
        ctx.error(
            "BROWNFIELD_PRD_BASELINE",
            "Brownfield baseline is missing fields: " + ", ".join(missing),
            PRD_FILE,
        )
    unresolved_fields = sorted(
        field for field in BROWNFIELD_BASELINE_FIELDS if not explicit_value(baseline.get(field, ""), allow_none=True)
    )
    if unresolved_fields:
        ctx.error(
            "BROWNFIELD_PRD_BASELINE",
            "Brownfield baseline has unresolved fields: " + ", ".join(unresolved_fields),
            PRD_FILE,
        )

    preservation_rows = [
        row for row in tables[1][2:] if row and re.fullmatch(r"PRES-\d+", row[0]) is not None
    ]
    if not preservation_rows:
        ctx.error(
            "BROWNFIELD_PRD_PRESERVATION",
            "Brownfield approval requires at least one explicit PRES record",
            PRD_FILE,
        )
    for row in preservation_rows:
        if len(row) < 5 or any(not explicit_value(value, allow_none=False) for value in row[1:5]):
            ctx.error(
                "BROWNFIELD_PRD_PRESERVATION",
                f"{row[0]} must explicitly define the preserved behavior and change boundary",
                PRD_FILE,
            )


def validate_construction_envelope(
    ctx: Context,
    envelope: dict[str, str],
    fields: dict[str, str],
    selections: dict[str, str | None],
    cost_posture: str,
) -> None:
    missing = sorted(ENVELOPE_EXPLICIT_FIELDS - set(envelope))
    if missing:
        ctx.error("GATE_B_ENVELOPE", "Construction envelope is missing fields: " + ", ".join(missing), PRD_FILE)
    unresolved_fields = sorted(
        field
        for field in ENVELOPE_EXPLICIT_FIELDS
        if not explicit_value(
            envelope.get(field, ""),
            allow_none=field
            in {
                "Excluded or owner-only write set",
                "Allowed external-state targets",
                "Protected dirty paths",
                "GitHub repository, branch, and merge constraints",
            },
        )
    )
    if unresolved_fields:
        ctx.error(
            "GATE_B_ENVELOPE",
            "Construction envelope has unresolved fields: " + ", ".join(unresolved_fields),
            PRD_FILE,
        )

    if envelope.get("Construction authorization ID") != fields.get("construction_authorization"):
        ctx.error("GATE_B_ENVELOPE", "Envelope AUTH does not match current AUTH", PRD_FILE)
    authorized_baseline = envelope.get("Authorized baseline commit", "")
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", authorized_baseline) is None:
        ctx.error("GATE_B_ENVELOPE", "Authorized baseline commit must be a full lowercase Git commit hash", PRD_FILE)
    else:
        validate_authorized_baseline_repository(ctx, authorized_baseline)
    expected_project_rows = {
        "Project mode": selections.get("mode"),
        "Delivery profile and effective risk": (
            f"{selections.get('delivery_profile')} / {selections.get('effective_risk')}"
            if selections.get("delivery_profile") and selections.get("effective_risk")
            else None
        ),
        "Project AWS lane": selections.get("aws_lane"),
    }
    for key, expected in expected_project_rows.items():
        if expected is None or envelope.get(key) != expected:
            ctx.error("GATE_B_PROJECT_DRIFT", f"Envelope {key} does not exactly match Document status", PRD_FILE)
    try:
        authorized_ids = parse_authorized_ids(
            envelope.get("Authorized requirement and design IDs", "")
        )
        if fields.get("requirements_revision") != authorized_ids[0]:
            ctx.error("GATE_B_ENVELOPE", "Authorized ID basis must include the current REQ revision", PRD_FILE)
        if fields.get("design_revision") != authorized_ids[1]:
            ctx.error("GATE_B_ENVELOPE", "Authorized ID basis must include the current DES revision", PRD_FILE)
    except ValueError as exc:
        ctx.error("GATE_B_ENVELOPE", str(exc), PRD_FILE)

    if envelope.get("Autonomous construction") not in {"ALLOWED", "PROHIBITED"}:
        ctx.error("GATE_B_ENVELOPE", "Autonomous construction must be ALLOWED or PROHIBITED", PRD_FILE)
    numeric: dict[str, int] = {}
    for key in ("Maximum generated tasks", "Maximum parallel workers", "Attempt budget"):
        value = envelope.get(key, "")
        if re.fullmatch(r"[1-9]\d*", value) is None:
            ctx.error("GATE_B_ENVELOPE", f"{key} must be a positive integer", PRD_FILE)
        else:
            numeric[key] = int(value)
    if envelope.get("Eligible task status") != "READY":
        ctx.error("GATE_B_ENVELOPE", "Eligible task status must be READY", PRD_FILE)
    if envelope.get("GitHub boundary") not in GITHUB_BOUNDARIES:
        ctx.error("GATE_B_ENVELOPE", "GitHub boundary is not canonical", PRD_FILE)
    if envelope.get("AWS boundary") not in AWS_BOUNDARIES:
        ctx.error("GATE_B_ENVELOPE", "AWS boundary is not canonical", PRD_FILE)
    try:
        parse_envelope_paths(
            envelope.get("Allowed repository write set", ""),
            "Allowed repository write set",
            allow_none=False,
        )
        parse_envelope_paths(
            envelope.get("Excluded or owner-only write set", ""),
            "Excluded or owner-only write set",
            allow_none=True,
        )
        parse_envelope_paths(
            envelope.get("Protected dirty paths", ""),
            "Protected dirty paths",
            allow_none=True,
        )
        parse_envelope_targets(envelope.get("Allowed external-state targets", ""))
        parse_task_boundary(envelope.get("Task boundary", ""))
        parse_command_prefixes(envelope.get("Local command boundary", ""))
        parse_github_constraints(
            envelope.get("GitHub repository, branch, and merge constraints", ""),
            envelope.get("GitHub boundary", ""),
        )
        parse_future_expiry(envelope.get("Authorization expiry or completion condition", ""))
    except ValueError as exc:
        ctx.error("GATE_B_ENVELOPE", str(exc), PRD_FILE)
    if numeric.get("Maximum parallel workers", 1) > 1 and "isolated worktree" not in envelope.get(
        "Parallelism rule", ""
    ).lower():
        ctx.error(
            "GATE_B_ENVELOPE",
            "More than one worker requires disjoint work in isolated worktrees",
            PRD_FILE,
        )

    lane_boundaries = {
        "documentation-only": {"NONE", "DOCS_ONLY"},
        "read-only": {"NONE", "DOCS_ONLY", "READ_ONLY"},
        "fast-dev": {"NONE", "DOCS_ONLY", "READ_ONLY", "MUTATE_LISTED_RESOURCES"},
        "explicit-gate": {"NONE", "DOCS_ONLY", "READ_ONLY", "MUTATE_LISTED_RESOURCES"},
    }
    lane = selections.get("aws_lane")
    if lane in lane_boundaries and envelope.get("AWS boundary") not in lane_boundaries[lane]:
        ctx.error("AWS_LANE_BOUNDARY", "AWS boundary does not match the selected project lane", PRD_FILE)
    aws_boundary = envelope.get("AWS boundary")
    if aws_boundary in {"NONE", "DOCS_ONLY"}:
        expected = f"NOT_APPLICABLE — AWS boundary {aws_boundary} authorizes no authenticated action"
        for key in sorted(AWS_DETAIL_FIELDS):
            if envelope.get(key) != expected:
                ctx.error(
                    "GATE_B_ENVELOPE",
                    f"{key} must be exactly {expected!r} for {aws_boundary}",
                    PRD_FILE,
                )
    elif aws_boundary == "READ_ONLY":
        required_read = {
            "AWS account",
            "AWS role or profile",
            "AWS Region",
            "AWS environment",
            "AWS resource allowlist",
            "AWS allowed operations",
            "AWS prohibited operations",
            "AWS authorization validity",
        }
        for key in sorted(AWS_DETAIL_FIELDS):
            value = envelope.get(key, "")
            if key in required_read and (
                not explicit_value(value) or value.startswith("NOT_APPLICABLE — ")
            ):
                ctx.error("GATE_B_ENVELOPE", f"{key} is required for READ_ONLY AWS authority", PRD_FILE)
            elif key not in required_read and not (
                explicit_value(value) or value.startswith("NOT_APPLICABLE — ")
            ):
                ctx.error("GATE_B_ENVELOPE", f"{key} must be explicit for READ_ONLY AWS authority", PRD_FILE)
        try:
            parse_aws_environment(envelope.get("AWS environment", ""))
            parse_future_expiry(envelope.get("AWS authorization validity", ""))
        except ValueError as exc:
            ctx.error("GATE_B_ENVELOPE", str(exc), PRD_FILE)
    elif aws_boundary == "MUTATE_LISTED_RESOURCES":
        for key in sorted(AWS_DETAIL_FIELDS):
            value = envelope.get(key, "")
            if not explicit_value(value) or value.startswith("NOT_APPLICABLE — "):
                ctx.error("GATE_B_ENVELOPE", f"{key} is required for AWS mutation authority", PRD_FILE)
        try:
            _environment, environment_class = parse_aws_environment(
                envelope.get("AWS environment", "")
            )
            if lane == "fast-dev" and environment_class != "NON_PRODUCTION":
                raise ValueError("fast-dev AWS mutation authority must be NON_PRODUCTION")
            validate_aws_artifact(
                envelope.get("AWS artifact authorization and provenance", ""),
                envelope.get("Authorized baseline commit", ""),
            )
            validate_aws_cost_ceiling(
                envelope.get("AWS cost ceiling", ""),
                cost_posture,
            )
            parse_future_expiry(envelope.get("AWS authorization validity", ""))
        except ValueError as exc:
            ctx.error("GATE_B_ENVELOPE", str(exc), PRD_FILE)


def validate_readiness_card(
    ctx: Context,
    card: dict[str, str],
    expected_fields: set[str],
    gate: str,
) -> None:
    if set(card) != expected_fields:
        ctx.error(
            f"{gate}_READINESS_CARD",
            f"{gate.replace('_', ' ')} readiness-card fields must be exact",
            PRD_FILE,
        )
    for field in sorted(expected_fields):
        value = clean_cell(card.get(field, ""))
        if field == "Outstanding gaps" and value == "NONE":
            continue
        if value.startswith("NOT_APPLICABLE — ") and explicit_value(
            value.removeprefix("NOT_APPLICABLE — ")
        ):
            continue
        if not explicit_value(value, allow_none=False):
            ctx.error(
                f"{gate}_READINESS_CARD",
                f"{field} is not an explicit current decision basis",
                PRD_FILE,
            )


def validate_prd(
    ctx: Context,
    state: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str], dict[str, str], bool]:
    text = ctx.texts.get(PRD_FILE) or safe_read_text(ctx, PRD_FILE)
    if text is None:
        return {}, {}, {}, False
    try:
        document = table_after_heading(text, "## Document status")
        workload = table_after_heading(text, "## 1. Workload profile")
        gate_a_agent = table_after_heading(text, "### Gate A — agent analysis record")
        gate_a_card = table_after_heading(text, "### Gate A — readiness card")
        gate_a_owner = table_after_heading(text, "### Gate A — owner acceptance record")
        gate_b_agent = table_after_heading(text, "## 27. Gate B agent review record")
        gate_b_card = table_after_heading(text, "### Gate B — readiness card")
        envelope = table_after_heading(text, "## 28. Construction envelope")
        gate_b_owner = table_after_heading(text, "## 29. Gate B owner authorization record")
        envelope_digest = canonical_envelope_sha256(text)
        # Check marker structure even before either gate is approved.
        marked_receipt(text, "gate-a")
        marked_receipt(text, "gate-b")
    except ValueError as exc:
        ctx.error("PRD_STRUCTURE", str(exc), PRD_FILE)
        return {}, {}, {}, False

    project = state.get("project", {})
    lifecycle = state.get("lifecycle", {})
    allow_unselected = project.get("mode") is None
    selections = {
        "mode": exact_selection(
            ctx, document.get("Project mode", ""), PROJECT_MODES,
            "PROJECT_VOCABULARY", "Project mode", allow_unselected=allow_unselected,
        ),
        "delivery_profile": exact_selection(
            ctx, document.get("Delivery profile", ""), DELIVERY_PROFILES,
            "PROJECT_VOCABULARY", "Delivery profile", allow_unselected=allow_unselected,
        ),
        "effective_risk": exact_selection(
            ctx, document.get("Effective risk", ""), RISK_LEVELS,
            "PROJECT_VOCABULARY", "Effective risk", allow_unselected=allow_unselected,
        ),
        "aws_lane": exact_selection(
            ctx, document.get("AWS lane", ""), AWS_LANES,
            "PROJECT_VOCABULARY", "AWS lane", allow_unselected=allow_unselected,
        ),
    }
    for key, selected in selections.items():
        if project.get(key) != selected:
            ctx.error(
                "STATE_PRD_DRIFT",
                f"project.{key}={project.get(key)!r} does not match PRD value {selected!r}",
                STATE_FILE,
            )
    if selections["effective_risk"] in {"high", "critical"} and selections["delivery_profile"] != "high-risk":
        ctx.error("PROJECT_RISK_PROFILE", "High or critical risk requires the high-risk profile", PRD_FILE)

    fields = {
        "requirements_revision": document.get("Current requirements revision", ""),
        "design_revision": document.get("Current design revision", ""),
        "construction_authorization": document.get("Current construction authorization ID", ""),
        "gate_a": document.get("Gate A derived status", ""),
        "gate_b": document.get("Gate B derived status", ""),
    }
    patterns = {
        "requirements_revision": REQ_ID,
        "design_revision": DES_ID,
        "construction_authorization": AUTH_ID,
    }
    for key, pattern in patterns.items():
        if pattern.fullmatch(fields[key]) is None:
            ctx.error("PRD_REVISION_ID", f"Invalid PRD {key}: {fields[key]!r}", PRD_FILE)
    if fields["gate_a"] not in GATE_A_STATES or fields["gate_b"] not in GATE_B_STATES:
        ctx.error("PRD_GATE", "Invalid PRD derived gate state", PRD_FILE)
    for key, value in fields.items():
        if lifecycle.get(key) != value:
            ctx.error(
                "STATE_PRD_DRIFT",
                f"lifecycle.{key}={lifecycle.get(key)!r} does not match PRD {value!r}",
                STATE_FILE,
            )

    gate_a_ready_or_current = fields["gate_a"] in {
        "PENDING_OWNER_APPROVAL",
        "APPROVED_FOR_DESIGN",
    }
    gate_b_ready_or_current = fields["gate_b"] in {
        "PENDING_OWNER_APPROVAL",
        "APPROVED_FOR_CONSTRUCTION",
    }
    gate_a_agent_ready = gate_a_agent.get("Agent recommendation") in {
        "READY_WITH_PROPOSED_ASSUMPTIONS",
        "READY_FOR_OWNER_APPROVAL",
    }
    gate_b_agent_ready = gate_b_agent.get("Agent recommendation") == "READY_FOR_CONSTRUCTION_APPROVAL"
    card_cost_posture = clean_cell(gate_a_card.get("Cost posture", ""))
    if gate_a_agent_ready or gate_a_ready_or_current:
        validate_readiness_card(ctx, gate_a_card, GATE_A_READINESS_FIELDS, "GATE_A")
        try:
            parse_cost_posture(card_cost_posture)
        except ValueError as exc:
            ctx.error("GATE_A_COST_POSTURE", str(exc), PRD_FILE)
        if card_cost_posture != project.get("cost_posture"):
            ctx.error(
                "STATE_PRD_DRIFT",
                "Gate A Cost posture does not match bootstrap state",
                STATE_FILE,
            )
    if gate_b_agent_ready or gate_b_ready_or_current:
        validate_readiness_card(ctx, gate_b_card, GATE_B_READINESS_FIELDS, "GATE_B")
        if gate_b_card.get("Outstanding gaps") != "NONE":
            ctx.error("GATE_B_READINESS_CARD", "Gate B readiness requires Outstanding gaps NONE", PRD_FILE)
    if gate_a_agent_ready and fields["gate_a"] == "BLOCKED":
        ctx.error(
            "GATE_A_LIFECYCLE_TRANSITION",
            "Agent-ready Gate A must atomically transition to PENDING_OWNER_APPROVAL",
            PRD_FILE,
        )
    if gate_b_agent_ready and fields["gate_b"] == "BLOCKED":
        ctx.error(
            "GATE_B_LIFECYCLE_TRANSITION",
            "Agent-ready Gate B must atomically transition to PENDING_OWNER_APPROVAL",
            PRD_FILE,
        )
    if gate_a_ready_or_current or gate_b_ready_or_current:
        missing_selections = sorted(key for key, value in selections.items() if value is None)
        if missing_selections:
            ctx.error(
                "PROJECT_SELECTION_REQUIRED",
                "Gate readiness requires explicit project selections: " + ", ".join(missing_selections),
                PRD_FILE,
            )
    if selections["mode"] == "greenfield" and project.get("brownfield_baseline") != "NOT_APPLICABLE":
        ctx.error("BROWNFIELD_STATE", "Greenfield mode requires NOT_APPLICABLE brownfield state", STATE_FILE)
    if selections["mode"] == "brownfield" and gate_a_ready_or_current:
        if project.get("brownfield_baseline") != "RECORDED":
            ctx.error(
                "BROWNFIELD_STATE",
                "Brownfield mode requires a RECORDED baseline before Gate A is presented or approved",
                STATE_FILE,
            )
        validate_brownfield_contract(ctx, text)

    requirements_present = not unresolved(workload.get("Business outcome", ""))
    functional_match = re.search(
        r"^### Functional requirements\s*$.*?(?=^##\s+7\.)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if functional_match is not None:
        rows = re.findall(r"^\|\s*FR-\d+\s*\|(.+)$", functional_match.group(0), re.MULTILINE)
        requirements_present = requirements_present and any("TODO" not in row.upper() for row in rows)

    if gate_a_ready_or_current:
        if gate_a_agent.get("Requirements revision analyzed") != fields["requirements_revision"]:
            ctx.error("GATE_A_REVISION_MISMATCH", "Gate A analysis does not match current REQ", PRD_FILE)
        if gate_a_agent.get("Agent recommendation") not in {
            "READY_WITH_PROPOSED_ASSUMPTIONS",
            "READY_FOR_OWNER_APPROVAL",
        }:
            ctx.error("GATE_A_RECOMMENDATION", "Gate A was not agent-ready", PRD_FILE)
        for key in ("Open blocking finding IDs", "Open blocking decision IDs"):
            if gate_a_agent.get(key) != "NONE":
                ctx.error("GATE_A_BLOCKER", f"{key} must be NONE before owner approval", PRD_FILE)

    if fields["gate_a"] == "APPROVED_FOR_DESIGN":
        expected = "\n".join(
            [
                "APPROVE REQUIREMENTS GATE A",
                f"Requirements revision: {fields['requirements_revision']}",
                f"Cost posture: {card_cost_posture}",
                f"Accepted assumptions: {gate_a_owner.get('Explicitly accepted assumption IDs', '')}",
                f"Approver: {gate_a_owner.get('Approver', '')}",
            ]
        )
        if gate_a_owner.get("Owner decision") != "APPROVED" or gate_a_owner.get(
            "Authorized requirements revision"
        ) != fields["requirements_revision"]:
            ctx.error("GATE_A_OWNER_RECORD", "Gate A owner record is not current and approved", PRD_FILE)
        if gate_a_owner.get("Authorized cost posture") != card_cost_posture:
            ctx.error(
                "GATE_A_COST_AUTHORIZATION",
                "Gate A owner record does not authorize the exact readiness-card cost posture",
                PRD_FILE,
            )
        if gate_a_owner.get("Derived Gate A state") != fields["gate_a"]:
            ctx.error("GATE_A_OWNER_RECORD", "Detailed Gate A state does not match Document status", PRD_FILE)
        if not explicit_human_approver(gate_a_owner.get("Approver", "")):
            ctx.error(
                "GATE_A_HUMAN_APPROVER",
                "Gate A approver must be an explicit human owner, not an agent or automation identity",
                PRD_FILE,
            )
        if not explicit_timestamp(gate_a_owner.get("Authorization provided at", "")):
            ctx.error(
                "GATE_A_OWNER_RECORD",
                "Gate A authorization time must be an explicit ISO 8601 timestamp with timezone",
                PRD_FILE,
            )
        if not explicit_value(gate_a_owner.get("Authorization source", "")):
            ctx.error("GATE_A_OWNER_RECORD", "Gate A authorization source is unresolved", PRD_FILE)
        if gate_a_owner.get("Verbatim owner receipt") != "RECORDED_BELOW":
            ctx.error("GATE_A_OWNER_RECORD", "Approved Gate A must reference the marked receipt block", PRD_FILE)
        try:
            required_ids = parse_exact_id_list(
                gate_a_agent.get("Proposed assumption IDs required to proceed", ""),
                re.compile(r"ASM-\d+"),
                "Gate A proposed assumptions",
            )
            accepted_ids = parse_exact_id_list(
                gate_a_owner.get("Explicitly accepted assumption IDs", ""),
                re.compile(r"ASM-\d+"),
                "Gate A accepted assumptions",
            )
            if required_ids != accepted_ids:
                ctx.error(
                    "GATE_A_ASSUMPTIONS",
                    "Accepted assumption IDs must exactly equal the required IDs in the same order",
                    PRD_FILE,
                )
        except ValueError as exc:
            ctx.error("GATE_A_ASSUMPTIONS", str(exc), PRD_FILE)
        try:
            actual = marked_receipt(text, "gate-a")
            if actual != expected:
                ctx.error("GATE_A_RECEIPT_MISMATCH", "Marked Gate A receipt does not match structured fields", PRD_FILE)
        except ValueError as exc:
            ctx.error("GATE_A_RECEIPT_MISMATCH", str(exc), PRD_FILE)

    if gate_b_ready_or_current:
        reviewed = {
            "Requirements revision reviewed": fields["requirements_revision"],
            "Design revision reviewed": fields["design_revision"],
            "Construction authorization ID reviewed": fields["construction_authorization"],
        }
        for key, value in reviewed.items():
            if gate_b_agent.get(key) != value:
                ctx.error("GATE_B_REVISION_MISMATCH", f"{key} does not match current state", PRD_FILE)
        if gate_b_agent.get("Construction envelope SHA-256 reviewed") != envelope_digest:
            ctx.error(
                "GATE_B_ENVELOPE_HASH",
                "Gate B agent review does not bind the complete current construction envelope",
                PRD_FILE,
            )
        if gate_b_agent.get("Agent recommendation") != "READY_FOR_CONSTRUCTION_APPROVAL":
            ctx.error("GATE_B_RECOMMENDATION", "Gate B was not agent-ready", PRD_FILE)
        for key in (
            "PRD completeness gaps",
            "Requirement-to-design-and-test traceability gaps",
            "Unresolved risk or preservation gaps",
        ):
            if gate_b_agent.get(key) != "NONE":
                ctx.error("GATE_B_GAP", f"{key} must be NONE before owner approval", PRD_FILE)
        validate_construction_envelope(
            ctx,
            envelope,
            fields,
            selections,
            str(project.get("cost_posture", "")),
        )

    if fields["gate_b"] == "APPROVED_FOR_CONSTRUCTION":
        if fields["gate_a"] != "APPROVED_FOR_DESIGN":
            ctx.error("GATE_B_WITHOUT_GATE_A", "Gate B cannot be current while Gate A is not current", PRD_FILE)
        if gate_b_owner.get("Authorized construction envelope SHA-256") != envelope_digest:
            ctx.error(
                "GATE_B_ENVELOPE_HASH",
                "Gate B owner authorization does not bind the complete current construction envelope",
                PRD_FILE,
            )
        expected = "\n".join(
            [
                "APPROVE PRD AND CONSTRUCTION GATE B",
                f"Requirements revision: {fields['requirements_revision']}",
                f"Design revision: {fields['design_revision']}",
                f"Construction authorization: {fields['construction_authorization']}",
                f"Construction envelope SHA-256: {envelope_digest}",
                "Use the proposed construction envelope above.",
                f"Approver: {gate_b_owner.get('Approver', '')}",
            ]
        )
        owner_values = {
            "Authorized requirements revision": fields["requirements_revision"],
            "Authorized design revision": fields["design_revision"],
            "Authorized construction authorization ID": fields["construction_authorization"],
        }
        if gate_b_owner.get("Owner decision") != "APPROVED":
            ctx.error("GATE_B_OWNER_RECORD", "Gate B owner decision is not APPROVED", PRD_FILE)
        for key, value in owner_values.items():
            if gate_b_owner.get(key) != value:
                ctx.error("GATE_B_OWNER_RECORD", f"{key} does not match current state", PRD_FILE)
        if not explicit_human_approver(gate_b_owner.get("Approver", "")):
            ctx.error(
                "GATE_B_HUMAN_APPROVER",
                "Gate B approver must be an explicit human owner, not an agent or automation identity",
                PRD_FILE,
            )
        if not explicit_timestamp(gate_b_owner.get("Authorization provided at", "")):
            ctx.error(
                "GATE_B_OWNER_RECORD",
                "Gate B authorization time must be an explicit ISO 8601 timestamp with timezone",
                PRD_FILE,
            )
        if not explicit_value(gate_b_owner.get("Authorization source", "")):
            ctx.error("GATE_B_OWNER_RECORD", "Gate B authorization source is unresolved", PRD_FILE)
        if gate_b_owner.get("Derived Gate B state") != fields["gate_b"]:
            ctx.error("GATE_B_OWNER_RECORD", "Detailed Gate B state does not match Document status", PRD_FILE)
        if gate_b_owner.get("Verbatim owner receipt") != "RECORDED_BELOW":
            ctx.error("GATE_B_OWNER_RECORD", "Approved Gate B must reference the marked receipt block", PRD_FILE)
        try:
            actual = marked_receipt(text, "gate-b")
            if actual != expected:
                ctx.error("GATE_B_RECEIPT_MISMATCH", "Marked Gate B receipt does not match structured fields", PRD_FILE)
        except ValueError as exc:
            ctx.error("GATE_B_RECEIPT_MISMATCH", str(exc), PRD_FILE)

    return fields, envelope, selections, requirements_present or gate_b_agent_ready


def path_boundary_contains(allowed: str, requested: str) -> bool:
    allowed = allowed.casefold()
    requested = requested.casefold()
    allowed_base = allowed[:-3] if allowed.endswith("/**") else allowed
    requested_base = requested[:-3] if requested.endswith("/**") else requested
    if allowed.endswith("/**"):
        return requested_base == allowed_base or requested_base.startswith(allowed_base + "/")
    return allowed == requested and not requested.endswith("/**")


def path_boundaries_overlap(first: str, second: str) -> bool:
    first = first.casefold()
    second = second.casefold()
    first_base = first[:-3] if first.endswith("/**") else first
    second_base = second[:-3] if second.endswith("/**") else second
    return (
        first_base == second_base
        or first_base.startswith(second_base + "/")
        or second_base.startswith(first_base + "/")
    )


def external_targets_overlap(first: str, second: str) -> bool:
    first = first.casefold()
    second = second.casefold()
    if first == second:
        return True
    return any(
        first.startswith(second + separator) or second.startswith(first + separator)
        for separator in ("/", ":", "#")
    )


def external_target_contains(allowed: str, requested: str) -> bool:
    allowed = allowed.casefold()
    requested = requested.casefold()
    if allowed == requested:
        return True
    return any(requested.startswith(allowed + separator) for separator in ("/", ":", "#"))


def validate_tasks_against_envelope(
    ctx: Context,
    tasks: list[InspectedTask],
    snapshot: dict[str, str],
    state: dict[str, Any],
    envelope: dict[str, str],
) -> None:
    try:
        maximum_tasks = int(envelope.get("Maximum generated tasks", ""))
        maximum_workers = int(envelope.get("Maximum parallel workers", ""))
        maximum_attempts = int(envelope.get("Attempt budget", ""))
        snapshot_workers = int(snapshot.get("Maximum workers", ""))
        allowed_writes = parse_envelope_paths(
            envelope.get("Allowed repository write set", ""),
            "Allowed repository write set",
            allow_none=False,
        )
        excluded_writes = parse_envelope_paths(
            envelope.get("Excluded or owner-only write set", ""),
            "Excluded or owner-only write set",
            allow_none=True,
        )
        allowed_external = parse_envelope_targets(
            envelope.get("Allowed external-state targets", "")
        )
        authorized_protected = parse_envelope_paths(
            envelope.get("Protected dirty paths", ""),
            "Protected dirty paths",
            allow_none=True,
        )
        authorized_ids = set(
            parse_authorized_ids(
                envelope.get("Authorized requirement and design IDs", "")
            )
        )
        authorized_ids.update(ID_LIKE.findall(envelope.get("Authorized outcome", "")))
        boundary_mode, explicit_task_ids = parse_task_boundary(envelope.get("Task boundary", ""))
        command_prefixes = parse_command_prefixes(envelope.get("Local command boundary", ""))
        github_repo = parse_github_constraints(
            envelope.get("GitHub repository, branch, and merge constraints", ""),
            envelope.get("GitHub boundary", ""),
        )
        parse_future_expiry(envelope.get("Authorization expiry or completion condition", ""))
    except (ValueError, TypeError) as exc:
        ctx.error("GATE_B_ENVELOPE", f"Cannot validate task boundaries: {exc}", PRD_FILE)
        return
    if len(tasks) > maximum_tasks:
        ctx.error("TASK_LIMIT_EXCEEDED", f"{len(tasks)} tasks exceed AUTH maximum {maximum_tasks}", TASKS_FILE)
    if snapshot_workers > maximum_workers:
        ctx.error("WORKER_LIMIT_EXCEEDED", "TASKS Maximum workers exceeds AUTH", TASKS_FILE)
    if maximum_workers > 1 and "isolated worktree" not in envelope.get("Parallelism rule", "").lower():
        ctx.error("GATE_B_ENVELOPE", "Parallel AUTH above one worker must require isolated worktrees", PRD_FILE)
    if snapshot.get("Baseline commit") != envelope.get("Authorized baseline commit"):
        ctx.error("TASK_BASELINE_DRIFT", "TASKS baseline commit does not match AUTH", TASKS_FILE)
    snapshot_protected = snapshot.get("Protected dirty paths", "NONE")
    try:
        task_protected = (
            []
            if snapshot_protected == "NONE"
            else parse_task_write_set(snapshot_protected, "Protected dirty paths")
        )
    except ValueError as exc:
        ctx.error("TASK_SNAPSHOT", str(exc), TASKS_FILE)
        task_protected = []
    if [item.casefold() for item in task_protected] != [item.casefold() for item in authorized_protected]:
        ctx.error("TASK_BASELINE_DRIFT", "TASKS protected dirty paths do not match AUTH", TASKS_FILE)

    execution = state.get("execution") if isinstance(state.get("execution"), dict) else {}
    if execution.get("mode") == "AUTONOMOUS" and envelope.get("Autonomous construction") != "ALLOWED":
        ctx.error("AUTONOMY_OUTSIDE_AUTH", "AUTONOMOUS run is not allowed by Gate B", STATE_FILE)
    if not tasks:
        return

    github_boundary = envelope.get("GitHub boundary", "NONE")
    aws_boundary = envelope.get("AWS boundary", "NONE")
    protected = snapshot.get("Protected dirty paths", "NONE")
    try:
        protected_paths = [] if protected == "NONE" else parse_task_write_set(protected, "Protected dirty paths")
    except ValueError as exc:
        ctx.error("TASK_SNAPSHOT", str(exc), TASKS_FILE)
        protected_paths = []

    for task in tasks:
        try:
            writes = parse_task_write_set(task.metadata["Write set"], task.task_id)
            external_targets = parse_task_external_state(
                task.metadata["External state"], task.task_id
            )
        except (KeyError, ValueError):
            continue
        for requested in writes:
            if not any(path_boundary_contains(allowed, requested) for allowed in allowed_writes):
                ctx.error("TASK_OUTSIDE_WRITE_BOUNDARY", f"{task.task_id} write {requested!r} is outside AUTH", TASKS_FILE)
            if any(path_boundaries_overlap(requested, excluded) for excluded in excluded_writes):
                ctx.error("TASK_EXCLUDED_WRITE", f"{task.task_id} overlaps excluded path {requested!r}", TASKS_FILE)
            if task.status in {"READY", "IN_PROGRESS"} and any(
                path_boundaries_overlap(requested, dirty) for dirty in protected_paths
            ):
                ctx.error("TASK_PROTECTED_DIRTY_OVERLAP", f"{task.task_id} overlaps protected dirty path {requested!r}", TASKS_FILE)
        for target in external_targets:
            if not any(external_target_contains(allowed, target) for allowed in allowed_external):
                ctx.error(
                    "TASK_EXTERNAL_STATE_BOUNDARY",
                    f"{task.task_id} external target {target!r} is outside AUTH",
                    TASKS_FILE,
                )
        if boundary_mode == "EXPLICIT" and task.task_id not in explicit_task_ids:
            ctx.error("TASK_OUTSIDE_TASK_BOUNDARY", f"{task.task_id} is not listed by AUTH", TASKS_FILE)

        sections, _duplicates = inspect_task_sections(task.block)
        referenced_ids = set(ID_LIKE.findall(task.metadata.get("Requirements", "")))
        referenced_ids.update(ID_LIKE.findall(task.metadata.get("Design", "")))
        referenced_ids.update(ID_LIKE.findall(sections.get("Outcome", "")))
        outside_ids = sorted(referenced_ids - authorized_ids)
        if outside_ids:
            ctx.error(
                "TASK_ID_OUTSIDE_AUTH",
                f"{task.task_id} references unauthorized IDs: {', '.join(outside_ids)}",
                TASKS_FILE,
            )
        if task.status in {"READY", "IN_PROGRESS", "DONE"}:
            try:
                commands = validation_commands(sections.get("Validation", ""), task.task_id)
                for command in commands:
                    if not any(command_matches_prefix(command, prefix) for prefix in command_prefixes):
                        ctx.error(
                            "TASK_COMMAND_BOUNDARY",
                            f"{task.task_id} command {command!r} is outside AUTH",
                            TASKS_FILE,
                        )
            except ValueError as exc:
                ctx.error("TASK_COMMAND_BOUNDARY", str(exc), TASKS_FILE)
        try:
            if task.attempt_budget > maximum_attempts:
                ctx.error("TASK_ATTEMPT_BOUNDARY", f"{task.task_id} attempt budget exceeds AUTH", TASKS_FILE)
        except (KeyError, ValueError):
            pass
        aws_mode = clean_cell(task.metadata.get("AWS mode", "NONE")).upper()
        allowed_aws_modes = {
            "NONE": {"NONE"},
            "DOCS_ONLY": {"NONE", "DOCS_ONLY"},
            "READ_ONLY": {"NONE", "DOCS_ONLY", "READ_ONLY"},
            "MUTATE_LISTED_RESOURCES": {"NONE", "DOCS_ONLY", "READ_ONLY", "MUTATION"},
        }
        if aws_mode not in allowed_aws_modes.get(aws_boundary, set()):
            ctx.error("TASK_AWS_BOUNDARY", f"{task.task_id} AWS mode exceeds AUTH", TASKS_FILE)
        issue = clean_cell(task.metadata.get("GitHub issue", "PENDING_SYNC"))
        if github_boundary in {"NONE", "READ_ONLY"} and issue != "PENDING_SYNC":
            ctx.error("TASK_GITHUB_BOUNDARY", f"{task.task_id} has a GitHub write result outside AUTH", TASKS_FILE)
        elif github_boundary not in {"NONE", "READ_ONLY"} and issue != "PENDING_SYNC":
            match = GITHUB_ISSUE_URL.fullmatch(issue)
            if match is None or github_repo is None or match.group("repo").casefold() != github_repo.casefold():
                ctx.error(
                    "TASK_GITHUB_BOUNDARY",
                    f"{task.task_id} issue URL does not match the authorized GitHub repository",
                    TASKS_FILE,
                )

    active = [task for task in tasks if task.status == "IN_PROGRESS"]
    if len(active) > min(maximum_workers, snapshot_workers):
        ctx.error("WORKER_LIMIT_EXCEEDED", "IN_PROGRESS tasks exceed the active worker limit", TASKS_FILE)
    for index, first in enumerate(active):
        first_writes = parse_task_write_set(first.metadata["Write set"], first.task_id)
        first_external = parse_task_external_state(first.metadata["External state"], first.task_id)
        for second in active[index + 1 :]:
            second_writes = parse_task_write_set(second.metadata["Write set"], second.task_id)
            second_external = parse_task_external_state(second.metadata["External state"], second.task_id)
            conflict = any(path_boundaries_overlap(a, b) for a in first_writes for b in second_writes)
            conflict |= any(external_targets_overlap(a, b) for a in first_external for b in second_external)
            conflict |= clean_cell(first.metadata["AWS mode"]).upper() == "MUTATION"
            conflict |= clean_cell(second.metadata["AWS mode"]).upper() == "MUTATION"
            if conflict:
                ctx.error("ACTIVE_TASK_CONFLICT", f"{first.task_id} conflicts with {second.task_id}", TASKS_FILE)

def git_read(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(root),
            *arguments,
        ],
        check=False,
        capture_output=True,
        env=environment,
        timeout=10,
    )


def parse_checkpoint_rows(tasks_text: str) -> list[CheckpointReceiptRow]:
    structural = without_fenced_code(tasks_text)
    headings = list(
        re.finditer(r"^## Checkpoints and resume[ \t]*$", structural, re.MULTILINE)
    )
    if len(headings) != 1:
        raise ValueError("TASKS requires exactly one Checkpoints and resume section")
    following = re.search(r"^##\s+", structural[headings[0].end() :], re.MULTILINE)
    end = headings[0].end() + following.start() if following else len(structural)
    raw_lines = tasks_text[headings[0].end() : end].splitlines()
    structural_lines = structural[headings[0].end() : end].splitlines()
    header_indexes = [
        index
        for index, (raw_line, structural_line) in enumerate(
            zip(raw_lines, structural_lines)
        )
        if structural_line.strip().startswith("|")
        and split_markdown_table_row(raw_line) == list(CHECKPOINT_HEADERS)
    ]
    if len(header_indexes) != 1:
        raise ValueError("TASKS requires one exact checkpoint table header")
    header = header_indexes[0]
    table_lines: list[str] = []
    for raw_line, structural_line in zip(raw_lines[header:], structural_lines[header:]):
        if not structural_line.strip().startswith("|"):
            break
        table_lines.append(raw_line)
    header = 0
    separator = (
        split_markdown_table_row(table_lines[header + 1])
        if header + 1 < len(table_lines)
        else None
    )
    if (
        separator is None
        or len(separator) != len(CHECKPOINT_HEADERS)
        or any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in separator)
    ):
        raise ValueError("TASKS checkpoint table separator is invalid")
    rows: list[CheckpointReceiptRow] = []
    for line in table_lines[header + 2 :]:
        cells = split_markdown_table_row(line)
        if cells is None or len(cells) != len(CHECKPOINT_HEADERS):
            raise ValueError("TASKS checkpoint rows must have exactly eight cells")
        cleaned = [clean_cell(cell) for cell in cells]
        if cleaned[0] == "NONE":
            continue
        if CHECKPOINT_ID.fullmatch(cleaned[0]) is None:
            raise ValueError(f"Invalid checkpoint table ID: {cleaned[0]!r}")
        rows.append(CheckpointReceiptRow(*cleaned))
    identifiers = [row.checkpoint_id for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Checkpoint table IDs must be unique")
    ordinals = [int(identifier.split("-", 1)[1]) for identifier in identifiers]
    if ordinals != sorted(ordinals) or len(ordinals) != len(set(ordinals)):
        raise ValueError("Checkpoint table IDs must be strictly monotonic")
    return rows


def parse_checkpoint_git_receipt(
    tasks_text: str,
    checkpoint_id: str,
) -> tuple[str, list[str]]:
    rows = parse_checkpoint_rows(tasks_text)
    matches = [row for row in rows if row.checkpoint_id == checkpoint_id]
    if not rows or len(matches) != 1 or rows[-1].checkpoint_id != checkpoint_id:
        raise ValueError(f"{checkpoint_id}: must be the unique newest checkpoint row")
    receipt = matches[0].commit_and_dirty
    match = re.fullmatch(
        r"Commit\s*:\s*`?([0-9a-fA-F]{7,64})`?\s*;\s*Dirty\s*:\s*(.+?)\s*",
        receipt,
        re.IGNORECASE,
    )
    if match is None:
        raise ValueError(
            f"{checkpoint_id}: commit receipt must use Commit: <sha>; Dirty: <paths|NONE>"
        )
    dirty_value = match.group(2).replace("`", "").strip()
    dirty = (
        []
        if dirty_value == "NONE"
        else parse_task_write_set(dirty_value, f"{checkpoint_id} checkpoint Dirty paths")
    )
    return match.group(1), dirty


def validate_checkpoint_record(
    ctx: Context,
    tasks_text: str,
    snapshot: dict[str, str],
    tasks: list[InspectedTask],
    verify_text: str | None,
) -> None:
    checkpoint_id = snapshot.get("Last checkpoint", "")
    try:
        rows = parse_checkpoint_rows(tasks_text)
        matching = [row for row in rows if row.checkpoint_id == checkpoint_id]
        if not rows or len(matching) != 1 or rows[-1].checkpoint_id != checkpoint_id:
            raise ValueError(f"{checkpoint_id}: must be the unique newest checkpoint row")
        row = matching[0]
        if row.run_id != snapshot.get("Active run ID"):
            raise ValueError(f"{checkpoint_id}: checkpoint run does not match the snapshot")
        if not explicit_timestamp(row.recorded_at):
            raise ValueError(f"{checkpoint_id}: checkpoint time must be ISO 8601 with timezone")
        for prefix, expected in (
            ("REQ", snapshot.get("Requirements revision", "")),
            ("DES", snapshot.get("Design revision", "")),
            ("AUTH", snapshot.get("Construction authorization", "")),
        ):
            if re.findall(rf"\b{prefix}-\d{{4,}}\b", row.basis) != [expected]:
                raise ValueError(f"{checkpoint_id}: checkpoint REQ/DES/AUTH basis is not current")
        parse_checkpoint_git_receipt(tasks_text, checkpoint_id)
        if not explicit_value(row.task_outcomes):
            raise ValueError(f"{checkpoint_id}: task outcomes and attempts are unresolved")
        for task in tasks:
            token = re.compile(
                rf"(?<![A-Za-z0-9-]){re.escape(task.task_id)}(?![A-Za-z0-9-])"
            )
            segments = [
                segment.strip()
                for segment in re.split(r"[;\n]", row.task_outcomes)
                if token.search(segment) is not None
            ]
            if len(segments) != 1 or re.search(
                rf"\b{re.escape(task.status)}\b", segments[0]
            ) is None:
                raise ValueError(f"{checkpoint_id}: outcome for {task.task_id} is not current")
            attempt = re.compile(
                rf"\battempts?(?:\s+used)?\s*[=:]\s*{task.attempts_used}"
                rf"(?:\s*/\s*{task.attempt_budget})?(?!\s*/\s*\d)\b",
                re.IGNORECASE,
            )
            if attempt.search(segments[0]) is None:
                raise ValueError(f"{checkpoint_id}: attempts for {task.task_id} are not current")
        if (
            not explicit_value(row.evidence_and_external)
            or re.search(r"\bevidence\b", row.evidence_and_external, re.IGNORECASE) is None
            or re.search(r"\bexternal\b", row.evidence_and_external, re.IGNORECASE) is None
        ):
            raise ValueError(f"{checkpoint_id}: evidence and external actions are unresolved")
        evidence_cell = row.evidence_and_external
        for task in tasks:
            references = [
                match.group(0)
                for match in EVIDENCE_PATTERN.finditer(
                    clean_cell(task.metadata.get("Evidence", ""))
                )
            ]
            if any(
                re.search(
                    rf"(?<![A-Za-z0-9._-]){re.escape(reference)}(?![A-Za-z0-9._-])",
                    evidence_cell,
                    re.IGNORECASE,
                )
                is None
                for reference in references
            ):
                raise ValueError(f"{checkpoint_id}: evidence for {task.task_id} is incomplete")
        if (
            not explicit_value(row.blockers_and_next)
            or re.search(r"\bblockers?\b", row.blockers_and_next, re.IGNORECASE) is None
            or re.search(r"\bnext\b", row.blockers_and_next, re.IGNORECASE) is None
        ):
            raise ValueError(f"{checkpoint_id}: blockers and next action are unresolved")
        structural_verify = without_fenced_code(verify_text) if verify_text is not None else ""
        if re.search(
            rf"(?<![A-Za-z0-9-]){re.escape(checkpoint_id)}(?![A-Za-z0-9-])",
            structural_verify,
        ) is None:
            raise ValueError(f"{checkpoint_id}: checkpoint is not referenced in VERIFY.md")
    except (KeyError, ValueError) as exc:
        ctx.error("CONSTRUCTION_CHECKPOINT_UNVERIFIED", str(exc), TASKS_FILE)


def validate_authorized_baseline_repository(ctx: Context, baseline: str) -> None:
    """Prove Gate B's full authorized baseline resolves in a regular worktree."""

    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", baseline) is None:
        return
    try:
        inside = git_read(ctx.root, "rev-parse", "--is-inside-work-tree")
        bare = git_read(ctx.root, "rev-parse", "--is-bare-repository")
        resolved = git_read(ctx.root, "rev-parse", "--verify", f"{baseline}^{{commit}}")
    except (OSError, subprocess.SubprocessError) as exc:
        ctx.error(
            "GATE_B_GIT_UNVERIFIED",
            f"Unable to inspect the authorized Git baseline read-only: {exc}",
            PRD_FILE,
        )
        return
    if (
        inside.returncode != 0
        or inside.stdout.strip() != b"true"
        or bare.returncode != 0
        or bare.stdout.strip() != b"false"
    ):
        ctx.error(
            "GATE_B_GIT_UNVERIFIED",
            "Gate B requires a regular local Git worktree",
            PRD_FILE,
        )
        return
    if resolved.returncode != 0 or resolved.stdout.decode("ascii", errors="replace").strip() != baseline:
        ctx.error(
            "GATE_B_GIT_UNVERIFIED",
            "Authorized baseline commit does not resolve exactly in this repository",
            PRD_FILE,
        )


def validate_construction_repository(
    ctx: Context,
    snapshot: dict[str, str],
    *,
    tasks_text: str | None,
    reconcile_worktree: bool,
) -> None:
    """Prove construction Git history and, at checkpoints, current dirty state."""

    baseline = snapshot.get("Baseline commit", "")
    known_green = snapshot.get("Last known-green commit", "")
    for label, value in (("Baseline commit", baseline), ("Last known-green commit", known_green)):
        if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
            ctx.error(
                "CONSTRUCTION_GIT_UNVERIFIED",
                f"{label} must be a full lowercase Git commit ID",
                TASKS_FILE,
            )
            return

    checkpoint_commit: str | None = None
    checkpoint_dirty: list[str] | None = None
    if reconcile_worktree and tasks_text is not None:
        checkpoint_id = snapshot.get("Last checkpoint", "")
        if CHECKPOINT_ID.fullmatch(checkpoint_id) is None:
            ctx.error(
                "CONSTRUCTION_CHECKPOINT_UNVERIFIED",
                "Checkpointed construction requires a current checkpoint receipt",
                TASKS_FILE,
            )
            return
        try:
            checkpoint_commit, checkpoint_dirty = parse_checkpoint_git_receipt(
                tasks_text, checkpoint_id
            )
        except ValueError as exc:
            ctx.error("CONSTRUCTION_CHECKPOINT_UNVERIFIED", str(exc), TASKS_FILE)
            return

    try:
        inside = git_read(ctx.root, "rev-parse", "--is-inside-work-tree")
        bare = git_read(ctx.root, "rev-parse", "--is-bare-repository")
        head_result = git_read(ctx.root, "rev-parse", "--verify", "HEAD^{commit}")
        baseline_result = git_read(ctx.root, "rev-parse", "--verify", f"{baseline}^{{commit}}")
        green_result = git_read(ctx.root, "rev-parse", "--verify", f"{known_green}^{{commit}}")
        checkpoint_result = (
            git_read(ctx.root, "rev-parse", "--verify", f"{checkpoint_commit}^{{commit}}")
            if checkpoint_commit is not None
            else None
        )
    except (OSError, subprocess.SubprocessError) as exc:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            f"Unable to inspect construction Git state read-only: {exc}",
            TASKS_FILE,
        )
        return
    if (
        inside.returncode != 0
        or inside.stdout.strip() != b"true"
        or bare.returncode != 0
        or bare.stdout.strip() != b"false"
    ):
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Construction requires a regular local Git worktree",
            TASKS_FILE,
        )
        return
    commit_results = [head_result, baseline_result, green_result]
    if checkpoint_result is not None:
        commit_results.append(checkpoint_result)
    if any(result.returncode != 0 for result in commit_results):
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Authorized baseline, last-known-green, or checkpoint commit cannot be resolved",
            TASKS_FILE,
        )
        return
    resolved_baseline = baseline_result.stdout.decode("ascii", errors="replace").strip()
    resolved_green = green_result.stdout.decode("ascii", errors="replace").strip()
    if resolved_baseline != baseline or resolved_green != known_green:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Construction commit identities must be exact full hashes",
            TASKS_FILE,
        )
        return
    if checkpoint_result is not None and (
        checkpoint_result.stdout.decode("ascii", errors="replace").strip() != resolved_green
    ):
        ctx.error(
            "CONSTRUCTION_CHECKPOINT_UNVERIFIED",
            "Checkpoint receipt commit does not match Last known-green commit",
            TASKS_FILE,
        )
        return

    try:
        baseline_ancestor = git_read(
            ctx.root, "merge-base", "--is-ancestor", baseline, known_green
        )
        green_ancestor = git_read(
            ctx.root, "merge-base", "--is-ancestor", known_green, "HEAD"
        )
        committed = git_read(
            ctx.root,
            "diff",
            "--name-only",
            "-z",
            "--relative",
            f"{known_green}..HEAD",
            "--",
            ".",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            f"Unable to compare construction Git history: {exc}",
            TASKS_FILE,
        )
        return
    if baseline_ancestor.returncode != 0:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Authorized baseline is not an ancestor of Last known-green commit",
            TASKS_FILE,
        )
    if green_ancestor.returncode != 0:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Last known-green commit is not an ancestor of current HEAD",
            TASKS_FILE,
        )
    if committed.returncode != 0:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Unable to enumerate commits after Last known-green",
            TASKS_FILE,
        )
        return
    committed_paths = {
        item.decode("utf-8", errors="surrogateescape")
        for item in committed.stdout.split(b"\0")
        if item
    }
    unauthorized_committed = sorted(committed_paths - COORDINATOR_LEDGER_PATHS)
    if unauthorized_committed:
        ctx.error(
            "CONSTRUCTION_GIT_DRIFT",
            "Commits after Last known-green contain non-ledger paths: "
            + ", ".join(unauthorized_committed),
            TASKS_FILE,
        )

    if not reconcile_worktree:
        return
    try:
        tracked = git_read(ctx.root, "diff", "--name-only", "-z", "--relative", "HEAD", "--", ".")
        untracked = git_read(ctx.root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".")
    except (OSError, subprocess.SubprocessError) as exc:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            f"Unable to enumerate the checkpoint worktree: {exc}",
            TASKS_FILE,
        )
        return
    if tracked.returncode != 0 or untracked.returncode != 0:
        ctx.error(
            "CONSTRUCTION_GIT_UNVERIFIED",
            "Unable to enumerate the checkpoint worktree",
            TASKS_FILE,
        )
        return
    observed = {
        item.decode("utf-8", errors="surrogateescape")
        for payload in (tracked.stdout, untracked.stdout)
        for item in payload.split(b"\0")
        if item
    }
    observed_nonledger = observed - COORDINATOR_LEDGER_PATHS
    protected_value = snapshot.get("Protected dirty paths", "NONE")
    try:
        protected = (
            []
            if protected_value == "NONE"
            else parse_task_write_set(protected_value, "Protected dirty paths")
        )
    except ValueError as exc:
        ctx.error("CONSTRUCTION_GIT_UNVERIFIED", str(exc), TASKS_FILE)
        return
    if checkpoint_dirty is not None and {
        item.casefold() for item in checkpoint_dirty
    } != {item.casefold() for item in protected}:
        ctx.error(
            "CONSTRUCTION_CHECKPOINT_UNVERIFIED",
            "Checkpoint Dirty paths do not match Protected dirty paths",
            TASKS_FILE,
        )
    uncovered = sorted(
        path
        for path in observed_nonledger
        if not any(path_boundary_contains(boundary, path) for boundary in protected)
    )
    unused = sorted(
        boundary
        for boundary in protected
        if not any(path_boundary_contains(boundary, path) for path in observed_nonledger)
    )
    if uncovered or unused:
        details: list[str] = []
        if uncovered:
            details.append("unrecorded dirty paths=" + ", ".join(uncovered))
        if unused:
            details.append("recorded paths not dirty=" + ", ".join(unused))
        ctx.error(
            "CONSTRUCTION_WORKTREE_DRIFT",
            "Checkpoint protected paths do not exactly match the worktree: "
            + "; ".join(details),
            TASKS_FILE,
        )


def validate_resume_repository(
    ctx: Context,
    snapshot: dict[str, str],
    tasks_text: str | None = None,
) -> None:
    """Compatibility entry point for conservative checkpoint reconciliation."""

    validate_construction_repository(
        ctx,
        snapshot,
        tasks_text=tasks_text,
        reconcile_worktree=True,
    )


def validate_tasks(
    ctx: Context,
    state: dict[str, Any],
    prd_fields: dict[str, str],
    envelope: dict[str, str],
) -> TaskSummary:
    summary = TaskSummary()
    text = ctx.texts.get(TASKS_FILE) or safe_read_text(ctx, TASKS_FILE)
    if text is None:
        return summary
    try:
        snapshot = table_after_heading(text, "## Active execution snapshot")
    except ValueError as exc:
        ctx.error("TASK_SNAPSHOT", str(exc), TASKS_FILE)
        return summary

    if set(snapshot) != SNAPSHOT_FIELDS:
        missing = sorted(SNAPSHOT_FIELDS - set(snapshot))
        extra = sorted(set(snapshot) - SNAPSHOT_FIELDS)
        details: list[str] = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if extra:
            details.append("unexpected=" + ", ".join(extra))
        ctx.error("TASK_SNAPSHOT", "Active execution snapshot fields must be exact: " + "; ".join(details), TASKS_FILE)

    run_state = snapshot.get("Run state", "")
    if run_state not in SNAPSHOT_RUN_STATES:
        ctx.error("TASK_SNAPSHOT", f"Invalid Run state {run_state!r}", TASKS_FILE)
    try:
        snapshot_workers = int(snapshot.get("Maximum workers", ""))
        if snapshot_workers < 1:
            raise ValueError
    except ValueError:
        ctx.error("TASK_SNAPSHOT", "Maximum workers must be a positive integer", TASKS_FILE)
    active_run_id = snapshot.get("Active run ID", "")
    coordinator = snapshot.get("Coordinator", "")
    if run_state == "NOT_STARTED":
        if active_run_id != "NONE" or coordinator != "UNASSIGNED":
            ctx.error("TASK_SNAPSHOT", "NOT_STARTED requires no run ID and an unassigned coordinator", TASKS_FILE)
    else:
        if RUN_ID.fullmatch(active_run_id) is None or coordinator in {"", "NONE", "UNASSIGNED", "TODO"}:
            ctx.error("TASK_SNAPSHOT", "An active or checkpointed run requires a RUN ID and coordinator", TASKS_FILE)
    current_wave = snapshot.get("Current wave", "")
    if current_wave != "NONE" and re.fullmatch(r"[1-9]\d*", current_wave) is None:
        ctx.error("TASK_SNAPSHOT", "Current wave must be NONE or a positive integer", TASKS_FILE)
    checkpoint = snapshot.get("Last checkpoint", "")
    if run_state in {"PAUSED", "BLOCKED", "COMPLETE"}:
        if CHECKPOINT_ID.fullmatch(checkpoint) is None:
            ctx.error("TASK_SNAPSHOT", f"{run_state} requires a checkpoint ID", TASKS_FILE)
    elif checkpoint != "NONE":
        ctx.error("TASK_SNAPSHOT", f"{run_state or 'unknown run state'} must not claim a checkpoint", TASKS_FILE)
    try:
        if snapshot.get("Protected dirty paths") != "NONE":
            parse_task_write_set(snapshot.get("Protected dirty paths", ""), "Protected dirty paths")
    except ValueError as exc:
        ctx.error("TASK_SNAPSHOT", str(exc), TASKS_FILE)
    if not explicit_value(snapshot.get("Next safe action", ""), allow_none=False):
        ctx.error("TASK_SNAPSHOT", "Next safe action must be explicit", TASKS_FILE)
    if snapshot.get("Gate B state") == "APPROVED_FOR_CONSTRUCTION":
        for key in ("Baseline commit", "Last known-green commit"):
            if re.fullmatch(
                r"(?:[0-9a-f]{40}|[0-9a-f]{64})", snapshot.get(key, "")
            ) is None:
                ctx.error(
                    "TASK_SNAPSHOT",
                    f"Current Gate B requires a full lowercase {key}",
                    TASKS_FILE,
                )

    raw_plan = snapshot.get("Task-plan revision", "")
    summary.plan_state = snapshot.get("Task-plan state", "")
    summary.plan_revision = None if raw_plan == "UNINITIALIZED" else raw_plan
    if summary.plan_revision is not None and PLAN_ID.fullmatch(summary.plan_revision) is None:
        ctx.error("TASK_PLAN_STATE", "Task-plan revision must be UNINITIALIZED or PLAN-nnnn", TASKS_FILE)
    if summary.plan_state not in {"UNINITIALIZED", "CURRENT", "STALE"}:
        ctx.error("TASK_PLAN_STATE", "Task-plan state must be UNINITIALIZED, CURRENT, or STALE", TASKS_FILE)
    if summary.plan_revision is None and summary.plan_state != "UNINITIALIZED":
        ctx.error("TASK_PLAN_STATE", "UNINITIALIZED revision requires UNINITIALIZED plan state", TASKS_FILE)
    if summary.plan_revision is not None and summary.plan_state == "UNINITIALIZED":
        ctx.error("TASK_PLAN_STATE", "Initialized revision cannot have UNINITIALIZED plan state", TASKS_FILE)
    execution = state.get("execution") if isinstance(state.get("execution"), dict) else {}
    lifecycle = state.get("lifecycle") if isinstance(state.get("lifecycle"), dict) else {}
    if summary.plan_revision != execution.get("plan_revision"):
        ctx.error("STATE_TASK_DRIFT", "Task-plan revision does not match bootstrap state", TASKS_FILE)
    if summary.plan_state != execution.get("plan_state"):
        ctx.error("STATE_TASK_DRIFT", "Task-plan state does not match bootstrap state", TASKS_FILE)
    snapshot_pairs = {
        "Requirements revision": "requirements_revision",
        "Design revision": "design_revision",
        "Construction authorization": "construction_authorization",
        "Gate B state": "gate_b",
    }
    for snapshot_key, lifecycle_key in snapshot_pairs.items():
        if snapshot.get(snapshot_key) != lifecycle.get(lifecycle_key):
            ctx.error("STATE_TASK_DRIFT", f"{snapshot_key} does not match lifecycle state", TASKS_FILE)

    run_map = {
        "IDLE": "NOT_STARTED",
        "RUNNING": "RUNNING",
        "CHECKPOINTED": "PAUSED",
        "BLOCKED": "BLOCKED",
        "COMPLETE": "COMPLETE",
    }
    execution_state = execution.get("state") if isinstance(execution.get("state"), str) else ""
    expected_run = run_map.get(execution_state)
    if expected_run is not None and snapshot.get("Run state") != expected_run:
        ctx.error("STATE_TASK_DRIFT", "Run state does not match bootstrap state", TASKS_FILE)
    expected_run_id = execution.get("run_id") or "NONE"
    if snapshot.get("Active run ID") != expected_run_id:
        ctx.error("STATE_TASK_DRIFT", "Active run ID does not match bootstrap state", TASKS_FILE)
    expected_coordinator = execution.get("coordinator") or "UNASSIGNED"
    if snapshot.get("Coordinator") != expected_coordinator:
        ctx.error("STATE_TASK_DRIFT", "Coordinator does not match bootstrap state", TASKS_FILE)

    verify_text = ctx.texts.get(VERIFY_FILE) or safe_read_text(ctx, VERIFY_FILE)
    try:
        tasks, _by_id, ready = validate_task_records(text, snapshot, verify_text)
    except ValueError as exc:
        ctx.error("TASK_GRAPH_INVALID", str(exc), TASKS_FILE)
        return summary

    if summary.plan_revision is None and tasks:
        ctx.error("TASK_PLAN_STATE", "UNINITIALIZED task plan contains task blocks", TASKS_FILE)
    if summary.plan_revision is not None and not tasks:
        ctx.error("TASK_PLAN_STATE", "Initialized task plan contains no task blocks", TASKS_FILE)
    if summary.plan_state == "CURRENT" and prd_fields.get("gate_b") != "APPROVED_FOR_CONSTRUCTION":
        ctx.error("TASK_PLAN_STATE", "CURRENT task plan requires current Gate B", TASKS_FILE)
    if summary.plan_state == "STALE" and any(task.status in {"READY", "IN_PROGRESS"} for task in tasks):
        ctx.error("TASK_PLAN_STATE", "STALE task plan cannot contain runnable or active tasks", TASKS_FILE)

    summary.statuses = {task.task_id: task.status for task in tasks}
    summary.active = sorted(task.task_id for task in tasks if task.status == "IN_PROGRESS")
    summary.ready = sorted(ready)

    state_active_value = execution.get("active_tasks")
    state_active = (
        sorted(state_active_value)
        if isinstance(state_active_value, list) and all(isinstance(item, str) for item in state_active_value)
        else []
    )
    if summary.active != state_active:
        ctx.error("STATE_TASK_DRIFT", "active_tasks does not match IN_PROGRESS task records", STATE_FILE)
    task_attempts = {task.task_id: task.attempts_used for task in tasks}
    if execution.get("attempts") != task_attempts:
        ctx.error("STATE_TASK_DRIFT", "attempt counters do not match task records", STATE_FILE)
    state_checkpoint = execution.get("last_checkpoint")
    expected_checkpoint = (
        state_checkpoint.get("id")
        if isinstance(state_checkpoint, dict)
        else "NONE"
    )
    if snapshot.get("Last checkpoint") != expected_checkpoint:
        ctx.error("STATE_TASK_DRIFT", "Last checkpoint does not match bootstrap state", TASKS_FILE)

    basis = execution.get("basis")
    if basis is not None:
        expected_basis = {
            "requirements_revision": prd_fields.get("requirements_revision"),
            "design_revision": prd_fields.get("design_revision"),
            "construction_authorization": prd_fields.get("construction_authorization"),
        }
        if basis != expected_basis:
            ctx.error("RUN_BASIS_STALE", "Execution basis does not match current PRD revisions", STATE_FILE)
    if prd_fields.get("gate_b") == "APPROVED_FOR_CONSTRUCTION" or tasks:
        validate_tasks_against_envelope(ctx, tasks, snapshot, state, envelope)
    construction_states = {"RUNNING", "CHECKPOINTED", "BLOCKED", "COMPLETE"}
    if execution_state in {"CHECKPOINTED", "BLOCKED", "COMPLETE"}:
        validate_checkpoint_record(ctx, text, snapshot, tasks, verify_text)
    if (
        prd_fields.get("gate_b") == "APPROVED_FOR_CONSTRUCTION"
        or execution_state in construction_states
    ):
        validate_construction_repository(
            ctx,
            snapshot,
            tasks_text=text,
            reconcile_worktree=execution_state in {"CHECKPOINTED", "BLOCKED", "COMPLETE"},
        )
    return summary


def validate_release_decision(ctx: Context) -> str:
    relative = VERIFY_FILE
    text = ctx.texts.get(relative) or safe_read_text(ctx, relative)
    if text is None:
        return "NOT_READY"
    heading = "## Current release decision"
    matches = list(re.finditer(rf"^{re.escape(heading)}[ \t]*$", text, re.MULTILINE))
    if len(matches) != 1:
        ctx.error("RELEASE_DECISION", f"Expected exactly one {heading!r}", relative)
        return "NOT_READY"
    section = text[matches[0].end() :]
    next_heading = re.search(r"^##\s+", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    decisions = re.findall(r"^- Release state:\s*`([^`]+)`\s*$", section, re.MULTILINE)
    if len(decisions) != 1 or decisions[0] not in {
        "NOT_READY",
        "READY_TO_DEPLOY",
        "RELEASE_VERIFIED",
    }:
        ctx.error(
            "RELEASE_DECISION",
            "Release decision must be exactly NOT_READY, READY_TO_DEPLOY, or RELEASE_VERIFIED",
            relative,
        )
        return "NOT_READY"
    return decisions[0]


def derive_route(
    gate_a: str,
    gate_b: str,
    requirements_present: bool,
    gate_b_agent_ready: bool,
    tasks: TaskSummary,
    autonomous_allowed: bool,
    execution_mode: str,
    release_decision: str = "NOT_READY",
) -> tuple[str, str]:
    if gate_a == "STALE":
        return (
            ("REQUIREMENTS_STALE", "REQ-10")
            if requirements_present
            else ("INTAKE_REQUIRED", "INTAKE-10")
        )
    if gate_a == "BLOCKED":
        return ("REQUIREMENTS_ANALYSIS", "REQ-10") if requirements_present else ("INTAKE_REQUIRED", "INTAKE-10")
    if gate_a == "PENDING_OWNER_APPROVAL":
        return "WAITING_GATE_A", "INTAKE-20"
    if gate_a != "APPROVED_FOR_DESIGN":
        return "BLOCKED", "STOP"
    if gate_b == "STALE":
        return "DESIGN_STALE", "DESIGN-10"
    if gate_b == "BLOCKED":
        return ("WAITING_GATE_B", "DESIGN-20") if gate_b_agent_ready else ("DESIGN_REQUIRED", "DESIGN-10")
    if gate_b == "PENDING_OWNER_APPROVAL":
        return "WAITING_GATE_B", "DESIGN-20"
    if gate_b != "APPROVED_FOR_CONSTRUCTION":
        return "BLOCKED", "STOP"
    if tasks.plan_state in {"UNINITIALIZED", "STALE"}:
        return "TASK_PLAN_REQUIRED", "TASK-10"
    if tasks.active:
        if execution_mode == "AUTONOMOUS" and autonomous_allowed:
            return "CONSTRUCTION_AUTONOMOUS", "BUILD-20"
        if len(tasks.active) == 1:
            return "CONSTRUCTION_SINGLE", "BUILD-10"
        return "BLOCKED", "STOP"
    if len(tasks.ready) == 1:
        return "CONSTRUCTION_SINGLE", "BUILD-10"
    if len(tasks.ready) > 1:
        if autonomous_allowed:
            return "CONSTRUCTION_AUTONOMOUS", "BUILD-20"
        return "BLOCKED", "STOP"
    if tasks.terminal:
        if release_decision == "READY_TO_DEPLOY":
            return "AWS_PREFLIGHT_REQUIRED", "AWS-10"
        if release_decision == "RELEASE_VERIFIED":
            return "RELEASE_VERIFIED", "STOP"
        return "RELEASE_REVIEW", "RELEASE-10"
    return "BLOCKED", "STOP"


def inspect_project(root: Path, *, template_source: bool = False) -> dict[str, Any]:
    root = root.resolve()
    ctx = Context(root=root, template_source=template_source)
    if not root.is_dir():
        ctx.error("PROJECT_ROOT", "Project root is not a directory", str(root))
        return build_report(ctx, "BLOCKED", "STOP", {}, TaskSummary())

    manifest = load_json_document(ctx, MANIFEST_FILE, "MANIFEST_PARSE")
    state = load_json_document(ctx, STATE_FILE, "STATE_PARSE")
    if manifest is None or state is None:
        return build_report(
            ctx,
            "BLOCKED",
            "STOP",
            {},
            TaskSummary(),
            manifest=manifest,
            state=state,
        )

    validate_manifest(ctx, manifest)
    state_sections_valid = validate_state_schema(ctx, state)
    validate_prompt_pack(ctx, manifest, state)
    if not state_sections_valid:
        validate_placeholders(ctx)
        return build_report(
            ctx,
            "BLOCKED",
            "STOP",
            {},
            TaskSummary(),
            manifest=manifest,
            state=state,
        )
    prd_fields, envelope, _selections, requirements_present = validate_prd(ctx, state)
    aws_core_rows: dict[str, AwsCoreEvidenceRow] = {}
    verify_text = ctx.texts.get(VERIFY_FILE) or safe_read_text(ctx, VERIFY_FILE)
    if verify_text is not None:
        try:
            aws_core_rows = parse_aws_core_evidence(verify_text)
        except ValueError as exc:
            ctx.error("AWS_CORE_EVIDENCE_STRUCTURE", str(exc), VERIFY_FILE)
    tasks = validate_tasks(ctx, state, prd_fields, envelope)
    release_decision = validate_release_decision(ctx)
    validate_placeholders(ctx)

    gate_a = prd_fields.get("gate_a", "BLOCKED")
    gate_b = prd_fields.get("gate_b", "BLOCKED")
    prd_text = ctx.texts.get(PRD_FILE, "")
    try:
        gate_b_agent = table_after_heading(prd_text, "## 27. Gate B agent review record")
        gate_b_agent_ready = gate_b_agent.get("Agent recommendation") == "READY_FOR_CONSTRUCTION_APPROVAL"
    except ValueError:
        gate_b_agent_ready = False
    if gate_b_agent_ready or gate_b in {
        "PENDING_OWNER_APPROVAL",
        "APPROVED_FOR_CONSTRUCTION",
    }:
        require_aws_core_phase_evidence(
            ctx,
            aws_core_rows,
            "DESIGN-10",
            expected_binding=prd_fields.get("design_revision"),
        )
    lifecycle_state, next_prompt = derive_route(
        gate_a,
        gate_b,
        requirements_present,
        gate_b_agent_ready,
        tasks,
        envelope.get("Autonomous construction") == "ALLOWED",
        state.get("execution", {}).get("mode", "NONE"),
        release_decision,
    )
    aws_execution_planning_ready = False
    aws_10_issues = ["AWS-10 active artifact binding is unresolved"]
    if verify_text is not None:
        try:
            active_scope = table_after_heading(verify_text, "## Active evidence scope")
            artifact_binding = clean_cell(
                active_scope.get("Commit, tag, or image digest", "")
            )
        except ValueError:
            artifact_binding = ""
        if explicit_value(artifact_binding, allow_none=False):
            aws_10_issues = aws_core_phase_evidence_issues(
                aws_core_rows,
                "AWS-10",
                expected_binding=artifact_binding,
            )
            aws_execution_planning_ready = not aws_10_issues
    if next_prompt == "AWS-10":
        if not aws_execution_planning_ready:
            ctx.warning(
                "AWS_CORE_AWS10_EVIDENCE_REQUIRED",
                "AWS-10 must record fresh source-attributed retrieve_skill and "
                "search_documentation evidence bound to the current artifact before "
                "AWS execution planning: " + "; ".join(aws_10_issues),
                VERIFY_FILE,
            )
    if ctx.has_errors:
        lifecycle_state, next_prompt = "BLOCKED", "STOP"
    return build_report(
        ctx,
        lifecycle_state,
        next_prompt,
        prd_fields,
        tasks,
        manifest=manifest,
        state=state,
        release_decision=release_decision,
        envelope=envelope,
        aws_execution_planning_ready=aws_execution_planning_ready,
    )


def inspect_git_baseline(root: Path) -> str:
    """Return the current commit or PENDING without changing Git state."""

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "PENDING"
    if result.returncode != 0:
        return "PENDING"
    commit = result.stdout.strip()
    return commit if re.fullmatch(r"[0-9a-fA-F]{40,64}", commit) else "PENDING"


def build_report(
    ctx: Context,
    lifecycle_state: str,
    next_prompt: str,
    prd_fields: dict[str, str],
    tasks: TaskSummary,
    *,
    manifest: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    release_decision: str = "NOT_READY",
    envelope: dict[str, str] | None = None,
    aws_execution_planning_ready: bool = False,
) -> dict[str, Any]:
    manifest = manifest or {}
    state = state or {}
    setup = state.get("setup") if isinstance(state.get("setup"), dict) else {}
    project = state.get("project") if isinstance(state.get("project"), dict) else {}
    lifecycle = (
        state.get("lifecycle") if isinstance(state.get("lifecycle"), dict) else {}
    )
    envelope = envelope or {}
    if ctx.template_source:
        classification = "TEMPLATE_SOURCE"
    elif setup.get("status") == "UNCONFIGURED_TEMPLATE":
        classification = "UNCONFIGURED_TEMPLATE"
    elif project.get("mode") == "brownfield":
        classification = "ACTIVE_BROWNFIELD"
    else:
        classification = "ACTIVE_GREENFIELD"
    if ctx.has_errors:
        status = "BLOCKED"
    elif lifecycle_state == "INTAKE_REQUIRED":
        status = "READY"
    else:
        status = "RESUME"
    lane = project.get("aws_lane")
    aws_access = {
        None: "NOT_USED",
        "documentation-only": "DOCUMENTATION_ONLY",
        "read-only": "READ_ONLY",
        "fast-dev": "AUTHORIZED_BOUNDARY_REQUIRED",
        "explicit-gate": "EXACT_AUTHORIZATION_REQUIRED",
    }.get(lane, "NOT_USED")
    gate_a = prd_fields.get("gate_a") or lifecycle.get("gate_a") or "BLOCKED"
    gate_b = prd_fields.get("gate_b") or lifecycle.get("gate_b") or "BLOCKED"
    authorization_id = (
        prd_fields.get("construction_authorization")
        or lifecycle.get("construction_authorization")
    )
    construction_authorization = (
        authorization_id
        if not ctx.has_errors and gate_b == "APPROVED_FOR_CONSTRUCTION"
        else "NONE"
    )
    aws_boundary = envelope.get("AWS boundary", "NONE")
    aws_authorization = (
        authorization_id
        if not ctx.has_errors
        and gate_b == "APPROVED_FOR_CONSTRUCTION"
        and aws_boundary in {"READ_ONLY", "MUTATE_LISTED_RESOURCES"}
        else "NONE"
    )
    return {
        "schema_version": 1,
        "bootstrap_version": manifest.get(
            "bootstrap_version", state.get("bootstrap_version")
        ),
        "status": status,
        "classification": classification,
        "ok": not ctx.has_errors,
        "lifecycle_state": lifecycle_state,
        "resume_safe": not ctx.has_errors,
        "next_prompt": next_prompt,
        "project": {
            "name": project.get("name"),
            "region": project.get("region"),
            "cost_posture": project.get("cost_posture"),
            "mode": project.get("mode"),
            "delivery_profile": project.get("delivery_profile"),
        },
        "git_baseline": inspect_git_baseline(ctx.root),
        "aws_access": aws_access,
        "gates": {
            "gate_a": gate_a,
            "gate_b": gate_b,
        },
        "evidence_state": release_decision,
        "aws_core_evidence": {
            "aws_execution_planning": (
                "READY" if aws_execution_planning_ready else "BLOCKED"
            )
        },
        "authorizations": {
            "construction": construction_authorization,
            "aws": aws_authorization,
        },
        "basis": {
            "requirements_revision": prd_fields.get("requirements_revision"),
            "design_revision": prd_fields.get("design_revision"),
            "construction_authorization": prd_fields.get("construction_authorization"),
        },
        "tasks": {
            "total": tasks.total,
            "ready": len(tasks.ready),
            "in_progress": len(tasks.active),
        },
        "diagnostics": [item.to_dict() for item in ctx.diagnostics],
    }


def print_human(report: dict[str, Any]) -> None:
    status = "PASS" if report["ok"] else "BLOCKED"
    basis = report["basis"]
    print(f"AWS Codex Fastlane Doctor: {status}")
    print(f"Classification: {report['classification']}")
    print(f"Lifecycle: {report['lifecycle_state']}")
    print(
        "Basis: "
        f"{basis.get('requirements_revision') or 'NONE'} / "
        f"{basis.get('design_revision') or 'NONE'} / "
        f"{basis.get('construction_authorization') or 'NONE'}"
    )
    print(f"Resume safe: {'yes' if report['resume_safe'] else 'no'}")
    print(f"Next prompt: {report['next_prompt']}")
    print(f"Git baseline: {report['git_baseline']}")
    print(f"AWS access: {report['aws_access']}")
    print(f"Gate A: {report['gates']['gate_a']}")
    print(f"Gate B: {report['gates']['gate_b']}")
    print(f"Evidence: {report['evidence_state']}")
    print(
        "AWS execution planning: "
        f"{report['aws_core_evidence']['aws_execution_planning']}"
    )
    print(f"AWS authorization: {report['authorizations']['aws']}")
    for item in report["diagnostics"]:
        location = f" ({item['path']})" if item.get("path") else ""
        print(f"{item['severity']} {item['code']}{location}: {item['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only AWS Codex Fastlane project doctor")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root (defaults to the bootstrap project containing this script)",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    parser.add_argument(
        "--template-source",
        action="store_true",
        help="Allow unresolved render tokens in the reusable template source",
    )
    args = parser.parse_args(argv)
    report = inspect_project(args.root, template_source=args.template_source)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
