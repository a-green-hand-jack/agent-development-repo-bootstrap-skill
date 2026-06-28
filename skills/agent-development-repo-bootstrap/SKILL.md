---
name: agent-development-repo-bootstrap
description: Bootstrap an agent-development repository with a detailed lab/deliverables/memory structure, local .agent doctrine for ongoing Codex or Claude Code development, capability evidence chains, trace-native eval scaffolds, tool permission ledgers, context and memory policy files, human gates, production control-plane templates, drift-control ledgers, and a deterministic harness validator. Use when creating or converting a coding agent, research agent, workflow agent, tool-using assistant, multi-agent harness, or production agent repo.
---

# Agent Development Repo Bootstrap

Use this skill to initialize an agent-development repo. The global skill is intentionally thin: it creates the project scaffold and writes the enduring development philosophy into the target repo's `.agent/` directory so future Codex, Claude Code, or other code-agent sessions can read local guidance from the project itself.

## Workflow

1. Confirm the target path and whether it is a new repo or an existing repo.
2. Collect only the necessary labels: project name, agent name, task domain, and runtime profile.
3. Run the deterministic bootstrap script:

   ```bash
   python3 skills/agent-development-repo-bootstrap/scripts/bootstrap_agent_development_repo.py /path/to/repo \
     --project-name "My Agent Project" \
     --agent-name "my_agent" \
     --domain "workflow automation" \
     --runtime-profile single-agent
   ```

4. Run the generated validator in the target repo:

   ```bash
   python3 scripts/check-agent-harness.py
   ```

5. Report created files, skipped existing files, validator result, and next actions.

## Rules

- Do not hand-write the scaffold when the script can generate it.
- Do not overwrite existing files unless the user explicitly asks for `--force`.
- Keep long-lived agent development doctrine inside `.agent/`, not in the global skill.
- Keep durable behavior facts in `lab/research/`, `lab/artifacts/`, `lab/experiments/`, `deliverables/`, or `DECISIONS.md`.
- Treat `memory/` as active project state. It must include `memory/gc/retention-policy.yaml`, `compaction-log.md`, and `tombstones.yaml`.
- Keep private machine overlays under `lab/infra/private/` and gitignored.
- Track local/private/git/system dependencies in `lab/infra/dependencies.yaml`.
- Track external scripts and non-repo commands in `lab/infra/external-scripts.yaml`.
- Track behavior, capability, tool, model, context, memory, target, and release changes in `memory/change-control.yaml`.
- Use `.agent/session-protocol.md` as the ongoing session contract after the repo is initialized.

## Resources

- `scripts/bootstrap_agent_development_repo.py` creates the repo structure, `.agent/` doctrine, starter ledgers, and validator.
- `references/generated-repo-contract.md` summarizes the generated structure, local doctrine, and drift-control contract.

