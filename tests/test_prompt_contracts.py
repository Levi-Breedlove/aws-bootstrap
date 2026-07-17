from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPOSITORY_ROOT / "my-project"
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
        self.assertIn("Update both\natomically", gate_a)
        self.assertIn("Update both\natomically", gate_b)

    def test_launchpad_routes_from_existing_lifecycle_state(self) -> None:
        boot = self.prompt_section("BOOT-00")
        self.assertIn("Determine lifecycle state", boot)
        self.assertIn("Gate A awaits a current owner receipt: INTAKE-20", boot)
        self.assertIn("Gate B approved and tasks absent: TASK-10", boot)
        self.assertIn("Only when the state-derived next prompt is INTAKE-10", boot)

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
        self.assertEqual(manifest["bootstrap_version"], "2.0.0")
        self.assertEqual(manifest["canonical_prompt_ids"], PROMPT_IDS)
        self.assertIn("**Pack version:** 2.0.0", self.prompts)
        missing = [
            path
            for path in manifest["required_files"]
            if not (PROJECT_ROOT / path).is_file()
        ]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
