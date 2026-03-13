#!/usr/bin/env bash
# scripts/deploy.sh — Deploy or update the RPG Recorder bot on the host.
#
# Usage:
#   ./scripts/deploy.sh            # pull, install deps, restart service
#
# Prerequisites:
#   - Repo checked out at ~/rpg-recorder
#   - Virtualenv at ~/rpg-recorder/venv
#   - systemd user service installed (see deploy/rpg-recorder.service)

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/rpg-recorder}"
VENV_PYTHON="${VENV_PYTHON:-$REPO_DIR/venv/bin/python}"
SERVICE_NAME="rpg-recorder"

echo "==> Deploying RPG Recorder from $REPO_DIR"

# 1. Pull latest code
echo "--> git pull"
git -C "$REPO_DIR" pull --ff-only

# 2. Install / upgrade Python dependencies
echo "--> pip install -r requirements.txt"
"$VENV_PYTHON" -m pip install -q -r "$REPO_DIR/requirements.txt"

# 3. Restart the systemd user service
echo "--> systemctl --user restart $SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "==> Done. Check status with: journalctl --user -u $SERVICE_NAME -f"
