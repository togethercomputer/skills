#!/usr/bin/env python3
"""Generate AGENTS.md and update README.md skills table from SKILL.md frontmatter.

Usage:
    python scripts/generate_agents.py              # Generate artifacts
    python scripts/generate_agents.py --check      # Check if artifacts are up-to-date

Reads YAML frontmatter from all skills/together-*/SKILL.md files,
renders AGENTS.md from scripts/AGENTS_TEMPLATE.md, and updates the
README.md skills table between marker comments.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
TEMPLATE_PATH = REPO_ROOT / "scripts" / "AGENTS_TEMPLATE.md"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
README_PATH = REPO_ROOT / "README.md"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Skill ordering for consistent output
SKILL_ORDER = [
    "together-chat-completions",
    "together-images",
    "together-video",
    "together-audio",
    "together-embeddings",
    "together-fine-tuning",
    "together-batch-inference",
    "together-evaluations",
    "together-code-interpreter",
    "together-dedicated-endpoints",
    "together-dedicated-containers",
    "together-gpu-clusters",
]

README_TABLE_BEGIN = "<!-- BEGIN_SKILLS_TABLE -->"
README_TABLE_END = "<!-- END_SKILLS_TABLE -->"


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse YAML frontmatter from markdown text."""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def collect_skills() -> list[dict[str, str]]:
    """Collect skill metadata from all SKILL.md frontmatter."""
    skills: list[dict[str, str]] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or not skill_dir.name.startswith("together-"):
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if fm.get("name") and fm.get("description"):
            # Collect script names
            scripts_dir = skill_dir / "scripts"
            script_names = []
            if scripts_dir.exists():
                script_names = sorted(
                    f.name for f in scripts_dir.iterdir() if f.suffix == ".py"
                )
            skills.append(
                {
                    "name": fm["name"],
                    "description": fm["description"],
                    "scripts": ", ".join(f"`{s}`" for s in script_names) if script_names else "—",
                }
            )

    # Sort by defined order
    order_map = {name: i for i, name in enumerate(SKILL_ORDER)}
    skills.sort(key=lambda s: order_map.get(s["name"], 999))
    return skills


def render_agents_md(skills: list[dict[str, str]]) -> str:
    """Render AGENTS.md from template and skills data."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Replace skill count
    output = template.replace("{{skill_count}}", str(len(skills)))

    # Replace skills loop
    skills_block_re = re.compile(
        r"\{\{#skills\}\}\n(.*?)\{\{/skills\}\}", re.DOTALL
    )
    match = skills_block_re.search(output)
    if match:
        line_template = match.group(1)
        lines = []
        for skill in skills:
            line = line_template
            line = line.replace("{{name}}", skill["name"])
            line = line.replace("{{description}}", skill["description"])
            lines.append(line)
        output = output[: match.start()] + "".join(lines).rstrip("\n") + "\n" + output[match.end() :]

    return output


def render_readme_table(skills: list[dict[str, str]]) -> str:
    """Render the skills table for README.md."""
    lines = [
        "| Skill | Description | Scripts |",
        "|-------|-------------|---------|",
    ]
    for skill in skills:
        # Truncate description for table (first sentence)
        desc = skill["description"]
        first_sentence = desc.split(". ")[0] + "."
        if len(first_sentence) > 120:
            first_sentence = first_sentence[:117] + "..."
        lines.append(f"| **{skill['name']}** | {first_sentence} | {skill['scripts']} |")
    return "\n".join(lines)


def update_readme(skills: list[dict[str, str]]) -> str:
    """Update the skills table in README.md between markers."""
    readme = README_PATH.read_text(encoding="utf-8")

    if README_TABLE_BEGIN not in readme or README_TABLE_END not in readme:
        print("WARNING: README.md missing skills table markers, skipping update")
        return readme

    before = readme[: readme.index(README_TABLE_BEGIN) + len(README_TABLE_BEGIN)]
    after = readme[readme.index(README_TABLE_END) :]
    table = render_readme_table(skills)

    return before + "\n" + table + "\n" + after


def validate_marketplace(skills: list[dict[str, str]]) -> list[str]:
    """Check that marketplace.json skill names match SKILL.md names."""
    errors: list[str] = []
    if not MARKETPLACE_PATH.exists():
        errors.append("Missing .claude-plugin/marketplace.json")
        return errors

    import json
    data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    marketplace_names = set()
    for plugin in data:
        for s in plugin.get("skills", []):
            marketplace_names.add(s["name"])

    skill_names = {s["name"] for s in skills}
    missing = skill_names - marketplace_names
    extra = marketplace_names - skill_names

    if missing:
        errors.append(f"Skills in SKILL.md but not in marketplace.json: {missing}")
    if extra:
        errors.append(f"Skills in marketplace.json but not in SKILL.md: {extra}")

    return errors


def main() -> int:
    check_mode = "--check" in sys.argv

    skills = collect_skills()
    if not skills:
        print("ERROR: No skills found")
        return 1

    print(f"Found {len(skills)} skills")

    # Generate AGENTS.md
    agents_content = render_agents_md(skills)
    # Update README.md
    readme_content = update_readme(skills)

    # Validate marketplace
    mp_errors = validate_marketplace(skills)
    for e in mp_errors:
        print(f"WARNING: {e}")

    if check_mode:
        errors = 0
        if AGENTS_PATH.exists():
            current = AGENTS_PATH.read_text(encoding="utf-8")
            if current != agents_content:
                print("FAIL: AGENTS.md is out of date. Run: python scripts/generate_agents.py")
                errors += 1
            else:
                print("OK: AGENTS.md is up to date")
        else:
            print("FAIL: AGENTS.md does not exist")
            errors += 1

        if README_PATH.exists():
            current = README_PATH.read_text(encoding="utf-8")
            if current != readme_content:
                print("FAIL: README.md skills table is out of date. Run: python scripts/generate_agents.py")
                errors += 1
            else:
                print("OK: README.md skills table is up to date")
        else:
            print("FAIL: README.md does not exist")
            errors += 1

        return 1 if errors else 0

    # Write files
    AGENTS_PATH.write_text(agents_content, encoding="utf-8")
    print(f"Generated {AGENTS_PATH}")

    README_PATH.write_text(readme_content, encoding="utf-8")
    print(f"Updated {README_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
