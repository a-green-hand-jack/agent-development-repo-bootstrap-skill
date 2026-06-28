#!/usr/bin/env python3
"""Small self-contained skill folder validator for CI."""

from __future__ import annotations

import sys
from pathlib import Path


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter must be closed with ---") from exc
    if not body.strip():
        raise ValueError("SKILL.md body must not be empty")

    values: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"unsupported frontmatter line: {line}")
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing required file: {skill_md}"]

    try:
        frontmatter = parse_frontmatter(skill_md)
    except ValueError as exc:
        return [str(exc)]

    for key in ["name", "description"]:
        if not frontmatter.get(key):
            errors.append(f"missing required frontmatter field: {key}")
    if frontmatter.get("name") != skill_dir.name:
        errors.append(f"frontmatter name must match folder name: {skill_dir.name}")
    unexpected = sorted(set(frontmatter) - {"name", "description"})
    if unexpected:
        errors.append(f"unexpected frontmatter field(s): {', '.join(unexpected)}")
    if len(frontmatter.get("description", "")) < 40:
        errors.append("description is too short to route the skill reliably")
    if not (skill_dir / "agents" / "openai.yaml").is_file():
        errors.append("missing recommended agents/openai.yaml")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: validate_skill.py <skill-dir>", file=sys.stderr)
        return 2
    skill_dir = Path(argv[0]).resolve()
    errors = validate(skill_dir)
    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    print(f"skill validation passed: {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
