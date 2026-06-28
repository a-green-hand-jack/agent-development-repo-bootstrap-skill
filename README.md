# Agent Development Repo Bootstrap Skill

Installable Codex skill for initializing agent-development repositories.

The skill lives at:

```text
skills/agent-development-repo-bootstrap/
```

It provides:

- a deterministic bootstrap script for an agent-development repo
- a local `.agent/` doctrine layer that Codex, Claude Code, and other code agents can read after initialization
- a detailed `lab/`, `deliverables/`, and `memory/` harness for runtime, context, memory, tools, evals, traces, permissions, evidence, and release gates
- a generated `scripts/check-agent-harness.py` validator in the target repo

Install with the skills CLI after publishing this repository:

```bash
npx skills add <owner>/agent-development-repo-bootstrap-skill --skill agent-development-repo-bootstrap
```

Use the skill, then run:

```bash
python3 skills/agent-development-repo-bootstrap/scripts/bootstrap_agent_development_repo.py /path/to/repo --project-name "My Agent" --agent-name "my_agent"
```

Run the regression suite:

```bash
python3 -m unittest tests/test_bootstrap_agent_development_repo.py
```

The suite includes a chaos-drift e2e test: bootstrap a repo, inject root-level prompt/eval/trace drift, an unsafe tool permission, and an untracked local dependency; verify the generated validator fails; repair into the harness structure; then verify the validator passes.

