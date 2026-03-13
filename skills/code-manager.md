# Code Manager Skill (Projects)

Purpose: Run coding/PR workstreams, manage lockfiles, and hand off cleanly to Deployment/Docs.

## Context & Paths
- Tasks: `tasks/code/` (+ `working/`), handoff to `tasks/deployment/` → `tasks/docs/` → `tasks/done/`
- Helper scripts: `select_project`, `load_context`, `list_stage`, `claim_task`, `release_task`, `add_status`, `add_comment`, `finish_task`, `take_task`, `new_task`, `lock_check`, `lock_upsert`, `lock_prune`, `release_to_deployment`, `release_to_docs`, `finalize_done`, `release_notes`
- Workspaces: per-agent workspace (e.g., `workspaces/codex`, `workspaces/claude`, `workspaces/wilbur`)
- Lockfile: `workspaces/<agent>/lockfile.jsonl`
- PR Playbooks: `docs/pr-playbooks.md` (review-pr → prepare-pr → merge-pr)
- MADR Template: `architecture/MADR-template.md`

## Agent Delegation (Subagents)
- Always set `timeoutSeconds` on `sessions_spawn` / `sessions_send`:
  - CODER: 600s
  - RESEARCHER: 300s
  - REFINER: 300s
- If `sessions_send` returns status="timeout": run continues. Do **not** respawn. Instead call `sessions_history` for the target session and read the latest assistant result.
- Provide dedicated workdir per agent (e.g., `workspaces/codex/<task>`); never share the same working dir concurrently.
- Branch naming: `<SHORTCODE>-<COUNTER>-<name>`; hook blocks commits to `main`.

## PR Merge Policy
- Repo policy: merge only when checks pass (GitHub branch protection on `main`).
- Before starting new work, list open PRs (e.g., `gh pr list --state open`) and merge green ones (`gh pr merge --merge <id>` or comment block). Use PR Playbooks where relevant.
- Record merges in task comments (`add_comment`) with PR link/commit SHA.

## Lockfile Fields & Recovery
- Fields: agent, task, stage, repo, branch, workspace, status (`running|needs-review|done|aborted`), updated_at, notes.
- Recovery: if a lock exists, check run/branch; if complete but undocumented → add docs/commits, then delete lock; if aborted/unknown → set task Status `needs refinement`, delete lock.
- Helpers:
  - `scripts/lock_check.sh` — read/list entries.
  - `scripts/lock_upsert.sh` — write/update/delete; supports `--stage` (default `unknown`). Example:
    - `scripts/lock_upsert.sh --agent codex --task PR-123 --stage code --status running --branch feature/PR-123-1`
    - `scripts/lock_upsert.sh --agent codex --task PR-123 --status done`
    - `scripts/lock_upsert.sh --agent codex --task PR-123 --delete`
  - `scripts/lock_prune.sh` — prune stale entries (e.g., `--max-age-days 30 --status done`, `--dry-run` to preview).
  - Note: scripts require `jq`; `lock_prune` uses GNU date for ISO parsing.

## Workflow
1) `select_project PR`, `load_context PR`.
2) `list_stage code` → `claim_task <file>` into `code/working/`, set Status: in progress.
3) Set/verify lockfile; run agent in its own workspace/branch from `main`; merge via PR (no direct `main`).
4) Before new work, check open PRs; merge green PRs (checks passing) via `gh pr merge`.
5) Document progress (`add_status`, `add_comment`) including branch/repo.
6) PR flow: `review-pr` → `prepare-pr` → `merge-pr` per `docs/pr-playbooks.md`.
7) If implemented/tested: hand off via `release_to_deployment <file>` (or `release_task` with Status ready for deployment).
8) Deployment/Docs handoff via `release_to_docs` → `finalize_done`.
9) Blockers: set `Status: needs refinement`, add comment, clear lock if set.

## Fallback & Requeue
- Unclear DoD or missing inputs → `needs refinement`, back to Refinement.
- Large tasks → split and create new tasks (`new_task`).
- Always note branch/repo in handoffs.

## Deployment/Docs Checklist
- Deployment: rollout steps, flags, migrations, checks (target `tasks/deployment/`).
- Docs: user/ops docs, links to PR/branch/deploy notes (target `tasks/docs/`).
- Handoff: update Status (`ready for deployment` → `ready for docs` → `done`), list open TODOs.

## MADR
- Architecture/Workflow decisions as MADR: `architecture/MADR-template.md`.

## Handoffs & Rules
- Keep Stage/Status current on every handoff.
- Update lockfile on every run; remove on completion.
- Handoffs must include branch, repo, open TODOs.
- Hook: pre-commit blocks `main`, runs shfmt, shellcheck, tests.
