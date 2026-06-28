#!/usr/bin/env python3
"""Bootstrap an agent-development repository with local .agent doctrine."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DIRS = [
    ".agent/checklists",
    ".agent/templates",
    "lab/code/src/{package}/runtime",
    "lab/code/src/{package}/orchestration",
    "lab/code/src/{package}/tools",
    "lab/code/src/{package}/skills",
    "lab/code/src/{package}/prompts",
    "lab/code/src/{package}/policies",
    "lab/code/src/{package}/context",
    "lab/code/src/{package}/memory",
    "lab/code/src/{package}/planning",
    "lab/code/src/{package}/safety",
    "lab/code/src/{package}/observability",
    "lab/code/src/{package}/evaluation",
    "lab/code/src/{package}/integrations",
    "lab/code/src/{package}/utils",
    "lab/code/configs/model",
    "lab/code/configs/runtime",
    "lab/code/configs/tool",
    "lab/code/configs/prompt",
    "lab/code/configs/policy",
    "lab/code/configs/context",
    "lab/code/configs/memory",
    "lab/code/configs/eval",
    "lab/code/configs/experiment",
    "lab/code/configs/baseline",
    "lab/code/configs/benchmark",
    "lab/code/configs/infra",
    "lab/code/configs/release",
    "lab/code/scripts",
    "lab/code/baselines/wrappers",
    "lab/code/baselines/configs",
    "lab/code/baselines/replays",
    "lab/code/benchmarks/tasks",
    "lab/code/benchmarks/metrics",
    "lab/code/benchmarks/protocols",
    "lab/code/benchmarks/runners",
    "lab/code/benchmarks/judges",
    "lab/code/tests/unit",
    "lab/code/tests/smoke",
    "lab/code/tests/contract",
    "lab/code/tests/regression",
    "lab/code/tests/safety",
    "lab/infra/providers/openai",
    "lab/infra/providers/anthropic",
    "lab/infra/providers/local",
    "lab/infra/targets/local",
    "lab/infra/targets/ci",
    "lab/infra/targets/staging",
    "lab/infra/targets/production",
    "lab/infra/permissions",
    "lab/infra/environments/uv",
    "lab/infra/environments/conda",
    "lab/infra/environments/docker",
    "lab/infra/schedulers/local",
    "lab/infra/schedulers/tmux",
    "lab/infra/schedulers/github-actions",
    "lab/infra/schedulers/slurm",
    "lab/infra/schedulers/runai",
    "lab/infra/launch",
    "lab/infra/paths",
    "lab/infra/storage",
    "lab/infra/probes",
    "lab/infra/private",
    "lab/infra/vendor",
    "lab/infra/reports",
    "lab/research",
    "lab/data/cards",
    "lab/data/task-sets",
    "lab/data/trace-corpora",
    "lab/data/labels",
    "lab/data/golden",
    "lab/data/synthetic",
    "lab/data/manifests",
    "lab/data/schemas",
    "lab/data/privacy",
    "lab/data/checksums",
    "lab/experiments/E001-bootstrap-smoke",
    "lab/runs/eval",
    "lab/runs/replay",
    "lab/runs/live-trial",
    "lab/runs/red-team",
    "lab/runs/incident",
    "lab/artifacts/eval-reports",
    "lab/artifacts/evidence-bundles",
    "lab/artifacts/release-packages",
    "deliverables/docs",
    "deliverables/demos",
    "deliverables/integration",
    "deliverables/reviews",
    "deliverables/release",
    "memory/lab",
    "memory/product",
    "memory/bridge",
    "memory/archive/lab",
    "memory/archive/product",
    "memory/archive/bridge",
    "memory/archive/handoffs",
    "memory/gc",
    "scripts",
]

ALWAYS_KEEP_DIRS = {
    "lab/infra/private",
    "lab/runs/eval",
    "lab/runs/replay",
    "lab/runs/live-trial",
    "lab/runs/red-team",
    "lab/runs/incident",
    "lab/artifacts/evidence-bundles",
    "lab/artifacts/release-packages",
}


@dataclass
class Context:
    root: Path
    project_name: str
    agent_name: str
    package_name: str
    domain: str
    runtime_profile: str
    force: bool
    dry_run: bool


class Writer:
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.created: list[str] = []
        self.skipped: list[str] = []

    def mkdir(self, rel_path: str) -> None:
        rel_path = rel_path.format(package=self.ctx.package_name)
        path = self.ctx.root / rel_path
        if not self.ctx.dry_run:
            path.mkdir(parents=True, exist_ok=True)
        self.created.append(rel_path + "/")

    def write(self, rel_path: str, content: str, *, executable: bool = False) -> None:
        rel_path = rel_path.format(package=self.ctx.package_name)
        path = self.ctx.root / rel_path
        if path.exists() and not self.ctx.force:
            self.skipped.append(rel_path)
            return
        if not self.ctx.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content.rstrip() + "\n", encoding="utf-8")
            if executable:
                path.chmod(0o755)
        self.created.append(rel_path)


def slugify(value: str, *, sep: str = "-") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", sep, value.strip().lower()).strip(sep)
    return slug or "agent-project"


def py_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    if not name:
        return "my_agent"
    if name[0].isdigit():
        name = "agent_" + name
    return name


def files(ctx: Context) -> dict[str, str]:
    project = ctx.project_name
    agent = ctx.agent_name
    package = ctx.package_name
    domain = ctx.domain
    runtime_profile = ctx.runtime_profile
    return {
        ".gitignore": """
.DS_Store
__pycache__/
*.pyc
.venv/
.env
.env.*
*.log

# Private machine overlays and runtime output
lab/infra/private/*
!lab/infra/private/.gitkeep
lab/runs/**
!lab/runs/
!lab/runs/**/
!lab/runs/**/.gitkeep

# Large generated artifacts are indexed, not committed directly.
lab/artifacts/release-packages/*
!lab/artifacts/release-packages/.gitkeep
lab/artifacts/evidence-bundles/*
!lab/artifacts/evidence-bundles/.gitkeep
""",
        "README.md": f"""
# {project}

Agent-development repository for `{agent}`.

## Quick Start

```bash
python3 scripts/check-agent-harness.py
```

## Structure

```text
.agent/       local doctrine for code-agent development
lab/          runtime, infra, evals, traces, evidence, and artifacts
deliverables/ human-facing docs, demos, integration, reviews, and release notes
memory/       active project state, bridge state, archive, and memory GC
```
""",
        "AGENTS.md": """
# Agent Entry

Before working on this repository, read:

```text
.agent/AGENTS.md
.agent/principles.md
.agent/session-protocol.md
memory/current-status.md
```

Then follow the smallest relevant path in `.agent/AGENTS.md`.
""",
        "CLAUDE.md": """
# Claude Code Entry

Read `AGENTS.md` first. This repository keeps its durable agent-development doctrine in `.agent/`.
""",
        "PROJECT.md": f"""
# {project}

## Agent

`{agent}`

## Task Domain

{domain}

## Runtime Profile

{runtime_profile}

## Success Criteria

- Capability claims trace to `lab/research/evidence.yaml`.
- High-risk actions have explicit human gates.
- Failures become regression cases before release.
- Release notes do not exceed evidence.

## Out of Scope

- TBD.
""",
        "DECISIONS.md": """
# Decisions

Record durable decisions here. Do not bury durable decisions only in `memory/`.

## Template

```text
YYYY-MM-DD - DEC-001 - Title
Context:
Decision:
Consequences:
Links:
```
""",
        ".agent/AGENTS.md": """
# Local Agent Development Protocol

This directory is the local doctrine for developing this Agent. It is part of the repository, not a global skill.

## Mandatory Session Start

Read:

```text
.agent/principles.md
.agent/session-protocol.md
memory/current-status.md
lab/research/CAPABILITIES.md
lab/research/claims.yaml
```

For implementation work, also read the relevant contract:

```text
.agent/behavior-contract.md
.agent/action-boundary.md
.agent/context-memory-policy.md
.agent/tool-skill-interface.md
.agent/trace-eval-loop.md
```

## Mandatory Session Closeout

Update the smallest useful set of:

```text
lab/research/evidence.yaml
lab/research/experiment-ledger.yaml
lab/research/regression-matrix.yaml
memory/current-status.md
memory/change-control.yaml
```

Then run:

```bash
python3 scripts/check-agent-harness.py
```
""",
        ".agent/principles.md": """
# Agent Development Principles

- Treat the Agent as a controlled runtime, not a prompt.
- Define behavior before implementation.
- Define action boundaries before adding tools.
- Engineer context per step; do not maximize context blindly.
- Treat memory as durable state policy, not chat history.
- Use trace-native evals; final-answer scoring is not enough.
- Turn failures into regression cases before claiming improvement.
- Gate high-risk side effects with human approval.
- Release only capabilities that have evidence.
- Keep doctrine local to `.agent/` so future code-agent sessions inherit the same spirit.
""",
        ".agent/development-methodology.md": """
# Development Methodology

Use three loops.

## Design Loop

```text
behavior contract -> action boundary -> context policy -> tool/skill interface -> runtime topology
```

## Evidence Loop

```text
trace -> label/review -> eval dataset -> regression -> evidence ledger -> release gate
```

## Production Loop

```text
telemetry -> incident -> failure analysis -> regression -> policy/runtime update -> release
```

Prefer narrow vertical slices: one behavior, one action boundary, one traceable eval path, one release gate.
""",
        ".agent/repo-structure-contract.md": """
# Repo Structure Contract

The repository is organized as:

```text
.agent/       local doctrine
lab/          evidence factory
deliverables/ external promises
memory/       active project control plane
scripts/      deterministic checks and maintenance
```

Core chain:

```text
capability claim
  -> agent experiment
  -> infra target
  -> eval / trace replay / live trial
  -> run logs
  -> artifact index
  -> evidence ledger
  -> release note / docs / product behavior
```
""",
        ".agent/session-protocol.md": """
# Session Protocol

## Start

1. Read `.agent/AGENTS.md`.
2. Read `memory/current-status.md`.
3. Identify the relevant claim, behavior, tool, eval, or release gate.
4. Define the smallest verifiable change.

## During Work

- Keep implementation in `lab/code/`.
- Keep runtime and provider assumptions in `lab/infra/`.
- Keep durable behavior evidence in `lab/research/` and `lab/artifacts/`.
- Keep active state in `memory/`.

## Closeout

1. Update evidence, regression, or blocker ledgers.
2. Update `memory/current-status.md`.
3. Run `python3 scripts/check-agent-harness.py`.
4. Report changed files and remaining risk.
""",
        ".agent/behavior-contract.md": """
# Behavior Contract

Define what the Agent should do, should not do, and how it should behave under uncertainty.

Minimum fields for any new behavior:

```text
behavior id
user-visible promise
non-goals
allowed actions
required context
failure mode
eval task set
human gate if any
release gate
```
""",
        ".agent/action-boundary.md": """
# Action Boundary

Agent capability comes from explicit action boundaries, not from maximizing tool count.

Every tool or side effect must define:

```text
allowed operation
risk level
input/output schema
failure behavior
approval requirement
logging requirement
rollback or repair path
```
""",
        ".agent/context-memory-policy.md": """
# Context And Memory Policy

Context is what the model sees for a step. Memory is durable state.

Rules:

- Keep context minimal and task-specific.
- Record context assembly policy in `lab/code/configs/context/`.
- Record memory read/write rules in `lab/code/configs/memory/`.
- Do not store secrets, credentials, or private user data in memory.
- Move stale active memory through `memory/gc/`.
""",
        ".agent/tool-skill-interface.md": """
# Tool And Skill Interface

Tools and skills are capability interfaces. They require contracts.

Each interface should include:

```text
name
purpose
schema
permission class
side effects
observability fields
error handling
human gate
test coverage
```
""",
        ".agent/trace-eval-loop.md": """
# Trace-Native Eval Loop

Evaluate the Agent by trajectories, not final messages alone.

Minimum loop:

```text
task set -> run/eval -> trace -> label/judge -> evidence -> regression -> release gate
```

Any fixed failure should add or update a regression case.
""",
        ".agent/capability-evidence-chain.md": """
# Capability Evidence Chain

No capability claim is production-ready until it has an evidence chain:

```text
CLM-* claim
  -> task set / trace corpus
  -> run config
  -> trace or eval report
  -> EVD-* evidence
  -> release gate
  -> deliverable
```
""",
        ".agent/human-gates.md": """
# Human Gates

Human approval is required for high-risk side effects:

- sending external messages
- spending money
- deleting or mutating user data
- changing production config
- accessing private data
- publishing releases or claims beyond evidence

Record gates in `lab/infra/permissions/human-gates.yaml`.
""",
        ".agent/production-control-plane.md": """
# Production Control Plane

Production agents require:

- telemetry
- tracing
- pause/kill switch
- approval inbox
- rollback or repair path
- incident capture
- regression learning loop

Do not call a release production-ready unless these controls are addressed or explicitly out of scope.
""",
        ".agent/anti-patterns.md": """
# Anti-Patterns

- Prompt-first: behavior only exists inside a long prompt.
- Tool-maxing: adding tools without action boundaries.
- Final-answer eval: grading only output text, not the trace.
- Memory hoarding: storing everything instead of governing durable state.
- No human gate: high-risk actions run without approval.
- Benchmark worship: public benchmark score replaces project-specific behavior evidence.
- Release drift: docs promise capabilities not backed by evidence.
""",
        ".agent/checklists/design-review.md": """
# Design Review Checklist

- Behavior contract exists.
- Action boundary exists.
- Context and memory policy exists.
- Tool/skill interface contract exists.
- Eval task set exists.
- Human gates are defined for high-risk side effects.
""",
        ".agent/checklists/eval-readiness.md": """
# Eval Readiness Checklist

- Task set is versioned.
- Trace schema is known.
- Labels or judge policy are defined.
- Regression cases include known failures.
- Evidence writeback path is defined.
""",
        ".agent/checklists/release-readiness.md": """
# Release Readiness Checklist

- Release claims map to CLM-* ids.
- CLM-* ids map to EVD-* ids.
- Human gates are satisfied.
- Failure regressions pass.
- Release notes do not exceed evidence.
""",
        ".agent/checklists/incident-closeout.md": """
# Incident Closeout Checklist

- Incident trace preserved or summarized.
- Root cause recorded in failure analysis.
- Regression case added.
- Policy/runtime/tool fix linked.
- Release or rollback decision recorded.
""",
        ".agent/templates/behavior-contract.yaml": """
id: BEH-001
promise: TBD
non_goals: []
allowed_actions: []
required_context: []
failure_modes: []
eval_task_sets: []
human_gates: []
release_gates: []
""",
        ".agent/templates/capability-claim.yaml": """
id: CLM-001
claim: TBD
status: draft
behavior_contract: BEH-001
evidence: []
release_locations: []
risks: []
next_actions: []
""",
        ".agent/templates/eval-card.yaml": """
id: EVAL-001
purpose: TBD
task_set: lab/data/task-sets/TASKSET-001-smoke.yaml
trace_corpus: null
metrics: []
judge_policy: null
human_review: required_for_release
""",
        ".agent/templates/failure-case.yaml": """
id: FAIL-001
source_trace: null
failure_mode: TBD
root_cause: unknown
regression_case: null
status: open
""",
        ".agent/templates/release-gate.yaml": """
id: GATE-001
release: TBD
required_claims: []
required_evidence: []
required_regressions: []
human_approvals: []
status: blocked
""",
        f"lab/code/src/{package}/__init__.py": '"""Agent runtime package."""\n',
        f"lab/code/src/{package}/runtime/loop.py": """
def main() -> None:
    raise SystemExit("Implement the controlled runtime loop.")


if __name__ == "__main__":
    main()
""",
        f"lab/code/src/{package}/tools/registry.py": """
TOOLS = []
""",
        f"lab/code/src/{package}/observability/tracing.py": """
def emit_trace(event: dict) -> None:
    raise NotImplementedError("Implement structured trace emission.")
""",
        "lab/code/configs/defaults.yaml": f"""
project: "{project}"
agent: "{agent}"
runtime_profile: "{runtime_profile}"
paths:
  trace_root: "logical:trace_root"
  run_root: "logical:run_root"
  artifact_root: "logical:artifact_root"
""",
        "lab/code/configs/model/default.yaml": """
routes:
  default:
    provider: TBD
    model: TBD
    fallback: null
budgets:
  max_input_tokens: null
  max_output_tokens: null
""",
        "lab/code/configs/runtime/default.yaml": """
runtime:
  profile: single-agent
  checkpointing: required
  max_steps: 20
  timeout_seconds: 600
""",
        "lab/code/configs/tool/default.yaml": """
tools: []
permission_source: lab/infra/permissions/tool-permissions.yaml
""",
        "lab/code/configs/prompt/default.yaml": f"""
prompts:
  system: lab/code/src/{package}/prompts/system.md
""",
        f"lab/code/src/{package}/prompts/system.md": """
You are an agent runtime under development. Follow the project-local behavior contract, action boundary, context policy, and human gates.
""",
        "lab/code/configs/policy/default.yaml": """
policy:
  human_gates: lab/infra/permissions/human-gates.yaml
  side_effects: lab/infra/permissions/side-effects.yaml
""",
        "lab/code/configs/context/default.yaml": """
context_policy:
  load_behavior_contract: true
  load_action_boundary: true
  load_relevant_memory_only: true
  max_context_items: 12
""",
        "lab/code/configs/memory/default.yaml": """
memory_policy:
  durable_writes_require_reason: true
  private_data: forbidden
  gc_policy: memory/gc/retention-policy.yaml
""",
        "lab/code/configs/eval/smoke.yaml": """
eval: EVAL-001-bootstrap-smoke
task_set: lab/data/task-sets/TASKSET-001-smoke.yaml
trace_output: lab/runs/eval/
""",
        "lab/code/configs/experiment/E001-bootstrap-smoke.yaml": """
experiment: E001-bootstrap-smoke
description: Validate the agent-development harness and one minimal behavior path.
""",
        "lab/code/configs/release/default.yaml": """
release:
  gate_source: lab/research/release-gates.yaml
  package_index: lab/artifacts/release-index.yaml
""",
        "lab/code/scripts/run_agent.py": """
def main() -> None:
    raise SystemExit("Implement agent runner.")


if __name__ == "__main__":
    main()
""",
        "lab/code/scripts/run_eval.py": """
def main() -> None:
    raise SystemExit("Implement eval runner.")


if __name__ == "__main__":
    main()
""",
        "lab/code/scripts/replay_trace.py": """
def main() -> None:
    raise SystemExit("Implement trace replay.")


if __name__ == "__main__":
    main()
""",
        "lab/code/scripts/collect_traces.py": """
def main() -> None:
    raise SystemExit("Implement trace collection.")


if __name__ == "__main__":
    main()
""",
        "lab/code/scripts/compare_runs.py": """
def main() -> None:
    raise SystemExit("Implement run comparison.")


if __name__ == "__main__":
    main()
""",
        "lab/code/scripts/package_release.py": """
def main() -> None:
    raise SystemExit("Implement release packaging.")


if __name__ == "__main__":
    main()
""",
        "lab/code/scripts/submit_job.py": """
def main() -> None:
    raise SystemExit("Implement target-specific submission.")


if __name__ == "__main__":
    main()
""",
        "lab/infra/inventory.yaml": """
targets:
  local:
    role: development_and_smoke_eval
    side_effects: none_by_default
  ci:
    role: deterministic_checks
  staging:
    role: gated_live_trials
  production:
    role: human_gated_release_only
""",
        "lab/infra/providers/openai/README.md": "# OpenAI Provider Contract\n",
        "lab/infra/providers/anthropic/README.md": "# Anthropic Provider Contract\n",
        "lab/infra/providers/local/README.md": "# Local Provider Contract\n",
        "lab/infra/permissions/tool-permissions.yaml": """
tools: []
rules:
  every_tool_requires_risk_level: true
  every_tool_requires_human_gate: true
  risk_levels:
    - read_only
    - local_write
    - external_write
    - money_or_compute
    - destructive
""",
        "lab/infra/permissions/side-effects.yaml": """
side_effects: []
rules:
  external_messages: human_approval_required
  spending_money: human_approval_required
  deleting_data: human_approval_required
  production_mutation: human_approval_required
""",
        "lab/infra/permissions/human-gates.yaml": """
human_gates:
  - id: HG-001
    action_class: external_write
    status: required
  - id: HG-002
    action_class: destructive
    status: required
  - id: HG-003
    action_class: production_mutation
    status: required
""",
        "lab/infra/permissions/secrets-policy.md": """
# Secrets Policy

Do not commit secrets, credentials, tokens, private keys, or private provider configuration.
Use `lab/infra/private/` for local overlays and keep it gitignored.
""",
        "lab/infra/dependencies.yaml": """
dependencies: []
rules:
  local_path_dependencies: "private overlay only; never the sole reproduction path"
  git_dependencies: "pin to immutable commit"
  private_packages: "require a public replacement plan before release"
  system_binaries: "record version and install method"
""",
        "lab/infra/external-scripts.yaml": """
external_scripts: []
rules:
  external_scripts: "pin by commit or sha256"
  curl_pipe_shell: forbidden
  private_machine_scripts: "private overlay only; never the sole reproduction path"
  vendored_scripts: "place small allowed copies under lab/infra/vendor/ with provenance"
""",
        "lab/infra/paths/logical-paths.yaml": """
logical_paths:
  project_root: "{PROJECT_ROOT}"
  trace_root: "{TRACE_ROOT}"
  run_root: "{RUN_ROOT}"
  artifact_root: "{ARTIFACT_ROOT}"
""",
        "lab/infra/paths/path-map.template.yaml": """
target: local
path_map:
  TRACE_ROOT: "/replace/with/trace/root"
  RUN_ROOT: "/replace/with/run/root"
  ARTIFACT_ROOT: "/replace/with/artifact/root"
""",
        "lab/infra/storage/traces.yaml": "traces: []\n",
        "lab/infra/storage/artifacts.yaml": "artifacts: []\n",
        "lab/infra/storage/logs.yaml": "logs: []\n",
        "lab/infra/probes/check_provider.py": """
def main() -> None:
    raise SystemExit("Implement provider smoke probe.")


if __name__ == "__main__":
    main()
""",
        "lab/infra/probes/check_permissions.py": """
def main() -> None:
    raise SystemExit("Implement permission-contract probe.")


if __name__ == "__main__":
    main()
""",
        "lab/infra/private/README.md": """
# Private Infra Overlays

This directory is gitignored. Do not commit private paths, credentials, tokens, or machine-specific provider configs.
""",
        "lab/research/BEHAVIOR.md": """
# Behavior

Define user-visible behavior here. Behavior claims should map to `lab/research/claims.yaml`.
""",
        "lab/research/CAPABILITIES.md": """
# Capabilities

Current capability claims:

- CLM-001: The scaffolded harness can support traceable agent-development work.
""",
        "lab/research/SAFETY.md": """
# Safety

Safety boundaries:

- High-risk side effects require human gates.
- Tool permissions are defined in `lab/infra/permissions/tool-permissions.yaml`.
- Production mutations require explicit approval.
""",
        "lab/research/claims.yaml": """
- id: CLM-001
  claim: "The scaffolded harness can support traceable agent-development work."
  status: draft
  behavior_contract: BEH-001
  evidence: []
  release_locations: []
  risks:
    - placeholder behavior not yet production evidence
  next_actions:
    - ACT-001
""",
        "lab/research/hypotheses.yaml": """
- id: HYP-001
  hypothesis: "A minimal smoke eval can verify the repository harness before real agent behavior work starts."
  status: open
  linked_experiments:
    - E001-bootstrap-smoke
""",
        "lab/research/evidence.yaml": "[]\n",
        "lab/research/experiment-ledger.yaml": """
- experiment: E001-bootstrap-smoke
  claims:
    - CLM-001
  hypotheses:
    - HYP-001
  status: planned
  eval_config: lab/code/configs/eval/smoke.yaml
  result_summary: null
""",
        "lab/research/capability-matrix.yaml": """
- capability: CLM-001
  behavior_contract: BEH-001
  task_sets:
    - TASKSET-001-smoke
  evidence: []
  release_gate: GATE-001
  status: draft
""",
        "lab/research/regression-matrix.yaml": "[]\n",
        "lab/research/comparison-matrix.yaml": "[]\n",
        "lab/research/failure-analysis.md": "# Failure Analysis\n\nRecord failed traces, root causes, and regression links here.\n",
        "lab/research/reviewer-risks.md": "# Reviewer Risks\n\nRecord likely reviewer or user objections here.\n",
        "lab/research/release-gates.yaml": """
- id: GATE-001
  release: bootstrap
  required_claims:
    - CLM-001
  required_evidence: []
  required_regressions: []
  human_approvals: []
  status: blocked
""",
        "lab/data/cards/TASKSET-001-smoke.md": """
# TASKSET-001 Smoke

Purpose: verify the harness and one minimal agent behavior path.
""",
        "lab/data/task-sets/TASKSET-001-smoke.yaml": """
id: TASKSET-001-smoke
tasks: []
expected_trace_schema: lab/data/schemas/trace.schema.json
""",
        "lab/data/schemas/trace.schema.json": """
{
  "type": "object",
  "required": ["trace_id", "task_id", "steps"],
  "properties": {
    "trace_id": {"type": "string"},
    "task_id": {"type": "string"},
    "steps": {"type": "array"}
  }
}
""",
        "lab/data/trace-corpora/README.md": "# Trace Corpora\n",
        "lab/data/labels/README.md": "# Labels\n",
        "lab/data/golden/README.md": "# Golden Cases\n",
        "lab/data/synthetic/README.md": "# Synthetic Tasks\n",
        "lab/data/manifests/README.md": "# Manifests\n",
        "lab/data/privacy/README.md": "# Privacy\n\nRecord PII, redaction, and data-retention policy here.\n",
        "lab/data/checksums/README.md": "# Checksums\n",
        "lab/experiments/E001-bootstrap-smoke/experiment-card.md": """
# E001-bootstrap-smoke

## Purpose

Validate the agent-development harness and first smoke-eval path.

## Linked Objects

- CLM-001
- HYP-001
""",
        "lab/experiments/E001-bootstrap-smoke/config.yaml": """
config: lab/code/configs/experiment/E001-bootstrap-smoke.yaml
eval: lab/code/configs/eval/smoke.yaml
infra_target: local
""",
        "lab/experiments/E001-bootstrap-smoke/linked-claims.yaml": """
claims:
  - CLM-001
hypotheses:
  - HYP-001
""",
        "lab/artifacts/result-index.yaml": "[]\n",
        "lab/artifacts/trace-index.yaml": "[]\n",
        "lab/artifacts/prompt-index.yaml": "[]\n",
        "lab/artifacts/policy-index.yaml": "[]\n",
        "lab/artifacts/tool-schema-index.yaml": "[]\n",
        "lab/artifacts/release-index.yaml": "[]\n",
        "deliverables/docs/README.md": "# Docs\n",
        "deliverables/demos/README.md": "# Demos\n",
        "deliverables/integration/README.md": "# Integration\n",
        "deliverables/reviews/README.md": "# Reviews\n",
        "deliverables/release/README.md": "# Release\n\nRelease notes must map claims to evidence.\n",
        "memory/current-status.md": f"""
# Current Status

Current goal: initialize the agent-development harness for {project}.

Recently completed:
- Repository scaffold created.

Current blocker:
- Replace bootstrap placeholders with project-specific behavior, tools, evals, and gates.

Next smallest action:
- Define the first real behavior contract and smoke task set.

Risks:
- Do not treat bootstrap placeholder claims as production evidence.
""",
        "memory/phase-dashboard.yaml": f"""
active_phase: bootstrap
agent: "{agent}"
domain: "{domain}"
runtime_profile: "{runtime_profile}"
next_gate: first_real_behavior_contract
active_claims:
  - CLM-001
open_actions: 1
high_risks: []
""",
        "memory/change-control.yaml": """
changes: []
required_sync_rules:
  behavior_contract_change:
    - .agent/behavior-contract.md
    - lab/research/claims.yaml
    - lab/research/capability-matrix.yaml
  action_boundary_change:
    - .agent/action-boundary.md
    - lab/infra/permissions/tool-permissions.yaml
    - lab/infra/permissions/human-gates.yaml
  tool_schema_change:
    - lab/code/configs/tool/
    - lab/artifacts/tool-schema-index.yaml
    - lab/code/tests/contract/
  context_policy_change:
    - .agent/context-memory-policy.md
    - lab/code/configs/context/
    - lab/research/experiment-ledger.yaml
  memory_policy_change:
    - .agent/context-memory-policy.md
    - lab/code/configs/memory/
    - memory/gc/retention-policy.yaml
  model_route_change:
    - lab/code/configs/model/
    - lab/research/experiment-ledger.yaml
    - lab/research/comparison-matrix.yaml
  release_claim_change:
    - lab/research/claims.yaml
    - lab/research/evidence.yaml
    - deliverables/release/
""",
        "memory/lab/active-experiments.yaml": """
- experiment: E001-bootstrap-smoke
  status: planned
  next_action: "Replace placeholder smoke eval with a project-specific behavior task."
""",
        "memory/lab/run-queue.yaml": "[]\n",
        "memory/lab/infra-status.yaml": """
active_target: local
validated_targets: []
blocked_targets: []
open_infra_risks: []
last_probe_report: null
""",
        "memory/product/release-plan.yaml": """
releases: []
next_release: null
""",
        "memory/product/user-feedback.md": "# User Feedback\n",
        "memory/product/roadmap.md": "# Roadmap\n",
        "memory/bridge/claim-to-evidence.yaml": """
- claim: CLM-001
  evidence: []
  status: draft
""",
        "memory/bridge/evidence-to-release.yaml": "[]\n",
        "memory/bridge/failure-to-regression.yaml": "[]\n",
        "memory/bridge/handoff-log.md": "# Handoff Log\n\nNo handoffs yet.\n",
        "memory/gc/retention-policy.yaml": """
rules:
  completed_run_queue_items:
    after: 14d
    action: archive_summary
  resolved_blockers:
    after: 7d
    action: compact_to_handoff_log
  stale_active_experiments:
    after: 30d_without_update
    action: require_review
  release_done:
    after: release_complete
    action: keep_pointer_only
""",
        "memory/gc/compaction-log.md": "# Memory Compaction Log\n\nNo compactions yet.\n",
        "memory/gc/tombstones.yaml": "[]\n",
        "scripts/check-agent-harness.py": validator_script(),
    }


def validator_script() -> str:
    return r'''
#!/usr/bin/env python3
"""Deterministic structural checks for an agent-development harness."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_DIRS = [
    ".agent/checklists",
    ".agent/templates",
    "lab/code/src",
    "lab/code/configs",
    "lab/code/scripts",
    "lab/code/benchmarks",
    "lab/code/tests",
    "lab/infra/providers",
    "lab/infra/targets",
    "lab/infra/permissions",
    "lab/infra/environments",
    "lab/infra/launch",
    "lab/infra/paths",
    "lab/infra/storage",
    "lab/infra/probes",
    "lab/infra/private",
    "lab/infra/vendor",
    "lab/research",
    "lab/data/task-sets",
    "lab/data/trace-corpora",
    "lab/data/labels",
    "lab/data/golden",
    "lab/data/schemas",
    "lab/data/privacy",
    "lab/experiments",
    "lab/runs",
    "lab/artifacts",
    "deliverables/docs",
    "deliverables/demos",
    "deliverables/integration",
    "deliverables/reviews",
    "deliverables/release",
    "memory/lab",
    "memory/product",
    "memory/bridge",
    "memory/archive",
    "memory/gc",
]

FORBIDDEN_ROOT_DIRS = [
    "agent",
    "agents",
    "evals",
    "traces",
    "prompts",
    "tools",
    "runs",
    "artifacts",
    "infra",
    "research",
    "data",
    "experiments",
]

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "PROJECT.md",
    "DECISIONS.md",
    ".agent/AGENTS.md",
    ".agent/principles.md",
    ".agent/development-methodology.md",
    ".agent/repo-structure-contract.md",
    ".agent/session-protocol.md",
    ".agent/behavior-contract.md",
    ".agent/action-boundary.md",
    ".agent/context-memory-policy.md",
    ".agent/tool-skill-interface.md",
    ".agent/trace-eval-loop.md",
    ".agent/capability-evidence-chain.md",
    ".agent/human-gates.md",
    ".agent/production-control-plane.md",
    ".agent/anti-patterns.md",
    "lab/infra/permissions/tool-permissions.yaml",
    "lab/infra/permissions/side-effects.yaml",
    "lab/infra/permissions/human-gates.yaml",
    "lab/infra/dependencies.yaml",
    "lab/infra/external-scripts.yaml",
    "lab/research/BEHAVIOR.md",
    "lab/research/CAPABILITIES.md",
    "lab/research/SAFETY.md",
    "lab/research/claims.yaml",
    "lab/research/evidence.yaml",
    "lab/research/experiment-ledger.yaml",
    "lab/research/capability-matrix.yaml",
    "lab/research/regression-matrix.yaml",
    "lab/research/failure-analysis.md",
    "lab/research/release-gates.yaml",
    "lab/artifacts/result-index.yaml",
    "lab/artifacts/trace-index.yaml",
    "lab/artifacts/prompt-index.yaml",
    "lab/artifacts/policy-index.yaml",
    "lab/artifacts/tool-schema-index.yaml",
    "lab/artifacts/release-index.yaml",
    "memory/current-status.md",
    "memory/phase-dashboard.yaml",
    "memory/change-control.yaml",
    "memory/gc/retention-policy.yaml",
    "memory/gc/compaction-log.md",
    "memory/gc/tombstones.yaml",
]

EXPERIMENT_REQUIRED_FILES = [
    "experiment-card.md",
    "config.yaml",
    "linked-claims.yaml",
]

EXPERIMENT_DIR_PATTERN = re.compile(r"^E[0-9]{3}-[A-Za-z0-9][A-Za-z0-9_.-]*$")
ID_PATTERN = re.compile(r"\b(?:BEH|CLM|HYP|EVD|ACT|RSK|FAIL|TASKSET|EVAL|GATE|HG)-[A-Za-z0-9_.-]+\b")
CURL_PIPE_SHELL_PATTERN = re.compile(r"\bcurl\b[^\n|]*\|[^\n]*(?:sh|bash)\b")
PRIVATE_ABS_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:/Users/|/home/|/mnt/)")
LOCAL_DEP_PATTERN = re.compile(r"(?m)(?:^|\s)(?:-e\s+)?(?:\.\./|file://)")
TEXT_SUFFIXES = {".bash", ".cfg", ".ini", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml", ".zsh"}
SKIP_SCAN_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "lab/infra/private",
    "lab/runs",
    "memory/archive",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def fail(findings: list[str], code: str, path: str, message: str) -> None:
    findings.append(f"[FAIL] {code} {path}: {message}")


def warn(findings: list[str], code: str, path: str, message: str) -> None:
    findings.append(f"[WARN] {code} {path}: {message}")


def collect_ids(root: Path, rel_path: str, prefix: str) -> set[str]:
    return {match for match in ID_PATTERN.findall(read(root / rel_path)) if match.startswith(prefix + "-")}


def clean_yaml_scalar(value: str) -> str | None:
    value = value.split("#", 1)[0].strip().strip("\"'")
    if not value or value.lower() in {"null", "none", "[]"}:
        return None
    return value


def split_yaml_scalar_values(value: str) -> set[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        values: set[str] = set()
        for item in value[1:-1].split(","):
            cleaned = clean_yaml_scalar(item)
            if cleaned:
                values.add(cleaned)
        return values
    cleaned = clean_yaml_scalar(value)
    return {cleaned} if cleaned else set()


def line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def collect_yaml_scalar_values(content: str, key: str) -> set[str]:
    """Collect simple YAML scalar values for a key without external dependencies.

    Supports `key: value`, `- key: value`, `key: [a, b]`, and an indented
    scalar list below `key:`. It intentionally ignores nested mapping values.
    """
    pattern = re.compile(rf"^(?P<indent>\s*)(?:-\s*)?{re.escape(key)}:\s*(?P<value>[^#\n]*)")
    values: set[str] = set()
    lines = content.splitlines()
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        values.update(split_yaml_scalar_values(match.group("value")))
        base_indent = line_indent(match.group("indent"))
        for child in lines[index + 1:]:
            stripped = child.strip()
            if not stripped or stripped.startswith("#"):
                continue
            child_indent = line_indent(child)
            if child_indent <= base_indent:
                break
            item_match = re.match(r"^\s*-\s*(?P<value>[^#\n]+?)\s*(?:#.*)?$", child)
            if item_match:
                item_value = item_match.group("value").strip()
                if ":" not in item_value:
                    values.update(split_yaml_scalar_values(item_value))
    return values


def iter_named_yaml_blocks(content: str) -> list[tuple[str, str]]:
    lines = content.splitlines()
    blocks: list[tuple[str, str]] = []
    pattern = re.compile(r"^(?P<indent>\s*)-\s*name:\s*(?P<name>[^#\n]+?)\s*(?:#.*)?$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        block_indent = line_indent(match.group("indent"))
        end = index + 1
        while end < len(lines):
            stripped = lines[end].strip()
            if stripped and line_indent(lines[end]) <= block_indent:
                break
            end += 1
        name = clean_yaml_scalar(match.group("name")) or match.group("name").strip()
        blocks.append((name, "\n".join(lines[index:end]) + "\n"))
    return blocks


def is_skipped_scan_path(root: Path, path: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if rel == "scripts/check-agent-harness.py":
        return True
    return any(rel == skip or rel.startswith(skip + "/") for skip in SKIP_SCAN_DIRS)


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or is_skipped_scan_path(root, path):
            continue
        if path.name in {"requirements.txt", "uv.lock"} or path.suffix in TEXT_SUFFIXES:
            files.append(path)
    return files


def main() -> int:
    root = Path.cwd()
    findings: list[str] = []

    for rel_path in REQUIRED_DIRS:
        if not (root / rel_path).is_dir():
            fail(findings, "S1", rel_path, "required directory is missing")
    for rel_path in FORBIDDEN_ROOT_DIRS:
        if (root / rel_path).exists():
            fail(findings, "S1", rel_path, "agent-owned directory appears at repository root")
    for rel_path in REQUIRED_FILES:
        if not (root / rel_path).is_file():
            fail(findings, "S1", rel_path, "required file is missing")

    gitignore = read(root / ".gitignore")
    for pattern in ["lab/infra/private/", "lab/runs/", "*.log"]:
        if pattern not in gitignore:
            warn(findings, "S1", ".gitignore", f"recommended ignore pattern missing: {pattern}")

    principles = read(root / ".agent/principles.md").lower()
    for token in ["controlled runtime", "action boundaries", "trace-native", "human approval"]:
        if token not in principles:
            warn(findings, "D1", ".agent/principles.md", f"local doctrine may be missing principle: {token}")

    claim_ids = collect_ids(root, "lab/research/claims.yaml", "CLM")
    evidence_ids = collect_ids(root, "lab/research/evidence.yaml", "EVD")
    gate_ids = collect_ids(root, "lab/research/release-gates.yaml", "GATE")

    if not claim_ids:
        fail(findings, "S3", "lab/research/claims.yaml", "no CLM-* capability claim ids found")
    if not gate_ids:
        fail(findings, "S3", "lab/research/release-gates.yaml", "no GATE-* release gate ids found")

    for evidence_id in sorted(collect_ids(root, "lab/research/claims.yaml", "EVD") - evidence_ids):
        fail(findings, "S3", "lab/research/claims.yaml", f"references unknown evidence id: {evidence_id}")
    for evidence_id in sorted(collect_ids(root, "lab/artifacts/result-index.yaml", "EVD") - evidence_ids):
        fail(findings, "S3", "lab/artifacts/result-index.yaml", f"references unknown evidence id: {evidence_id}")

    expected_control_tokens = {
        "lab/infra/permissions/tool-permissions.yaml": "risk_levels:",
        "lab/infra/permissions/human-gates.yaml": "human_gates:",
        "lab/infra/dependencies.yaml": "dependencies:",
        "lab/infra/external-scripts.yaml": "external_scripts:",
        "memory/change-control.yaml": "changes:",
    }
    for rel_path, token in expected_control_tokens.items():
        content = read(root / rel_path)
        if content and token not in content:
            fail(findings, "S2", rel_path, f"expected control token missing: {token}")

    tool_permissions = read(root / "lab/infra/permissions/tool-permissions.yaml")
    human_gate_ids = collect_yaml_scalar_values(read(root / "lab/infra/permissions/human-gates.yaml"), "id")
    for tool_name, tool_block in iter_named_yaml_blocks(tool_permissions):
        if not collect_yaml_scalar_values(tool_block, "risk_level"):
            fail(findings, "S2", "lab/infra/permissions/tool-permissions.yaml", f"registered tool {tool_name!r} requires risk_level")
        gate_refs = collect_yaml_scalar_values(tool_block, "human_gate")
        if not gate_refs:
            fail(findings, "S2", "lab/infra/permissions/tool-permissions.yaml", f"registered tool {tool_name!r} requires human_gate")
        for gate_ref in sorted(gate_refs):
            if gate_ref not in human_gate_ids:
                fail(findings, "S2", "lab/infra/permissions/tool-permissions.yaml", f"registered tool {tool_name!r} references unknown human_gate: {gate_ref}")

    experiments_root = root / "lab" / "experiments"
    if experiments_root.exists():
        for experiment_dir in sorted(path for path in experiments_root.iterdir() if path.is_dir()):
            experiment_rel_path = experiment_dir.relative_to(root).as_posix()
            if not EXPERIMENT_DIR_PATTERN.fullmatch(experiment_dir.name):
                fail(findings, "S4", experiment_rel_path, "experiment directory must match E###-slug")
            for filename in EXPERIMENT_REQUIRED_FILES:
                if not (experiment_dir / filename).is_file():
                    fail(findings, "S4", str(experiment_dir.relative_to(root) / filename), "experiment contract file is missing")
            linked = read(experiment_dir / "linked-claims.yaml")
            if linked and not any(token.startswith(("CLM-", "HYP-")) for token in ID_PATTERN.findall(linked)):
                fail(findings, "S4", str((experiment_dir / "linked-claims.yaml").relative_to(root)), "no CLM-* or HYP-* link found")

    status = read(root / "memory/current-status.md").lower()
    if not any(token in status for token in ["next", "blocker", "risk", "blocked"]):
        warn(findings, "S9", "memory/current-status.md", "does not mention next step, blocker, or risk")

    change_control = read(root / "memory/change-control.yaml")
    if re.search(r"(?im)^\s*status:\s*(open|pending|todo|incomplete)\b", change_control):
        warn(findings, "S9", "memory/change-control.yaml", "contains open synchronization work")

    for path in iter_text_files(root):
        rel_path = path.relative_to(root).as_posix()
        content = read(path)
        if CURL_PIPE_SHELL_PATTERN.search(content):
            fail(findings, "S5", rel_path, "curl piped to shell is not reproducible")
        if PRIVATE_ABS_PATH_PATTERN.search(content):
            fail(findings, "S5", rel_path, "private absolute machine path detected")
        if LOCAL_DEP_PATTERN.search(content):
            fail(findings, "S5", rel_path, "local path or file:// dependency detected")

    release_notes = root / "deliverables" / "release"
    if release_notes.exists():
        for path in release_notes.rglob("*.md"):
            content = read(path)
            for claim_id in sorted(set(ID_PATTERN.findall(content))):
                if claim_id.startswith("CLM-") and claim_id not in claim_ids:
                    fail(findings, "S3", path.relative_to(root).as_posix(), f"release references unknown claim id: {claim_id}")

    for item in findings:
        print(item)
    failures = [item for item in findings if item.startswith("[FAIL]")]
    warnings = [item for item in findings if item.startswith("[WARN]")]
    print()
    if failures:
        print(f"agent harness check failed: {len(failures)} failure(s), {len(warnings)} warning(s)")
        return 1
    print(f"agent harness check passed: 0 failure(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''.strip()


def bootstrap(ctx: Context) -> Writer:
    writer = Writer(ctx)
    for rel_path in DIRS:
        writer.mkdir(rel_path)
    for rel_path, content in files(ctx).items():
        writer.write(rel_path, content, executable=rel_path == "scripts/check-agent-harness.py")
    for rel_path in DIRS:
        formatted = rel_path.format(package=ctx.package_name)
        path = ctx.root / formatted
        needs_marker = formatted in ALWAYS_KEEP_DIRS
        if not ctx.dry_run and path.exists():
            needs_marker = needs_marker or not any(child.is_file() for child in path.iterdir())
        if needs_marker:
            writer.write(f"{rel_path}/.gitkeep", "")
    return writer


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap an agent-development repository.")
    parser.add_argument("root", nargs="?", default=".", help="target repository root")
    parser.add_argument("--project-name", default=None, help="human-readable project name")
    parser.add_argument("--agent-name", default=None, help="agent/runtime package name")
    parser.add_argument("--domain", default="workflow automation", help="agent task domain")
    parser.add_argument(
        "--runtime-profile",
        default="single-agent",
        choices=["single-agent", "multi-agent", "deep-agent", "ambient-agent", "managed-agent"],
        help="agent runtime topology label",
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing scaffold files")
    parser.add_argument("--dry-run", action="store_true", help="print planned writes without changing files")
    parser.add_argument("--validate", action="store_true", help="run generated validator after scaffolding")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    project_name = args.project_name or root.name.replace("-", " ").replace("_", " ").title()
    agent_name = args.agent_name or slugify(project_name, sep="-")
    package_name = py_name(agent_name)
    ctx = Context(
        root=root,
        project_name=project_name,
        agent_name=agent_name,
        package_name=package_name,
        domain=args.domain,
        runtime_profile=args.runtime_profile,
        force=args.force,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        root.mkdir(parents=True, exist_ok=True)

    writer = bootstrap(ctx)
    print(f"Target: {root}")
    print(f"Created/planned: {len(writer.created)}")
    if writer.skipped:
        print(f"Skipped existing files: {len(writer.skipped)}")
        for item in writer.skipped[:20]:
            print(f"  skipped {item}")
        if len(writer.skipped) > 20:
            print("  ...")

    if args.validate and not args.dry_run:
        result = subprocess.run([sys.executable, "scripts/check-agent-harness.py"], cwd=root, check=False)
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
