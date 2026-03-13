#!/usr/bin/env bash
set -euo pipefail
AGENT="${1:-wilbur}"
LOCKFILE="workspaces/${AGENT}/lockfile.jsonl"
if [[ ! -f "$LOCKFILE" ]]; then echo "No lockfile for $AGENT"; exit 0; fi
jq -r '"\(.task) | \(.status) | branch:\(.branch) | \(.updated_at)"' "$LOCKFILE"
