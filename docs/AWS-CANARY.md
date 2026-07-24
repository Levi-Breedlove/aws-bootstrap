# Disposable AWS Canary Validation

This optional field review tests Fastlane against real Codex behavior and a
disposable AWS environment. Framework maintenance, ordinary CI, and the
scorer in `scripts/aws_canary_eval.py` do not access AWS. A live run starts
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

## Machine-readable result

Print the authoritative schema and required step identifiers:

```text
python scripts/aws_canary_eval.py plan --json
```

The untracked result contains exactly one observed run for each canary. Each
run records:

- exact account alias or 12-digit ID, Region, environment, and profile or role;
- immutable artifact digest and plan or change-set type, identifier, and digest;
- deployed resource boundary and Gate A, Gate B, deployment, and teardown
  receipt references;
- finite currency-qualified ceiling, observed cost, and validity period;
- official AWS Core identity, both capability results, returned skill,
  documentation query, official references, and observation time;
- CloudTrail evidence reference;
- controlled failure, rollback, teardown, residual-resource, and billing
  results; and
- one evidence reference for every required step.

Raw result files remain outside the repository unless an approved durable
evidence location is named. Record only the non-secret summary and durable
reference in `docs/project/VERIFY.md`. Score all three observed runs with:

```text
python scripts/aws_canary_eval.py score --input <results.json> --json
```

The scorer is standard-library-only, performs no network or subprocess
operation, and does not access AWS. It fails closed on missing canaries or
fabricated-live
flags, unknown fields, wrong AWS Core provenance, malformed bindings,
non-finite or over-ceiling cost, missing CloudTrail evidence, failed rollback
or teardown, unauthorized residual resources, or any indication that
credentials or secret values were inspected or recorded.

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
