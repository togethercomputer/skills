#!/usr/bin/env python3
"""Validate Together AI skill directories.

Usage:
    python scripts/quick_validate.py skills/together-*
    python scripts/quick_validate.py skills/together-chat-completions

Checks:
    - YAML frontmatter exists and parses
    - name is kebab-case, max 64 chars, matches directory name
    - description has no angle brackets, max 1024 chars
    - No disallowed frontmatter keys
    - Referenced files in references/ and scripts/ exist
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}

KEBAB_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from markdown text. Returns (frontmatter, body)."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            fm[key] = value

    return fm, parts[2]


def iter_skill_dirs(path: Path) -> list[Path]:
    """Expand a path into one or more skill directories."""
    if (path / "SKILL.md").exists():
        return [path]

    return sorted(
        child
        for child in path.iterdir()
        if child.is_dir() and (child / "SKILL.md").exists()
    )


def validate_skill(skill_dir: Path) -> list[str]:
    """Validate a single skill directory. Returns list of error messages."""
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        errors.append(f"{skill_dir}: SKILL.md not found")
        return errors

    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if not fm:
        errors.append(f"{skill_dir}: No YAML frontmatter found")
        return errors

    # Check name
    name = fm.get("name", "")
    if not name:
        errors.append(f"{skill_dir}: Missing 'name' in frontmatter")
    else:
        if len(name) > 64:
            errors.append(f"{skill_dir}: name exceeds 64 characters ({len(name)})")
        if not KEBAB_CASE_RE.match(name):
            errors.append(f"{skill_dir}: name '{name}' is not kebab-case")
        if name != skill_dir.name:
            errors.append(
                f"{skill_dir}: name '{name}' does not match directory name '{skill_dir.name}'"
            )

    # Check description
    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{skill_dir}: Missing 'description' in frontmatter")
    else:
        if len(desc) > 1024:
            errors.append(
                f"{skill_dir}: description exceeds 1024 characters ({len(desc)})"
            )
        if "<" in desc or ">" in desc:
            errors.append(f"{skill_dir}: description contains angle brackets")

    # Check for disallowed keys
    for key in fm:
        if key not in ALLOWED_FRONTMATTER_KEYS:
            errors.append(f"{skill_dir}: Disallowed frontmatter key '{key}'")

    # Check referenced files exist
    refs_dir = skill_dir / "references"
    scripts_dir = skill_dir / "scripts"

    if refs_dir.exists() and not any(refs_dir.iterdir()):
        errors.append(f"{skill_dir}: Empty references/ directory")

    if scripts_dir.exists() and not any(scripts_dir.iterdir()):
        errors.append(f"{skill_dir}: Empty scripts/ directory")

    # Check markdown links in body point to existing files
    link_re = re.compile(r"\[.*?\]\(((?:references|scripts)/[^)]+)\)")
    for match in link_re.finditer(body):
        ref_path = skill_dir / match.group(1)
        if not ref_path.exists():
            errors.append(f"{skill_dir}: Referenced file not found: {match.group(1)}")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/quick_validate.py skills/together-*")
        return 1

    all_errors: list[str] = []
    validated = 0

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.is_dir():
            print(f"Skipping {arg} (not a directory)")
            continue
        skill_dirs = iter_skill_dirs(path)
        if not skill_dirs:
            print(f"Skipping {arg} (no SKILL.md found)")
            continue

        for skill_dir in skill_dirs:
            errors = validate_skill(skill_dir)
            validated += 1
            if errors:
                all_errors.extend(errors)
                print(f"FAIL  {skill_dir.name}")
                for e in errors:
                    print(f"      {e}")
            else:
                print(f"OK    {skill_dir.name}")

    print(f"\n{validated} skills validated, {len(all_errors)} errors")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
