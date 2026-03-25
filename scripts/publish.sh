#!/usr/bin/env bash
# Orchestrator script to generate all derived artifacts.
#
# Usage:
#   ./scripts/publish.sh           # Generate all artifacts
#   ./scripts/publish.sh --check   # Verify artifacts are up-to-date (for CI)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

CHECK_FLAG=""
if [[ "${1:-}" == "--check" ]]; then
    CHECK_FLAG="--check"
fi

EXIT_CODE=0

echo "==> Generating AGENTS.md and README.md skills table..."
if ! python3 scripts/generate_agents.py $CHECK_FLAG; then
    EXIT_CODE=1
fi

echo ""
echo "==> Generating .cursor-plugin/ manifests..."
if ! python3 scripts/generate_cursor_plugin.py $CHECK_FLAG; then
    EXIT_CODE=1
fi

echo ""
if [[ -z "$CHECK_FLAG" ]]; then
    echo "==> Validating all skills..."
    if ! python3 scripts/quick_validate.py skills/together-*; then
        EXIT_CODE=1
    fi

    echo ""
    echo "==> Running quality checks..."
    if ! python3 scripts/quality_check.py; then
        EXIT_CODE=1
    fi
fi

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    if [[ -n "$CHECK_FLAG" ]]; then
        echo "All artifacts are up to date."
    else
        echo "All artifacts generated successfully."
    fi
else
    if [[ -n "$CHECK_FLAG" ]]; then
        echo "Some artifacts are out of date. Run: ./scripts/publish.sh"
    else
        echo "Some steps failed. See errors above."
    fi
fi

exit $EXIT_CODE
