from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPOSITORY_ROOT
PROMPT_PACK = PROJECT_ROOT / "prompts" / "CODEX-PROMPTS.md"

PROMPT_IDS = [
    "BOOT-00",
    "INTAKE-10",
    "REQ-10",
    "INTAKE-20",
    "DESIGN-10",
    "DESIGN-20",
    "BUG-10",
    "TASK-10",
    "BUILD-10",
    "BUILD-20",
    "SYNC-10",
    "RELEASE-10",
    "AWS-10",
    "AWS-20",
    "AWS-30",
    "AWS-40",
    "AWS-50",
    "LEARN-10",
]

CONTRACT_LABELS = [
    "Preconditions",
    "Authoritative inputs",
    "Permitted writes",
    "GitHub mode",
    "AWS mode",
    "Required authorization",
    "Stop conditions",
    "Receipt",
    "Next",
]


class PromptPackContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = PROMPT_PACK.read_text(encoding="utf-8")
        cls.prd = (PROJECT_ROOT / "PRD.md").read_text(encoding="utf-8")
        cls.agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.tasks = (PROJECT_ROOT / "TASKS.md").read_text(encoding="utf-8")
        cls.runbook = (PROJECT_ROOT / "RUNBOOK.md").read_text(encoding="utf-8")
        cls.verify = (PROJECT_ROOT / "VERIFY.md").read_text(encoding="utf-8")
        cls.security = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
        cls.root_readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    def prompt_section(self, prompt_id: str) -> str:
        pattern = re.compile(
            rf"^## {re.escape(prompt_id)} — .*?(?=^## [A-Z]+-\d+ — |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(self.prompts)
        self.assertIsNotNone(match, f"Missing section for {prompt_id}")
        return match.group(0) if match else ""

    def test_stable_prompt_ids_are_unique_and_ordered(self) -> None:
        positions: list[int] = []
        for prompt_id in PROMPT_IDS:
            heading = re.compile(rf"^## {re.escape(prompt_id)} — ", re.MULTILINE)
            matches = list(heading.finditer(self.prompts))
            self.assertEqual(
                len(matches),
                1,
                f"Expected one canonical heading for {prompt_id}",
            )
            positions.append(matches[0].start())
        self.assertEqual(positions, sorted(positions))

    def test_every_prompt_declares_the_common_contract(self) -> None:
        for prompt_id in PROMPT_IDS:
            section = self.prompt_section(prompt_id)
            for label in CONTRACT_LABELS:
                self.assertIn(label, section, f"{prompt_id} is missing {label}")

    def test_human_gate_receipts_are_exact_and_owner_only(self) -> None:
        for document in (self.prompts, self.prd):
            self.assertIn("APPROVE REQUIREMENTS GATE A", document)
            self.assertIn("APPROVE PRD AND CONSTRUCTION GATE B", document)
            self.assertIn("Accepted assumptions:", document)
            self.assertIn("Construction authorization:", document)

        self.assertIn("Only the owner", self.prompts)
        self.assertIn("Only the owner", self.agents)
        for reserved in ("`Codex`", "`agent`", "`automation`", "`system`", "`AI`"):
            self.assertIn(reserved, self.prd)
            self.assertIn(reserved, self.prompts)

    def test_gate_and_revision_vocabulary_does_not_drift(self) -> None:
        required = {
            "READY_WITH_PROPOSED_ASSUMPTIONS",
            "READY_FOR_OWNER_APPROVAL",
            "READY_FOR_CONSTRUCTION_APPROVAL",
            "APPROVED_FOR_DESIGN",
            "APPROVED_FOR_CONSTRUCTION",
            "STALE",
        }
        for value in required:
            self.assertIn(value, self.prd)
            self.assertIn(value, self.prompts)

        for document in (self.agents, self.prd, self.prompts):
            self.assertNotIn("READY_WITH_ACCEPTED_ASSUMPTIONS", document)

    def test_tool_access_is_not_authorization(self) -> None:
        self.assertIn("Tool availability is never authorization", self.prompts)
        self.assertIn("Credentials and connector availability are not authorization", self.agents)

    def test_markdown_fences_and_launch_commands_are_complete(self) -> None:
        self.assertEqual(self.prompts.count("~~~") % 2, 0)
        self.assertEqual(self.prd.count("```") % 2, 0)
        self.assertIn("START AWS CODEX BOOTSTRAP", self.prompts)
        self.assertIn("START GUIDED INTAKE", self.prompts)

    def test_receipts_require_complete_normalized_block_equality(self) -> None:
        self.assertIn("equal to this complete", self.prompts)
        self.assertIn("after trimming surrounding whitespace", self.prompts)
        self.assertIn("Reject extra non-blank", self.prompts)
        self.assertNotIn("response begins exactly", self.prompts)

    def test_gate_writes_keep_prd_summary_and_records_atomic(self) -> None:
        requirements = self.prompt_section("REQ-10")
        gate_a = self.prompt_section("INTAKE-20")
        design = self.prompt_section("DESIGN-10")
        gate_b = self.prompt_section("DESIGN-20")

        self.assertIn("Document status requirements revision", requirements)
        self.assertIn("derived Gate A/Gate B states", requirements)
        self.assertIn("matching Document\nstatus Gate A state", gate_a)
        self.assertIn("Document status DES/AUTH/design/Gate B fields", design)
        self.assertIn("matching Document\nstatus Gate B state", gate_b)
        self.assertIn("lifecycle mirror as one coordinator\ncheckpoint", gate_a)
        self.assertIn("lifecycle mirror as one coordinator checkpoint", gate_b)

    def test_ready_recommendations_transition_to_pending_and_sync_snapshot(self) -> None:
        requirements = self.prompt_section("REQ-10")
        design = self.prompt_section("DESIGN-10")
        gate_b = self.prompt_section("DESIGN-20")

        self.assertIn("Gate A owner state to `PENDING_OWNER_APPROVAL`", requirements)
        self.assertIn("TASKS.md's Active execution snapshot", requirements)
        self.assertIn("Gate B state to\n`PENDING_OWNER_APPROVAL`", design)
        self.assertIn("maximum\nworkers, baseline, and protected dirty paths", design)
        self.assertIn("TASKS.md Active execution snapshot", gate_b)
        self.assertIn("APPROVED_FOR_CONSTRUCTION", gate_b)
        self.assertRegex(
            self.agents,
            r"Do not leave\s+an agent-ready gate marked `BLOCKED`",
        )

    def test_stale_gates_have_recovery_routes(self) -> None:
        boot = self.prompt_section("BOOT-00")
        self.assertIn("Gate A is STALE: INTAKE-10", boot)
        self.assertIn("otherwise REQ-10", boot)
        self.assertIn("Gate A is current and Gate B is STALE: DESIGN-10", boot)
        self.assertIn("stale Gate B with a current Gate A routes to `DESIGN-10`", self.agents)

    def test_gate_receipts_record_provenance_without_extra_lines(self) -> None:
        gate_a = self.prompt_section("INTAKE-20")
        gate_b = self.prompt_section("DESIGN-20")
        for section in (gate_a, gate_b):
            self.assertIn("observed ISO 8601 authorization time", section)
            self.assertRegex(section, r"without\s+adding either value to the receipt")
            self.assertIn("Do not invent a source", section)
        self.assertIn("Authorization provided at", self.prd)
        self.assertIn("Authorization source", self.prd)
        self.assertIn("subset, superset, reordered list", self.prd)

    def test_launchpad_routes_from_existing_lifecycle_state(self) -> None:
        boot = self.prompt_section("BOOT-00")
        self.assertIn("Determine lifecycle state", boot)
        self.assertIn("Gate A awaits a current owner receipt: INTAKE-20", boot)
        self.assertIn(
            "Gate B approved and Task-plan state is UNINITIALIZED or STALE: TASK-10",
            boot,
        )
        self.assertIn("Only when the state-derived next prompt is INTAKE-10", boot)

    def test_launchpad_and_build_use_executable_safety_controls(self) -> None:
        boot = self.prompt_section("BOOT-00")
        tasks = self.prompt_section("TASK-10")
        build = self.prompt_section("BUILD-20")

        self.assertIn("Never use `--force`", boot)
        self.assertIn("bootstrap_doctor.py", boot)
        self.assertIn("hash-bound decision", boot)
        self.assertIn("Task-plan revision", tasks)
        self.assertIn("explicit skipped-dependency waivers", tasks)
        self.assertIn("durable coordinator run ID", build)
        self.assertIn("isolated worktrees", build)
        self.assertIn("UNKNOWN", build)

    def test_run_lifecycle_commands_are_complete_and_mode_specific(self) -> None:
        single = self.prompt_section("BUILD-10")
        autonomous = self.prompt_section("BUILD-20")
        common_claim = (
            "--claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 "
            "--coordinator codex-coordinator --checkpoint CP-0000"
        )
        self.assertIn("--start-run RUN-0001 --coordinator codex-coordinator --run-mode SINGLE_TASK", single)
        self.assertIn(common_claim, single)
        self.assertIn("--pause-run RUN-0001 --coordinator codex-coordinator --checkpoint CP-0002", single)
        self.assertIn("--set-status TASK-0001 DONE --evidence EV-0001 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0001", single)
        self.assertIn("--complete-run RUN-0001 --coordinator codex-coordinator", single)
        self.assertIn("--resume-run RUN-0001 --coordinator codex-coordinator", single)
        self.assertIn("--start-run RUN-0001 --coordinator codex-coordinator --run-mode AUTONOMOUS", autonomous)
        self.assertIn("--safe-ready --isolated-worktrees --json", autonomous)
        self.assertIn(common_claim, autonomous)
        self.assertIn(common_claim + " --isolated-worktrees", autonomous)
        self.assertRegex(
            autonomous,
            r"Never\s+run doctor against a persisted RUNNING snapshot",
        )

    def test_aws_mutations_use_canonical_prompts_and_exact_action_receipts(self) -> None:
        build_single = self.prompt_section("BUILD-10")
        build_auto = self.prompt_section("BUILD-20")
        preflight = self.prompt_section("AWS-10")
        evidence = self.prompt_section("AWS-30")

        self.assertIn("BUILD-10 never\nexecutes an AWS mutation directly", build_single)
        self.assertIn("Route AWS mutation through AWS-10/AWS-20", build_auto)
        self.assertIn("**AWS mode:** READ_ONLY.", preflight)
        self.assertNotIn("DOCS_ONLY plus", preflight)
        self.assertIn("AUTHORIZE AWS DEPLOYMENT", self.prompts)
        self.assertIn("AUTHORIZE AWS TEARDOWN", self.prompts)
        self.assertIn("AUTHORIZE AWS DEPLOYMENT", self.runbook)
        self.assertIn("AUTHORIZE AWS TEARDOWN", self.runbook)
        self.assertIn("action-authorization evidence", self.runbook)
        self.assertIn("## Action authorization provenance", self.verify)
        self.assertIn("put\n`VERIFIED`, `PENDING_AWS`", evidence)

    def test_profiles_are_overlays_not_additional_gates(self) -> None:
        for document in (self.prompts, self.prd, self.agents):
            self.assertIn("`quick-mvp`", document)
            self.assertIn("`standard`", document)
            self.assertIn("`high-risk`", document)
        self.assertIn("All profiles still use only Gate A and Gate B", self.prompts)
        self.assertIn("without adding lifecycle gates", self.agents)

    def test_owner_facing_profile_and_security_language_is_concrete(self) -> None:
        owner_documents = (
            self.root_readme,
            self.agents,
            self.prd,
            self.tasks,
            self.prompts,
        )
        rejected = (
            "controls " + "ceremony",
            "not weaker " + "security",
            "Deeper " + "threat",
            "threat " + "requirements",
            "privilege-escalation " + "properties",
        )
        for document in owner_documents:
            for phrase in rejected:
                self.assertNotIn(phrase, document)

        for document in (
            self.root_readme,
            self.agents,
            self.prd,
            self.prompts,
        ):
            self.assertRegex(
                document,
                r"A Quick MVP is one small, reversible development release",
            )
            self.assertRegex(
                document,
                r"An AWS lane describes planned access; it does not authorize a\s+change",
            )

        self.assertIn(
            "approved access succeeds and unapproved access is denied",
            self.prd,
        )
        self.assertIn("Invalid, malformed, and oversized inputs are rejected", self.prd)
        self.assertIn("actual discovered defect", self.prd)
        for phrase in (
            "approved access succeeds and unapproved access is denied",
            "secrets stay out of code and logs",
            "invalid or oversized input is rejected",
            "IAM permits only required actions",
            "sensitive data uses approved encryption",
        ):
            self.assertIn(phrase, self.security)

    def test_human_first_documents_label_the_exact_agent_reference(self) -> None:
        documents = {
            "root README": self.root_readme,
            "root AGENTS": self.agents,
            "PRD": self.prd,
            "TASKS": self.tasks,
            "prompt pack": self.prompts,
            "app AGENTS": (PROJECT_ROOT / "app" / "AGENTS.md").read_text(
                encoding="utf-8"
            ),
            "infrastructure AGENTS": (
                PROJECT_ROOT / "infrastructure" / "AGENTS.md"
            ).read_text(encoding="utf-8"),
            "tests AGENTS": (PROJECT_ROOT / "tests" / "AGENTS.md").read_text(
                encoding="utf-8"
            ),
        }
        for name, document in documents.items():
            self.assertRegex(document, r"(?m)^## Agent reference", name)

    def test_readme_uses_one_line_gate_flow(self) -> None:
        gate_line = (
            "Gate A — approve requirements → Gate B — approve the PRD and "
            "construction boundary → Codex builds autonomously inside that boundary."
        )
        self.assertEqual(self.root_readme.count(gate_line), 1)
        self.assertNotIn("| Gate | You approve |", self.root_readme)

    def test_template_first_readme_sets_complete_user_expectations(self) -> None:
        self.assertIn(
            "https://github.com/Levi-Breedlove/aws-bootstrap/generate",
            self.root_readme,
        )
        self.assertIn("Setup: THIS_REPOSITORY", self.root_readme)
        self.assertIn("Local Git setup: USE_EXISTING", self.root_readme)
        self.assertIn("Local Git setup: INIT_AND_BASELINE_COMMIT", self.root_readme)
        self.assertIn("Setup: ADOPT_EXISTING_REPOSITORY", self.root_readme)
        self.assertIn("AWS CODEX FASTLANE — READY", self.root_readme)
        self.assertIn("Classification: ACTIVE_GREENFIELD", self.root_readme)
        self.assertIn("Lifecycle: INTAKE_REQUIRED", self.root_readme)
        self.assertIn("Doctor: PASS", self.root_readme)
        self.assertIn("Next prompt: INTAKE-10", self.root_readme)
        self.assertIn("AWS access: NOT USED", self.root_readme)
        self.assertIn("## What is deterministic and what uses agent judgment", self.root_readme)
        self.assertIn("docs/demo/internal-change-request-api.md", self.root_readme)
        for path in (
            "AGENTS.md",
            "PRD.md",
            "TASKS.md",
            "VERIFY.md",
            "RUNBOOK.md",
            "bootstrap.manifest.json",
            ".agents/skills/",
            "docs/demo/",
        ):
            self.assertIn(path, self.root_readme)
        self.assertFalse((REPOSITORY_ROOT / "my-project" / "README.md").exists())

    def test_boot_prompt_has_stable_template_first_contract(self) -> None:
        boot = self.prompt_section("BOOT-00")
        self.assertIn("START AWS CODEX FASTLANE", boot)
        self.assertIn("Setup: <THIS_REPOSITORY|ADOPT_EXISTING_REPOSITORY>", boot)
        self.assertIn("Ask no more than these three setup questions", boot)
        self.assertIn("--in-place-template-instance --dry-run", boot)
        self.assertIn("UNCONFIGURED_TEMPLATE", boot)
        for field in (
            "Classification:",
            "Lifecycle:",
            "Doctor:",
            "Next prompt:",
            "Git baseline:",
            "AWS access:",
            "Gate A:",
            "Gate B:",
            "Evidence:",
            "AWS authorization:",
        ):
            self.assertIn(field, boot)

    def test_repo_scoped_skills_have_distinct_safe_trigger_contracts(self) -> None:
        implicit = {
            "launch-fastlane": "true",
            "plan-fastlane": "true",
            "build-fastlane": "true",
            "operate-fastlane-aws": "false",
        }
        descriptions: set[str] = set()
        for name, expected_implicit in implicit.items():
            root = REPOSITORY_ROOT / ".agents" / "skills" / name
            skill = (root / "SKILL.md").read_text(encoding="utf-8")
            config = (root / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertTrue(skill.startswith("---\nname: " + name + "\n"))
            description = re.search(r"(?m)^description:\s*(.+)$", skill)
            self.assertIsNotNone(description)
            descriptions.add(description.group(1) if description else "")
            self.assertIn("interface:", config)
            self.assertIn("display_name:", config)
            self.assertIn("short_description:", config)
            self.assertIn("default_prompt:", config)
            self.assertIn(
                f"allow_implicit_invocation: {expected_implicit}",
                config,
            )
            for forbidden in ("model:", "permissions:", "hooks:", "mcp_servers:"):
                self.assertNotIn(forbidden, config)
        self.assertEqual(len(descriptions), len(implicit))
        aws_skill = (
            REPOSITORY_ROOT
            / ".agents"
            / "skills"
            / "operate-fastlane-aws"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Use only when the user explicitly invokes this skill", aws_skill)
        self.assertIn("They never authorize an AWS change", aws_skill)

    def test_task_cards_are_human_first_with_collapsed_exact_metadata(self) -> None:
        self.assertIn("## How to read a task card", self.tasks)
        self.assertIn("- Status: BACKLOG", self.tasks)
        self.assertIn("- Owner: UNASSIGNED", self.tasks)
        self.assertIn("- Blocker: NONE", self.tasks)
        self.assertIn("- GitHub issue: PENDING_SYNC", self.tasks)
        self.assertIn("<details>", self.tasks)
        self.assertIn("Exact metadata used by Codex and task_waves.py", self.tasks)
        required_metadata = (
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
        task_template = self.tasks.split("~~~text", 1)[1].split("~~~", 1)[0]
        for key in required_metadata:
            self.assertEqual(
                task_template.count(f"- {key}:"),
                1,
                f"Task template must contain one {key} metadata line",
            )

    def test_brownfield_adoption_requires_exact_user_confirmation(self) -> None:
        boot = self.prompt_section("BOOT-00")
        self.assertIn("does not\nauthorize you to choose `ADOPT_TEMPLATE`", boot)
        self.assertIn("CONFIRM BOOTSTRAP ADOPTION PLAN", boot)
        self.assertIn("plan_sha256: <64 lowercase hex characters>", boot)
        self.assertIn("authorized_by: <human owner>", boot)
        self.assertIn("authorization_source: OWNER_CONFIRMATION", boot)
        self.assertIn("schema version, roots, and ordered decisions", boot)
        self.assertIn("It never hashes decisions\nalone", boot)
        self.assertIn("complete ordered decision map", self.agents)

    def test_task_prompt_and_ledger_define_validator_shape(self) -> None:
        task_prompt = self.prompt_section("TASK-10")
        for heading in (
            "#### Outcome",
            "#### Acceptance criteria",
            "#### Validation",
            "#### Execution log",
            "#### Agent execution details",
        ):
            self.assertIn(heading, task_prompt)
            self.assertIn(heading, self.tasks)
        self.assertIn("every remaining singleton metadata line", task_prompt)
        self.assertIn("A READY task cannot contain `TODO`", self.tasks)
        self.assertIn("- Dependency waivers: NONE", self.tasks)
        self.assertRegex(
            self.tasks,
            r"#### Validation\n\n```bash\n<exact validation command>\n```",
        )

    def test_readiness_cards_are_complete_and_prompt_filled(self) -> None:
        gate_a_fields = (
            "Outcome",
            "Owner and users",
            "Scope and non-goals",
            "Measurable requirement/acceptance IDs",
            "Data boundary",
            "Identity/security boundary",
            "Environment/Region",
            "Failure/recovery",
            "Cost ceiling",
            "Intake provenance",
        )
        gate_b_fields = (
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
        )
        self.assertIn("### Gate A — readiness card", self.prd)
        self.assertIn("### Gate B — readiness card", self.prd)
        for field in (*gate_a_fields, *gate_b_fields):
            self.assertIn(f"| {field} |", self.prd)
        self.assertIn("Fill the Gate A readiness card with these exact fields", self.prompt_section("REQ-10"))
        self.assertIn("Fill the Gate B readiness card with these exact fields", self.prompt_section("DESIGN-10"))
        self.assertIn("`NOT_APPLICABLE — <reason>`", self.prd)

    def test_gate_b_binds_canonical_complete_envelope_digest(self) -> None:
        receipt_line = "Construction envelope SHA-256: sha256:<64-lowercase-hex>"
        self.assertIn("| Authorized construction envelope SHA-256 |", self.prd)
        self.assertIn("| Construction envelope SHA-256 reviewed |", self.prd)
        self.assertIn(receipt_line, self.prd)
        self.assertEqual(self.prompts.count(receipt_line), 2)
        self.assertIn("header, separator, and every boundary row", self.prd)
        self.assertIn("append one final LF", self.prd)

    def test_construction_envelope_uses_bindable_grammars(self) -> None:
        required_rows = (
            "Project mode",
            "Delivery profile and effective risk",
            "Project AWS lane",
            "Authorized requirement and design IDs",
            "Authorized baseline commit",
            "Protected dirty paths",
            "Allowed external-state targets",
            "Local command boundary",
            "Task boundary",
            "GitHub repository, branch, and merge constraints",
            "Authorization expiry or completion condition",
        )
        for row in required_rows:
            self.assertIn(f"| {row} |", self.prd)
        self.assertIn("`<profile> / <risk>`", self.prd)
        self.assertIn("`ALLOW_PREFIXES: prefix; prefix`", self.prd)
        self.assertIn("`DERIVED_FROM_AUTHORIZED_IDS_AND_WRITE_SET`", self.prd)
        self.assertIn("`REPO: owner/name; BRANCH: branch; MERGE: ALLOWED\\|PROHIBITED`", self.prd)
        self.assertIn(
            "`ENVIRONMENT: <exact name>; CLASS: NON_PRODUCTION\\|PRODUCTION`",
            self.prd,
        )
        self.assertIn("`EXACT_DIGEST: sha256:<64 lowercase hex>`", self.prd)
        self.assertIn(
            "`DERIVED_FROM_AUTHORIZED_SOURCE: SHA-256 from baseline <full authorized commit>; <deterministic rule>`",
            self.prd,
        )
        self.assertIn(
            "`Expires at <ISO 8601 with timezone>; earlier completion: <exact condition>`",
            self.prd,
        )
        for row in (
            "AWS account", "AWS role or profile", "AWS Region", "AWS environment",
            "AWS stack or application", "AWS resource allowlist", "AWS allowed operations",
            "AWS cost ceiling", "AWS prohibited operations",
            "AWS artifact authorization and provenance", "AWS rollback boundary",
            "AWS authorization validity",
        ):
            self.assertIn(f"| {row} |", self.prd)

    def test_git_checkpoint_plan_and_release_lifecycles_are_explicit(self) -> None:
        self.assertIn("| Task-plan state | `UNINITIALIZED` |", self.tasks)
        for state in ("UNINITIALIZED", "CURRENT", "STALE"):
            self.assertIn(state, self.tasks)
        self.assertRegex(self.tasks, r"commits? only authorized wave changes")
        self.assertIn("Last known-green commit", self.tasks)
        for state in ("NOT_READY", "READY_TO_DEPLOY", "RELEASE_VERIFIED"):
            self.assertIn(state, self.verify)
            self.assertIn(state, self.prompt_section("RELEASE-10"))
        self.assertIn("AWS-30 | Reconcile deployed evidence | RELEASE-10", self.prompts)
        self.assertIn("**Next:** RELEASE-10", self.prompt_section("AWS-30"))
        self.assertIn("Local Git setup:", self.prompt_section("BOOT-00"))

    def test_done_requires_structured_observed_local_evidence(self) -> None:
        header = (
            "| Evidence ID | Task | Command or observation | Result | Actor | "
            "Observed at | Commit / worktree / artifact | Durable source | Status |"
        )
        self.assertIn("## Task completion evidence", self.verify)
        self.assertIn(header, self.verify)
        for document in (self.agents, self.tasks, self.prompts):
            self.assertIn("Task completion evidence", document)
        for field in (
            "command/result",
            "actor",
            "commit/worktree/artifact",
            "LOCAL_PASS",
            "VERIFIED",
        ):
            self.assertIn(field, self.prompts)

    def test_brownfield_mandatory_facts_are_not_nullable(self) -> None:
        self.assertIn("every baseline fact is mandatory", self.prd)
        self.assertIn("Only these fields\nare nullable", self.prd)
        self.assertIn("known defects and accepted debt\n`NONE_OBSERVED`", self.prd)
        self.assertIn("Only drift, dirty changes, known debt/defects", self.prompt_section("REQ-10"))

    def test_aws_mode_mapping_is_canonical(self) -> None:
        for document in (self.prompts, self.prd):
            self.assertIn("Project AWS lane", document)
            self.assertIn("Prompt AWS mode", document)
            self.assertIn("Gate B AWS boundary", document)
            self.assertIn("MUTATE_LISTED_RESOURCES", document)
        self.assertNotIn("PLAN_ONLY", self.prd)

    def test_manifest_matches_pack_and_required_files_exist(self) -> None:
        manifest_path = PROJECT_ROOT / "bootstrap.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["bootstrap_version"], "1.0.0")
        self.assertEqual(manifest["canonical_prompt_ids"], PROMPT_IDS)
        self.assertIn("**Pack version:** 1.0.0", self.prompts)
        missing = [
            path
            for path in manifest["required_files"]
            if not (PROJECT_ROOT / path).is_file()
        ]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
