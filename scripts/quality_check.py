#!/usr/bin/env python3
"""Validate non-structural quality expectations for Together AI skills.

Usage:
    python scripts/quality_check.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
TRIGGER_EVALS_DIR = REPO_ROOT / "quality" / "trigger-evals"
LONG_SKILL_LIMIT = 500
LONG_REFERENCE_LIMIT = 100
TOC_RE = re.compile(r"^## (Contents|Table of Contents)$", re.MULTILINE)
GENERIC_SCRIPT_LINK_RE = re.compile(r"\[[^\]]+\]\(scripts/\)")
OPENAI_FIELDS = ("display_name", "short_description", "default_prompt")


def iter_skills() -> list[Path]:
    return sorted(
        skill_dir
        for skill_dir in SKILLS_DIR.iterdir()
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
    )


def validate_openai_yaml(skill_dir: Path) -> list[str]:
    warnings: list[str] = []
    path = skill_dir / "agents" / "openai.yaml"
    if not path.exists():
        return [f"{skill_dir.name}: missing agents/openai.yaml"]

    text = path.read_text(encoding="utf-8")
    for field in OPENAI_FIELDS:
        if f"{field}:" not in text:
            warnings.append(f"{skill_dir.name}: openai.yaml missing {field}")
    if f"${skill_dir.name}" not in text:
        warnings.append(f"{skill_dir.name}: default_prompt should mention ${skill_dir.name}")
    return warnings


def validate_skill_body(skill_dir: Path) -> list[str]:
    warnings: list[str] = []
    body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    lines = body.count("\n") + 1
    if lines > LONG_SKILL_LIMIT:
        warnings.append(f"{skill_dir.name}: SKILL.md is {lines} lines; target is <= {LONG_SKILL_LIMIT}")
    if GENERIC_SCRIPT_LINK_RE.search(body):
        warnings.append(f"{skill_dir.name}: replace generic scripts/ links with script-specific links")
    return warnings


def validate_references(skill_dir: Path) -> list[str]:
    warnings: list[str] = []
    for ref_path in sorted((skill_dir / "references").glob("*.md")):
        line_count = ref_path.read_text(encoding="utf-8").count("\n") + 1
        head = "\n".join(ref_path.read_text(encoding="utf-8").splitlines()[:30])
        if line_count > LONG_REFERENCE_LIMIT and not TOC_RE.search(head):
            warnings.append(
                f"{skill_dir.name}: {ref_path.relative_to(skill_dir)} is {line_count} lines with no TOC"
            )
    return warnings


def validate_scripts(skill_dir: Path) -> list[str]:
    warnings: list[str] = []
    for script_path in sorted((skill_dir / "scripts").glob("*.py")):
        text = script_path.read_text(encoding="utf-8")
        if "tempfile.mktemp" in text:
            warnings.append(f"{skill_dir.name}: {script_path.name} uses tempfile.mktemp")
    return warnings


def validate_trigger_eval(skill_dir: Path) -> list[str]:
    warnings: list[str] = []
    path = TRIGGER_EVALS_DIR / f"{skill_dir.name}.json"
    if not path.exists():
        return [f"{skill_dir.name}: missing trigger eval set at {path.relative_to(REPO_ROOT)}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{skill_dir.name}: invalid JSON in {path.relative_to(REPO_ROOT)}: {exc}"]

    if not isinstance(data, list) or len(data) < 6:
        warnings.append(f"{skill_dir.name}: trigger eval set should contain at least 6 items")
        return warnings

    positives = sum(1 for item in data if item.get("should_trigger") is True)
    negatives = sum(1 for item in data if item.get("should_trigger") is False)
    if positives < 3 or negatives < 3:
        warnings.append(f"{skill_dir.name}: trigger eval set should include at least 3 positive and 3 negative prompts")
    return warnings


def main() -> int:
    warnings: list[str] = []
    for skill_dir in iter_skills():
        warnings.extend(validate_openai_yaml(skill_dir))
        warnings.extend(validate_skill_body(skill_dir))
        warnings.extend(validate_references(skill_dir))
        warnings.extend(validate_scripts(skill_dir))
        warnings.extend(validate_trigger_eval(skill_dir))

    if warnings:
        for warning in warnings:
            print(f"WARN: {warning}")
        print(f"\n{len(warnings)} warnings found")
        return 1

    print("Quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
