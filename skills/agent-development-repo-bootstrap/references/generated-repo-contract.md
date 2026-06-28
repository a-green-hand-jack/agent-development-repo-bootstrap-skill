# Generated Agent Development Repo Contract

The generated repository separates four responsibilities:

```text
.agent/       Local doctrine: how Codex, Claude Code, and other code agents should develop this Agent.
lab/          Evidence factory: runtime, tools, context, memory, evals, traces, permissions, and capability evidence.
deliverables/ Human-facing promises: docs, demos, integrations, reviews, and release notes.
memory/       Active control panel: current state, phase, change control, bridge state, archive, and GC.
```

## Required Top-Level Files

```text
README.md
AGENTS.md
CLAUDE.md
PROJECT.md
DECISIONS.md
.gitignore
scripts/check-agent-harness.py
```

## Local Doctrine

`.agent/` is the project-local constitution. It must include:

```text
.agent/AGENTS.md
.agent/bootstrap-provenance.yaml
.agent/principles.md
.agent/development-methodology.md
.agent/repo-structure-contract.md
.agent/session-protocol.md
.agent/behavior-contract.md
.agent/action-boundary.md
.agent/context-memory-policy.md
.agent/tool-skill-interface.md
.agent/trace-eval-loop.md
.agent/capability-evidence-chain.md
.agent/human-gates.md
.agent/production-control-plane.md
.agent/anti-patterns.md
.agent/checklists/
.agent/templates/
```

The doctrine encodes these invariants:

```text
Agent is a controlled runtime, not a prompt.
Capability comes from explicit action boundaries, not tool count.
Context is engineered per step, not maximized.
Memory is durable state policy, not chat history.
Eval is trace-native evidence, not final-answer scoring alone.
Release means capability claims backed by evidence and gates.
Production requires observation, pause, approval, rollback, and incident learning.
```

## Lab Contract

`lab/` owns behavior evidence generation:

```text
lab/code/       runtime implementation, configs, scripts, baselines, benchmarks, tests
lab/infra/      providers, targets, permissions, human gates, environments, launch, storage, probes
lab/research/   behavior/capability/safety specs, claims, evidence, regressions, release gates
lab/data/       task sets, traces, labels, golden cases, schemas, manifests, privacy, checksums
lab/experiments/agent experiments and eval campaigns
lab/runs/       runtime logs and temporary outputs, normally gitignored
lab/artifacts/  indexes and evidence bundles for durable outputs
```

## Drift Control

The generated validator should catch obvious mechanical drift:

```text
structure drift      root-level agent/evals/traces/prompts/tools directories
doctrine drift       missing .agent doctrine files
permission drift     tools without risk level or human gate
evidence drift       claims referencing unknown evidence ids
trace drift          trace/release artifacts without indexes
dependency drift     local path dependencies, file:// dependencies, private machine paths
script drift         curl piped to shell or unregistered external scripts
memory drift         missing GC files or stale active-memory markers
```
