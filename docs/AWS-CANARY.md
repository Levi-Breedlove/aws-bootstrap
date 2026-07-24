# Disposable AWS Canary Validation

This optional field review tests Fastlane against real Codex behavior and a
disposable AWS environment. The offline scorer in
`scripts/aws_canary_eval.py` does not access AWS; framework maintenance and
ordinary CI do not access AWS either. A live run starts
only after the existing Gate A, Gate B, AWS-10, AWS-20, and teardown contracts
are independently satisfied.

Canaries are evidence exercises, not example applications or universal AWS
architectures. Use synthetic data, a non-production account or tightly
isolated environment, an exact resource namespace, a short validity window,
and the smallest practical cost ceiling. Never record credentials or secret
values.

## Representative canaries

### Synchronous managed-serverless application

Exercise one authenticated request through a managed API, stateless compute,
managed persistence, and telemetry. The controlled failure should prove a safe
dependency failure or rejected invalid request, followed by rollback to the
last known-good artifact.

### Asynchronous event-driven workflow

Exercise an accepted event through durable messaging and an idempotent
consumer. Observe retries and a bounded dead-letter or failure path, then
restore the known-good consumer and prove that duplicate delivery remains safe.

### Container-based application

Exercise an immutable image through managed container orchestration, bounded
networking, health checks, and telemetry. Inject one controlled unhealthy
revision, observe failed health or rollback behavior, and restore the last
known-good image digest.

The coordinator must still compare whole-system candidates and select the
actual services from approved requirements and current AWS Core evidence.
These descriptions do not preselect a stack.

## Required observed path

Every canary records evidence for each step in this order:

1. synthetic owner intake;
2. Gate A approval;
3. AWS Core-grounded design and candidate comparison;
4. Gate B approval;
5. local build and IaC validation;
6. AWS-10 read-only preflight;
7. exact AWS-20 deployment authority;
8. deployment and smoke tests;
9. one controlled failure and authorized rollback;
10. AWS-30 deployed evidence;
11. teardown review and exact teardown authority;
12. teardown; and
13. residual-resource and delayed-billing checks.

No step inherits authority from another. Gate B is not deployment authority,
deployment or rollback authority is not teardown authority, and a tool or IAM
permission never replaces an owner receipt.

## Machine-readable evidence bundle

Print the authoritative offline contract:

```text
python scripts/aws_canary_eval.py plan --json
```

Create one untracked bundle root. Each canary run contains a manifest with
SHA-256 bindings for:

- Gate A and Gate B receipts;
- AWS-20 deployment and distinct teardown authority;
- CloudTrail export;
- IaC plan or change set;
- smoke tests, rollback, and teardown results; and
- billing reports.

Every referenced path must stay inside the bundle root, be a regular
non-symlink file, and match its digest. Normalized receipt fields must match the
run's account, Region, environment, role, resources, operations, artifact and
plan, Decimal cost ceiling, rollback boundary, and expiration. Chronology must
show deployment authorization, deployment, controlled failure, rollback,
teardown authorization, teardown, billing observation, and follow-up in order.
Deployment authority never substitutes for teardown authority.

Verify the exported bundle without AWS or credentials:

```text
python scripts/aws_canary_eval.py score --input <results.json> --bundle-root <evidence-bundle> --json
```

`CANARY_EVIDENCE_CONTRACT_PASS` proves exported evidence integrity and internal
consistency only; it does not prove AWS truth. The verifier is
standard-library-only and fails closed on traversal, symlinks, digest mismatch,
duplicate runs, inconsistent identifiers, expired authority, non-canonical
money, chronology errors, secrets, or missing evidence. It performs no network
or subprocess operation.

Raw bundles remain outside the repository. Record only a non-secret summary and
durable reference in `docs/project/VERIFY.md`.
## Illustrative IAM boundaries

These identity-policy fragments are illustrative starting points, not
universal policies. Replace every placeholder, remove inapplicable actions,
separate roles, scope resources as tightly as each service supports, and run
IAM Access Analyzer validation during AWS-10. The conditions restrict the
example permissions to requests through the named AWS-managed MCP path; they
do not grant Fastlane authority.

### Design and read-only discovery role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadNamedCanaryStackThroughAwsMcp",
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:DescribeStacks"
      ],
      "Resource": "<EXACT_CANARY_STACK_ARN>",
      "Condition": {
        "Bool": {"aws:ViaAWSMCPService": "true"},
        "StringEquals": {"aws:CalledViaAWSMCP": "aws-mcp.amazonaws.com"}
      }
    },
    {
      "Sid": "ValidateCandidatePoliciesThroughAwsMcp",
      "Effect": "Allow",
      "Action": "access-analyzer:ValidatePolicy",
      "Resource": "*",
      "Condition": {
        "Bool": {"aws:ViaAWSMCPService": "true"},
        "StringEquals": {"aws:CalledViaAWSMCP": "aws-mcp.amazonaws.com"}
      }
    }
  ]
}
```

The wildcard is limited to an action that does not support resource-level
permissions; do not generalize it to other APIs.

### Deployment role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DeployOnlyReviewedCanaryChangeSetThroughAwsMcp",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet"
      ],
      "Resource": "<EXACT_CANARY_STACK_ARN>",
      "Condition": {
        "Bool": {"aws:ViaAWSMCPService": "true"},
        "StringEquals": {"aws:CalledViaAWSMCP": "aws-mcp.amazonaws.com"}
      }
    },
    {
      "Sid": "ReadOnlyReviewedArtifactThroughAwsMcp",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "<EXACT_ARTIFACT_OBJECT_ARN>",
      "Condition": {
        "Bool": {"aws:ViaAWSMCPService": "true"},
        "StringEquals": {"aws:CalledViaAWSMCP": "aws-mcp.amazonaws.com"}
      }
    }
  ]
}
```

The actual role must also constrain CloudFormation's service role and any
`iam:PassRole` permission to the exact reviewed identities and resources.

### Teardown role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DeleteOnlyAuthorizedCanaryStackThroughAwsMcp",
      "Effect": "Allow",
      "Action": "cloudformation:DeleteStack",
      "Resource": "<EXACT_CANARY_STACK_ARN>",
      "Condition": {
        "Bool": {"aws:ViaAWSMCPService": "true"},
        "StringEquals": {"aws:CalledViaAWSMCP": "aws-mcp.amazonaws.com"}
      }
    }
  ]
}
```

Do not add permission to disable termination protection, empty retained data,
or delete shared resources unless the separate teardown receipt names that
exact action and the reviewed policy is updated accordingly.

Primary references: [AWS global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html)
and [Understanding IAM for Managed AWS MCP Servers](https://aws.amazon.com/blogs/security/understanding-iam-for-managed-aws-mcp-servers/).

## Information and authorization needed for one live canary

Before any live run, the owner must provide the canary ID; exact account alias
or ID; Region; non-production environment; profile or role; resource namespace
and deployed-resource boundary; immutable artifact digest; reviewed plan or
change-set type, identifier, and digest; allowed deployment and rollback
operations; finite ISO-currency cost ceiling; validity window; expected
CloudTrail evidence location; billing follow-up time; and approver.

The current PRD must already contain approved Gate A and Gate B receipts, and
AWS-10 must pass. The owner must then send the exact canonical `AUTHORIZE AWS DEPLOYMENT` block from `docs/project/RUNBOOK.md`. After deployment evidence and
the teardown review, the owner must separately send the exact canonical `AUTHORIZE AWS TEARDOWN` block. Without every named value and both action-
specific receipts at their proper stages, the live canary is not authorized.
