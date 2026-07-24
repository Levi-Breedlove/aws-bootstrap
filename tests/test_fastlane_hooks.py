from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / ".codex" / "hooks" / "fastlane_hook.py"
EXAMPLE_PATH = REPOSITORY_ROOT / ".codex" / "hooks.fastlane.example.json"
SPEC = importlib.util.spec_from_file_location("fastlane_hook", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
fastlane_hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fastlane_hook)


def report(
    *,
    construction: str = "NONE",
    aws: str = "NONE",
    automatic: bool = False,
    owner_action: bool = True,
    formal_receipt: bool = False,
) -> dict[str, object]:
    return {
        "gates": {"gate_a": "BLOCKED", "gate_b": "BLOCKED"},
        "authorizations": {"construction": construction, "aws": aws},
        "interaction": {
            "owner_stage": "DEFINE",
            "owner_action_kind": "ANSWER_OPEN_DECISIONS",
            "automatic_continuation_allowed": automatic,
            "owner_action_required": owner_action,
            "formal_receipt_required": formal_receipt,
        },
    }


def payload(event: str, root: Path, **values: object) -> dict[str, object]:
    result: dict[str, object] = {
        "hook_event_name": event,
        "cwd": str(root),
        "permission_mode": "default",
    }
    result.update(values)
    return result


class FastlaneHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = REPOSITORY_ROOT

    def test_example_is_opt_in_complete_and_cross_platform(self) -> None:
        self.assertFalse((self.root / ".codex" / "hooks.json").exists())
        data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            set(data["hooks"]),
            {"SessionStart", "PreToolUse", "PermissionRequest", "PostToolUse", "Stop"},
        )
        for groups in data["hooks"].values():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertIn("git rev-parse --show-toplevel", hook["command"])
                    self.assertIn(
                        "git rev-parse --show-toplevel", hook["commandWindows"]
                    )
                    self.assertIn("fastlane_hook.py", hook["command"])
                    self.assertIn("fastlane_hook.py", hook["commandWindows"])

    def test_valid_and_malformed_event_payloads(self) -> None:
        parsed = fastlane_hook.read_event(
            io.StringIO(json.dumps(payload("Stop", self.root, stop_hook_active=True)))
        )
        self.assertEqual(parsed["hook_event_name"], "Stop")
        with self.assertRaises(fastlane_hook.HookInputError):
            fastlane_hook.read_event(io.StringIO("not-json"))
        with self.assertRaises(fastlane_hook.HookInputError):
            fastlane_hook.handle_event(
                "stop",
                payload("PreToolUse", self.root),
                root=self.root,
                doctor_report=report(),
            )

    def test_session_start_adds_short_read_only_state_context(self) -> None:
        result = fastlane_hook.handle_event(
            "session-start",
            payload("SessionStart", self.root),
            root=self.root,
            doctor_report=report(),
        )
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("stage=DEFINE", context)
        self.assertIn("Hooks are defense in depth", context)
        self.assertLessEqual(len(context), fastlane_hook.MAX_CONTEXT_CHARS)
        self.assertNotIn("sha256", context.casefold())

    def test_documentation_only_aws_tools_remain_allowed(self) -> None:
        for tool_name in (
            "mcp__aws-core__retrieve_skill",
            "mcp__aws-core__search_documentation",
        ):
            result = fastlane_hook.handle_event(
                "pre-tool-use",
                payload(
                    "PreToolUse",
                    self.root,
                    tool_name=tool_name,
                    tool_input={"query": "Lambda security guidance"},
                ),
                root=self.root,
                doctor_report=report(),
                envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
            )
            self.assertIsNone(result)

    def test_read_only_gh_api_is_not_misclassified_as_publication(self) -> None:
        read_result = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse",
                self.root,
                tool_name="Bash",
                tool_input={"command": "gh api repos/example/project"},
            ),
            root=self.root,
            doctor_report=report(),
            envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
        )
        self.assertIsNone(read_result)

        write_result = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse",
                self.root,
                tool_name="Bash",
                tool_input={
                    "command": "gh api --method POST repos/example/project/issues"
                },
            ),
            root=self.root,
            doctor_report=report(),
            envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
        )
        self.assertIn(
            "GitHub publication",
            write_result["hookSpecificOutput"]["permissionDecisionReason"],
        )

    def test_unauthorized_aws_and_github_mutations_are_denied(self) -> None:
        cases = (
            (
                "mcp__aws-core__call_aws",
                {"operation_name": "CreateStack"},
                "AWS mutation",
            ),
            ("Bash", {"command": "terraform destroy"}, "AWS mutation"),
            (
                "mcp__github__merge_pull_request",
                {"number": 1},
                "GitHub publication",
            ),
            ("Bash", {"command": "git push origin main"}, "GitHub publication"),
        )
        for tool_name, tool_input, expected in cases:
            with self.subTest(tool_name=tool_name, tool_input=tool_input):
                result = fastlane_hook.handle_event(
                    "pre-tool-use",
                    payload(
                        "PreToolUse",
                        self.root,
                        tool_name=tool_name,
                        tool_input=tool_input,
                    ),
                    root=self.root,
                    doctor_report=report(),
                    envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
                )
                decision = result["hookSpecificOutput"]
                self.assertEqual(decision["permissionDecision"], "deny")
                self.assertIn(expected, decision["permissionDecisionReason"])

    def test_out_of_repository_write_is_denied(self) -> None:
        outside = self.root.parent / "not-fastlane.txt"
        result = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse",
                self.root,
                tool_name="apply_patch",
                tool_input={"path": str(outside), "command": ""},
            ),
            root=self.root,
            doctor_report=report(),
            envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
        )
        self.assertIn(
            "outside the current repository",
            result["hookSpecificOutput"]["permissionDecisionReason"],
        )

    def test_authorized_requests_keep_normal_owner_approval(self) -> None:
        result = fastlane_hook.handle_event(
            "permission-request",
            payload(
                "PermissionRequest",
                self.root,
                tool_name="mcp__github__create_pull_request",
                tool_input={"description": "Open the reviewed pull request"},
            ),
            root=self.root,
            doctor_report=report(construction="AUTH-0001"),
            envelope={
                "AWS boundary": "NONE",
                "GitHub boundary": "BRANCH_AND_PR",
            },
        )
        self.assertIsNone(result)

    def test_permission_request_never_auto_allows(self) -> None:
        result = fastlane_hook.handle_event(
            "permission-request",
            payload(
                "PermissionRequest",
                self.root,
                tool_name="Bash",
                tool_input={
                    "command": "python -m unittest",
                    "description": "disable sandbox for unrestricted access",
                },
            ),
            root=self.root,
            doctor_report=report(construction="AUTH-0001"),
            envelope={"AWS boundary": "NONE", "GitHub boundary": "BRANCH_AND_PR"},
        )
        decision = result["hookSpecificOutput"]["decision"]
        self.assertEqual(decision["behavior"], "deny")
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn('"behavior": "allow"', source)

    def test_post_tool_runs_bounded_validation_without_claiming_evidence(self) -> None:
        calls: list[list[str]] = []

        def fail(root: Path, command: object) -> bool:
            calls.append(list(command))
            return False

        result = fastlane_hook.handle_event(
            "post-tool-use",
            payload(
                "PostToolUse",
                self.root,
                tool_name="apply_patch",
                tool_input={"command": "*** Begin Patch\n*** End Patch"},
                tool_response={"ok": True},
            ),
            root=self.root,
            validation_runner=fail,
        )
        self.assertEqual(calls, [["git", "diff", "--check"]])
        self.assertIn("diff-format problem", result["systemMessage"])
        self.assertNotIn("evidence", result["systemMessage"].casefold())

    def test_stop_continuation_and_loop_prevention(self) -> None:
        event = payload("Stop", self.root, stop_hook_active=False)
        continue_result = fastlane_hook.handle_event(
            "stop",
            event,
            root=self.root,
            doctor_report=report(automatic=True, owner_action=False),
        )
        self.assertEqual(continue_result["decision"], "block")
        for blocked in (
            report(automatic=False, owner_action=False),
            report(automatic=True, owner_action=True),
            report(automatic=True, owner_action=False, formal_receipt=True),
        ):
            self.assertIsNone(
                fastlane_hook.handle_event(
                    "stop", event, root=self.root, doctor_report=blocked
                )
            )
        self.assertIsNone(
            fastlane_hook.handle_event(
                "stop",
                payload("Stop", self.root, stop_hook_active=True),
                root=self.root,
                doctor_report=report(automatic=True, owner_action=False),
            )
        )

    def test_no_transcript_parsing_secret_persistence_or_tool_input_logging(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "transcript_path",
            "last_assistant_message",
            "AWS_ACCESS_KEY",
            "OPENAI_API_KEY",
            "GITHUB_TOKEN",
            "write_text(",
            "open(\"a",
            "logging.",
        ):
            self.assertNotIn(forbidden, source)
        security = (self.root / "SECURITY.md").read_text(encoding="utf-8")
        hooks = (self.root / "docs" / "HOOKS.md").read_text(encoding="utf-8")
        self.assertIn("Hooks are defense in depth", hooks)
        self.assertIn("never auto-allows", security)


if __name__ == "__main__":
    unittest.main()
