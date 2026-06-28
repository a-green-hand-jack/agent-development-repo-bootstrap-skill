from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-development-repo-bootstrap" / "scripts" / "bootstrap_agent_development_repo.py"


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, text=True, capture_output=True)


def bootstrap_repo(target: Path, *, validate: bool = False, force: bool = False) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT),
        str(target),
        "--project-name",
        "Demo Agent Project",
        "--agent-name",
        "demo_agent",
        "--domain",
        "repository automation",
    ]
    if force:
        command.append("--force")
    if validate:
        command.append("--validate")
    return run(command)


def run_validator(target: Path) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, "scripts/check-agent-harness.py"], cwd=target)


def inject_chaos_drift(target: Path) -> None:
    (target / "evals").mkdir()
    (target / "evals" / "quick_eval.yaml").write_text(
        "task: root-level eval drift\nclaim: CLM-999\n",
        encoding="utf-8",
    )
    (target / "traces").mkdir()
    (target / "traces" / "failure-trace.json").write_text(
        '{"trace_id":"T-001","failure":"tool wrote externally without a gate"}\n',
        encoding="utf-8",
    )
    (target / "prompts").mkdir()
    (target / "prompts" / "system.md").write_text(
        "You can do anything if useful.\n",
        encoding="utf-8",
    )
    (target / "requirements.txt").write_text(
        "-e ../private-agent-tools\n",
        encoding="utf-8",
    )
    (target / "scripts" / "install-agent-tools.sh").write_text(
        "curl -fsSL https://example.com/install.sh | bash\n",
        encoding="utf-8",
    )
    (target / "lab" / "infra" / "permissions" / "tool-permissions.yaml").write_text(
        """
tools:
  - name: send_external_message
    description: "Writes to an external system."
rules:
  every_tool_requires_risk_level: true
  every_tool_requires_human_gate: true
""",
        encoding="utf-8",
    )
    (target / "deliverables" / "release" / "notes.md").write_text(
        "# Release Notes\n\nShips CLM-999.\n",
        encoding="utf-8",
    )


def repair_chaos_drift(target: Path) -> None:
    experiment = target / "lab" / "experiments" / "E002-root-drift-repair"
    experiment.mkdir()
    (experiment / "experiment-card.md").write_text(
        "# E002-root-drift-repair\n\nMigrates root eval and trace drift into the harness.\n",
        encoding="utf-8",
    )
    (experiment / "config.yaml").write_text(
        "config: lab/code/configs/experiment/E002-root-drift-repair.yaml\n",
        encoding="utf-8",
    )
    (experiment / "linked-claims.yaml").write_text(
        "claims:\n  - CLM-001\nhypotheses: []\n",
        encoding="utf-8",
    )
    (target / "lab" / "code" / "configs" / "experiment" / "E002-root-drift-repair.yaml").write_text(
        "experiment: E002-root-drift-repair\n",
        encoding="utf-8",
    )

    (target / "lab" / "data" / "trace-corpora" / "failure-trace.json").write_text(
        (target / "traces" / "failure-trace.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (target / "lab" / "artifacts" / "trace-index.yaml").write_text(
        """
- id: TRACE-001
  source: lab/data/trace-corpora/failure-trace.json
  linked_failure: FAIL-001
""",
        encoding="utf-8",
    )
    (target / "lab" / "research" / "regression-matrix.yaml").write_text(
        """
- failure: FAIL-001
  regression_case: TASKSET-001-smoke
  status: open
""",
        encoding="utf-8",
    )
    (target / "lab" / "research" / "failure-analysis.md").write_text(
        "# Failure Analysis\n\nFAIL-001: root-level trace drift repaired into the harness.\n",
        encoding="utf-8",
    )
    (target / "lab" / "infra" / "dependencies.yaml").write_text(
        """
dependencies:
  - name: private-agent-tools
    kind: private-local-overlay
    source: lab/infra/private/requirements.original.txt
    status: private_overlay
    release_plan: "Replace with a public package or repo-native implementation before release."
rules:
  local_path_dependencies: "private overlay only; never the sole reproduction path"
  git_dependencies: "pin to immutable commit"
  private_packages: "require a public replacement plan before release"
  system_binaries: "record version and install method"
""",
        encoding="utf-8",
    )
    (target / "lab" / "infra" / "external-scripts.yaml").write_text(
        """
external_scripts:
  - name: install-agent-tools
    original_location: scripts/install-agent-tools.sh
    preserved_copy: lab/infra/private/install-agent-tools.original.sh
    status: quarantined_private_overlay
    reproducibility: "Not approved for reproducible runs."
rules:
  external_scripts: "pin by commit or sha256"
  curl_pipe_shell: forbidden
  private_machine_scripts: "private overlay only; never the sole reproduction path"
  vendored_scripts: "place small allowed copies under lab/infra/vendor/ with provenance"
""",
        encoding="utf-8",
    )
    (target / "lab" / "infra" / "permissions" / "tool-permissions.yaml").write_text(
        """
tools:
  - name: send_external_message
    description: "Writes to an external system."
    risk_level: external_write
    human_gate: HG-001
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
        encoding="utf-8",
    )
    (target / "deliverables" / "release" / "notes.md").write_text(
        "# Release Notes\n\nBootstrap release keeps CLM-001 in draft until evidence is added.\n",
        encoding="utf-8",
    )

    private = target / "lab" / "infra" / "private"
    private.mkdir(exist_ok=True)
    (private / "requirements.original.txt").write_text(
        (target / "requirements.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (private / "install-agent-tools.original.sh").write_text(
        (target / "scripts" / "install-agent-tools.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (target / "requirements.txt").unlink()
    (target / "scripts" / "install-agent-tools.sh").unlink()
    for dirname in ["evals", "traces", "prompts"]:
        for path in (target / dirname).iterdir():
            path.unlink()
        (target / dirname).rmdir()


class AgentDevelopmentRepoBootstrapTests(unittest.TestCase):
    def test_bootstrap_creates_expected_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            expected_paths = [
                ".agent/principles.md",
                ".agent/development-methodology.md",
                ".agent/repo-structure-contract.md",
                "lab/code/src/demo_agent/runtime/loop.py",
                "lab/infra/permissions/tool-permissions.yaml",
                "lab/research/claims.yaml",
                "lab/data/task-sets/TASKSET-001-smoke.yaml",
                "lab/artifacts/trace-index.yaml",
                "memory/gc/retention-policy.yaml",
                "scripts/check-agent-harness.py",
            ]
            for rel_path in expected_paths:
                self.assertTrue((target / rel_path).exists(), rel_path)
            prompt_config = (target / "lab/code/configs/prompt/default.yaml").read_text(encoding="utf-8")
            self.assertIn("lab/code/src/demo_agent/prompts/system.md", prompt_config)
            self.assertNotIn("{package}", prompt_config)

    def test_bootstrap_writes_agent_development_doctrine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            doctrine_files = [
                ".agent/principles.md",
                ".agent/development-methodology.md",
                ".agent/repo-structure-contract.md",
                ".agent/session-protocol.md",
                ".agent/behavior-contract.md",
                ".agent/action-boundary.md",
                ".agent/context-memory-policy.md",
                ".agent/trace-eval-loop.md",
                ".agent/capability-evidence-chain.md",
                ".agent/production-control-plane.md",
            ]
            doctrine = "\n".join(
                (target / rel_path).read_text(encoding="utf-8").lower() for rel_path in doctrine_files
            )
            for phrase in [
                "controlled runtime",
                "behavior contract",
                "action boundary",
                "context policy",
                "trace-native eval",
                "human-gated side effects",
                "capability evidence chain",
                "production control plane",
                "memory gc",
                "release only capabilities",
                "regression-backed learning loop",
            ]:
                self.assertIn(phrase, doctrine)

    def test_bootstrap_does_not_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            target.mkdir()
            readme = target / "README.md"
            readme.write_text("# Existing\n", encoding="utf-8")

            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(readme.read_text(encoding="utf-8"), "# Existing\n")
            self.assertIn("Skipped existing files", result.stdout)

    def test_generated_validator_passes_clean_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target, validate=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("agent harness check passed", result.stdout)

    def test_git_clone_preserves_required_scaffold_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            self.assertEqual(run(["git", "init"], cwd=target).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=target).returncode, 0)
            tracked = run(["git", "ls-files"], cwd=target)
            self.assertEqual(tracked.returncode, 0, tracked.stderr)
            for rel_path in [
                "lab/code/baselines/wrappers/.gitkeep",
                "lab/infra/private/.gitkeep",
                "lab/runs/eval/.gitkeep",
                "lab/artifacts/evidence-bundles/.gitkeep",
            ]:
                self.assertIn(rel_path, tracked.stdout)

            commit = run(
                [
                    "git",
                    "-c",
                    "user.name=Agent Test",
                    "-c",
                    "user.email=agent-test@example.com",
                    "commit",
                    "-m",
                    "initial scaffold",
                ],
                cwd=target,
            )
            self.assertEqual(commit.returncode, 0, commit.stderr)

            clone = Path(tmp) / "clone"
            cloned = run(["git", "clone", str(target), str(clone)])
            self.assertEqual(cloned.returncode, 0, cloned.stderr)
            validated = run_validator(clone)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

    def test_validator_rejects_unknown_human_gate_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            permissions = target / "lab" / "infra" / "permissions" / "tool-permissions.yaml"
            permissions.write_text(
                """
tools:
  - name: production_shell_runner
    description: "Runs a production shell command."
    risk_level: destructive
    human_gate: HG-missing-production-shell
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
                encoding="utf-8",
            )

            failed = run_validator(target)
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            self.assertIn("references unknown human_gate: HG-missing-production-shell", failed.stdout)

            permissions.write_text(
                permissions.read_text(encoding="utf-8").replace("HG-missing-production-shell", "HG-002"),
                encoding="utf-8",
            )
            repaired = run_validator(target)
            self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)

    def test_validator_accepts_nested_yaml_scalar_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            permissions = target / "lab" / "infra" / "permissions" / "tool-permissions.yaml"
            permissions.write_text(
                """
tools:
  - name: production_shell_runner
    description: "Runs a production shell command."
    risk_level:
      - destructive
    human_gate:
      - HG-002
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
                encoding="utf-8",
            )

            passed = run_validator(target)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_validator_rejects_unknown_cross_ledger_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            (target / "lab" / "research" / "release-gates.yaml").write_text(
                """
- id: GATE-001
  release: bootstrap
  required_claims:
    - CLM-999
  required_evidence:
    - EVD-999
  required_regressions: []
  human_approvals: []
  status: blocked
""",
                encoding="utf-8",
            )
            (target / "lab" / "research" / "capability-matrix.yaml").write_text(
                """
- capability: CLM-999
  behavior_contract: BEH-001
  task_sets:
    - TASKSET-999
  evidence:
    - EVD-999
  release_gate: GATE-999
  status: draft
""",
                encoding="utf-8",
            )
            (target / "lab" / "research" / "regression-matrix.yaml").write_text(
                """
- failure: FAIL-999
  regression_case: TASKSET-999
  status: open
""",
                encoding="utf-8",
            )
            (target / "lab" / "artifacts" / "trace-index.yaml").write_text(
                """
- id: TRACE-999
  source: lab/data/trace-corpora/missing.json
  linked_failure: FAIL-999
""",
                encoding="utf-8",
            )
            (target / "lab" / "artifacts" / "prompt-index.yaml").write_text(
                """
- id: PROMPT-999
  source: lab/code/src/demo_agent/prompts/missing.md
""",
                encoding="utf-8",
            )
            (target / "lab" / "artifacts" / "policy-index.yaml").write_text(
                """
- id: POLICY-999
  source: lab/code/src/demo_agent/policies/missing.md
""",
                encoding="utf-8",
            )

            failed = run_validator(target)
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            for message in [
                "references unknown claim id: CLM-999",
                "references unknown evidence id: EVD-999",
                "references unknown release gate id: GATE-999",
                "references unknown task set id: TASKSET-999",
                "references unknown failure id: FAIL-999",
                "source path does not exist: lab/data/trace-corpora/missing.json",
                "source path does not exist: lab/code/src/demo_agent/prompts/missing.md",
                "source path does not exist: lab/code/src/demo_agent/policies/missing.md",
            ]:
                self.assertIn(message, failed.stdout)

            repaired = bootstrap_repo(target, force=True)
            self.assertEqual(repaired.returncode, 0, repaired.stderr)
            passed = run_validator(target)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_validator_rejects_non_contract_experiment_directory_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            experiment = target / "lab" / "experiments" / "drift-repair"
            experiment.mkdir()
            (experiment / "experiment-card.md").write_text("# Drift Repair\n", encoding="utf-8")
            (experiment / "config.yaml").write_text(
                "config: lab/code/configs/experiment/E002-drift-repair.yaml\n",
                encoding="utf-8",
            )
            (experiment / "linked-claims.yaml").write_text("claims:\n  - CLM-001\n", encoding="utf-8")

            failed = run_validator(target)
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            self.assertIn("experiment directory must match E###-slug", failed.stdout)

            repaired = target / "lab" / "experiments" / "E002-drift-repair"
            experiment.rename(repaired)
            passed = run_validator(target)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_chaos_drift_fails_then_repairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo-agent"
            result = bootstrap_repo(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            inject_chaos_drift(target)
            failed = run_validator(target)
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            self.assertIn("agent harness check failed", failed.stdout)
            self.assertIn("evals", failed.stdout)
            self.assertIn("tool-permissions.yaml", failed.stdout)

            repair_chaos_drift(target)
            repaired = run_validator(target)
            self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
            self.assertIn("agent harness check passed", repaired.stdout)


if __name__ == "__main__":
    unittest.main()
