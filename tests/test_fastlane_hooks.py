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
    write_authority: dict[str, object] | None = None,
    external_authority: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "gates": {"gate_a": "BLOCKED", "gate_b": "BLOCKED"},
        "authorizations": {"construction": construction, "aws": aws},
        "write_authority": write_authority or {
            "valid": False,
            "approved_write_roots": [],
            "exclusions": [],
            "protected_paths": [],
            "active_task": "NONE",
            "active_task_write_set": [],
        },
        "external_authority": external_authority or {
            "kind": "NONE",
            "validity": "NONE",
            "resources": [],
            "operations": [],
        },
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


def aws_request(operation: str, stack: str = "fastlane-stack") -> dict[str, str]:
    return {
        "operation_name": operation,
        "stack_name": stack,
        "account": "111122223333",
        "region": "us-west-2",
        "environment": "development",
        "role": "fastlane-role",
        "artifact": "sha256:abc",
        "plan": "change-set-1",
    }


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

    def test_write_authority_enforces_roots_exclusions_protection_and_active_task(self) -> None:
        authority = {
            "valid": True,
            "approved_write_roots": ["app/**"],
            "exclusions": ["app/owner-only/**"],
            "protected_paths": ["app/protected.txt"],
            "active_task": "TASK-0001",
            "active_task_write_set": ["app/service/**"],
        }
        allowed = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse",
                self.root,
                tool_name="apply_patch",
                tool_input={"path": "app/service/handler.py", "command": ""},
            ),
            root=self.root,
            doctor_report=report(construction="AUTH-0001", write_authority=authority),
            envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
        )
        self.assertIsNone(allowed)
        for path, reason in (
            ("docs/project/PRD.md", "Gate B write roots"),
            ("app/owner-only/secret.txt", "excluded write path"),
            ("app/protected.txt", "protected dirty path"),
            ("app/other/file.py", "active write set"),
        ):
            with self.subTest(path=path):
                denied = fastlane_hook.handle_event(
                    "pre-tool-use",
                    payload(
                        "PreToolUse",
                        self.root,
                        tool_name="apply_patch",
                        tool_input={"path": path, "command": ""},
                    ),
                    root=self.root,
                    doctor_report=report(construction="AUTH-0001", write_authority=authority),
                    envelope={"AWS boundary": "NONE", "GitHub boundary": "NONE"},
                )
                self.assertIn(reason, denied["hookSpecificOutput"]["permissionDecisionReason"])

    def test_aws_read_fast_dev_explicit_deployment_and_teardown_are_distinct(self) -> None:
        base = {
            "validity": "CURRENT",
            "account": "111122223333",
            "region": "us-west-2",
            "environment": "development",
            "role_or_profile": "fastlane-role",
            "resources": ["fastlane-stack"],
            "artifact_plan_binding": {"artifact": "sha256:abc", "plan": "change-set-1"},
        }
        read = {**base, "kind": "AWS_READ_ONLY", "operations": ["DescribeStacks"]}
        self.assertIsNone(
            fastlane_hook.handle_event(
                "pre-tool-use",
                payload(
                    "PreToolUse", self.root,
                    tool_name="mcp__aws-core__call_aws",
                    tool_input={"operation_name": "DescribeStacks", "region": "us-west-2"},
                ),
                root=self.root,
                doctor_report=report(aws="AUTH-0001", external_authority=read),
                envelope={"AWS boundary": "READ_ONLY", "GitHub boundary": "NONE"},
            )
        )
        fast_dev = {**base, "kind": "FAST_DEV_GATE_B", "operations": ["CreateStack"]}
        self.assertIsNone(
            fastlane_hook.handle_event(
                "permission-request",
                payload(
                    "PermissionRequest", self.root,
                    tool_name="mcp__aws-core__call_aws",
                    tool_input=aws_request("CreateStack"),
                ),
                root=self.root,
                doctor_report=report(aws="AUTH-0001", external_authority=fast_dev),
                envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
            )
        )
        partial_operation = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse", self.root,
                tool_name="mcp__aws-core__call_aws",
                tool_input={**aws_request("CreateStack"), "operation_name": "Create"},
            ),
            root=self.root,
            doctor_report=report(aws="AUTH-0001", external_authority=fast_dev),
            envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
        )
        self.assertIn(
            "exact operation",
            partial_operation["hookSpecificOutput"]["permissionDecisionReason"],
        )
        partial_resource = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse", self.root,
                tool_name="mcp__aws-core__call_aws",
                tool_input=aws_request("CreateStack", "fastlane"),
            ),
            root=self.root,
            doctor_report=report(aws="AUTH-0001", external_authority=fast_dev),
            envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
        )
        self.assertIn(
            "resource target",
            partial_resource["hookSpecificOutput"]["permissionDecisionReason"],
        )
        deployment = {**base, "kind": "AWS_DEPLOYMENT", "operations": ["UpdateStack"]}
        teardown = {**base, "kind": "AWS_TEARDOWN", "operations": ["DeleteStack"]}
        self.assertIsNone(
            fastlane_hook.handle_event(
                "permission-request",
                payload(
                    "PermissionRequest", self.root,
                    tool_name="mcp__aws-core__call_aws",
                    tool_input=aws_request("UpdateStack"),
                ),
                root=self.root,
                doctor_report=report(aws="AWS-AUTH-0001", external_authority=deployment),
                envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
            )
        )
        for missing_field in ("account", "region", "environment", "role", "artifact", "plan"):
            with self.subTest(missing_field=missing_field):
                incomplete = aws_request("UpdateStack")
                incomplete.pop(missing_field)
                denied = fastlane_hook.handle_event(
                    "pre-tool-use",
                    payload(
                        "PreToolUse", self.root,
                        tool_name="mcp__aws-core__call_aws",
                        tool_input=incomplete,
                    ),
                    root=self.root,
                    doctor_report=report(aws="AWS-AUTH-0001", external_authority=deployment),
                    envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
                )
                self.assertIn(
                    "not observable",
                    denied["hookSpecificOutput"]["permissionDecisionReason"],
                )
        denied_teardown = fastlane_hook.handle_event(
            "pre-tool-use",
            payload(
                "PreToolUse", self.root,
                tool_name="mcp__aws-core__call_aws",
                tool_input=aws_request("DeleteStack"),
            ),
            root=self.root,
            doctor_report=report(aws="AWS-AUTH-0001", external_authority=deployment),
            envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
        )
        self.assertIn("distinct current teardown receipt", denied_teardown["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNone(
            fastlane_hook.handle_event(
                "pre-tool-use",
                payload(
                    "PreToolUse", self.root,
                    tool_name="mcp__aws-core__call_aws",
                    tool_input=aws_request("DeleteStack"),
                ),
                root=self.root,
                doctor_report=report(aws="TEARDOWN-AUTH-0001", external_authority=teardown),
                envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
            )
        )

    def test_wrappers_mixed_chains_and_run_script_fail_closed(self) -> None:
        external = {
            "kind": "FAST_DEV_GATE_B",
            "validity": "CURRENT",
            "resources": ["fastlane-stack"],
            "operations": ["CreateStack"],
        }
        for tool_name, tool_input in (
            ("Bash", {"command": "bash -c 'aws cloudformation create-stack --stack-name fastlane-stack; aws cloudformation delete-stack --stack-name fastlane-stack'"}),
            ("mcp__aws-core__run_script", {"script": "print('opaque')"}),
        ):
            denied = fastlane_hook.handle_event(
                "pre-tool-use",
                payload("PreToolUse", self.root, tool_name=tool_name, tool_input=tool_input),
                root=self.root,
                doctor_report=report(aws="AUTH-0001", external_authority=external),
                envelope={"AWS boundary": "MUTATE_LISTED_RESOURCES", "GitHub boundary": "NONE"},
            )
            self.assertIn("ambiguous", denied["hookSpecificOutput"]["permissionDecisionReason"].casefold())
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
