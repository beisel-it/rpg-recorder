#!/usr/bin/env bash
# scripts/test.sh — One-liner to run the full test suite.
#
# Usage:
#   ./scripts/test.sh                # run all tests with coverage
#   ./scripts/test.sh -k test_config # run a subset

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Provide a stub token if not already set (avoids bot.config KeyError in dev)
export DISCORD_TOKEN="${DISCORD_TOKEN:-dev-dummy-token}"

# Prefer the project venv's pytest when available so all dependencies are found.
PYTEST="${REPO_ROOT}/.venv/bin/pytest"
if [[ ! -x "$PYTEST" ]]; then
  PYTEST="pytest"
fi

exec "$PYTEST" "$@"
