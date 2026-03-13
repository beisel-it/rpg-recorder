#!/usr/bin/env bash
# Usage: lock_upsert.sh --agent A --task T --stage S --status ST --branch B [--notes N] [--delete]
set -euo pipefail
LOCKFILE="workspaces/${AGENT:-wilbur}/lockfile.jsonl"
AGENT=""; TASK=""; STAGE="unknown"; STATUS="running"; BRANCH=""; NOTES=""; DELETE=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --agent) AGENT="$2"; shift 2 ;;
    --task) TASK="$2"; shift 2 ;;
    --stage) STAGE="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --notes) NOTES="$2"; shift 2 ;;
    --delete) DELETE=true; shift ;;
    *) echo "unknown arg $1" >&2; exit 1 ;;
  esac
done
LOCKFILE="workspaces/${AGENT}/lockfile.jsonl"
mkdir -p "workspaces/${AGENT}"
touch "$LOCKFILE"
if $DELETE; then
  tmp=$(mktemp); jq -c "select(.task != \"$TASK\")" "$LOCKFILE" > "$tmp"; mv "$tmp" "$LOCKFILE"
  echo "lock deleted: $TASK"
  exit 0
fi
tmp=$(mktemp)
jq -c "select(.task != \"$TASK\")" "$LOCKFILE" > "$tmp" 2>/dev/null || true
echo "{\"agent\":\"$AGENT\",\"task\":\"$TASK\",\"stage\":\"$STAGE\",\"status\":\"$STATUS\",\"branch\":\"$BRANCH\",\"notes\":\"$NOTES\",\"updated_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$tmp"
mv "$tmp" "$LOCKFILE"
echo "lock upserted: $TASK ($STATUS)"
