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
import pathlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
TEMPLATE_PATH = REPO_ROOT / "scripts" / "AGENTS_TEMPLATE.md"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
README_PATH = REPO_ROOT / "README.md"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Skill ordering for consistent output
SKILL_ORDER = [
    "together-ai",
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
                    str(f.relative_to(scripts_dir))
                    for f in scripts_dir.rglob("*.py")
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


def collect_domains() -> list[dict[str, str]]:
    """Collect the level-3 domain guides that the skill router dispatches to."""
    domains: list[dict[str, str]] = []
    domains_dir = SKILLS_DIR / "together-ai" / "domains"
    if not domains_dir.exists():
        return domains
    for guide in sorted(domains_dir.glob("*.md")):
        text = guide.read_text(encoding="utf-8")
        title, summary, para = guide.stem, "", []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].replace("Together AI: ", "").strip()
            elif title == guide.stem or line.startswith("#"):
                continue
            elif line:
                # accumulate the wrapped lead paragraph, not just its first line
                para.append(line)
            elif para:
                break
        if para:
            summary = " ".join(para).rstrip(":")
            # keep the table cell to the first sentence
            first = summary.split(". ")[0]
            summary = first if first.endswith(".") else first + "."
        domains.append({"file": guide.name, "title": title, "summary": summary})
    return domains


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

    domains = collect_domains()
    output = output.replace("{{domain_count}}", str(len(domains)))
    domains_block_re = re.compile(r"\{\{#domains\}\}\n(.*?)\{\{/domains\}\}", re.DOTALL)
    match = domains_block_re.search(output)
    if match:
        line_template = match.group(1)
        lines = []
        for domain in domains:
            line = line_template
            line = line.replace("{{file}}", domain["file"])
            line = line.replace("{{title}}", domain["title"])
            line = line.replace("{{summary}}", domain["summary"])
            lines.append(line)
        output = output[: match.start()] + "".join(lines).rstrip("\n") + "\n" + output[match.end() :]

    return output


def render_readme_table(skills: list[dict[str, str]]) -> str:
    """Render the domain table for README.md.

    The repo is one skill, so a one-row skills table carries no information -- the useful
    breakdown for a reader is the domain guides the router dispatches to, and which runnable
    scripts back each one.
    """
    skill_dir = SKILLS_DIR / "together-ai"
    lines = [
        "| Domain guide | What it covers | Scripts |",
        "|--------------|----------------|---------|",
    ]
    for domain in collect_domains():
        area = pathlib.Path(domain["file"]).stem
        summary = domain["summary"]
        if len(summary) > 120:
            summary = summary[:117] + "..."
        area_scripts = sorted(
            f.name for f in (skill_dir / "scripts" / area).glob("*") if f.is_file()
        ) if (skill_dir / "scripts" / area).exists() else []
        scripts = ", ".join(f"`{s}`" for s in area_scripts) if area_scripts else "—"
        lines.append(f"| **{domain['file']}** | {summary} | {scripts} |")
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
    """Validate the .claude-plugin/marketplace.json structure.

    Skills are auto-discovered from skills/*/SKILL.md and are not enumerated
    in marketplace.json, so we only validate the top-level schema shape here:
    a root object with `name`, `owner`, and a non-empty `plugins` array.
    """
    errors: list[str] = []
    if not MARKETPLACE_PATH.exists():
        errors.append("Missing .claude-plugin/marketplace.json")
        return errors

    import json
    try:
        data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"marketplace.json is not valid JSON: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append("marketplace.json root must be an object, not a list")
        return errors

    for key in ("name", "owner", "plugins"):
        if key not in data:
            errors.append(f"marketplace.json missing required key: {key}")

    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append("marketplace.json `plugins` must be a non-empty array")

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
