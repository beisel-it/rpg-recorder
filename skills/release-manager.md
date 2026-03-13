# Release Manager Skill (Projects)

Purpose: Own handoff from Code → Deployment → Docs → Done, safeguard CI/Release automation, and ensure releases are documented and auditable.

## Context & Paths
- Stages: `tasks/deployment/`, `tasks/docs/`, `tasks/done/`
- Handoff scripts:
  - `scripts/release_to_deployment <task-file>` → move from code to deployment (`Stage: deployment`, `Status: ready for deployment`).
  - `scripts/release_to_docs <task-file>` → move from deployment to docs (`Status: ready for docs`).
  - `scripts/finalize_done <task-file>` → mark docs as done (`Stage: done`, `Status: done`, move to `tasks/done/working/`).
  - `scripts/release_notes [<tag>]` → placeholder for release notes (git/gh-based stub).
- References: `docs/deployment-docs-guidance.md`, `docs/pr-playbooks.md`, `docs/workflow-notes.md`, CI/Release workflows under `.github/workflows/`.

## Release Packages
- Define release packages (set of tasks) and schedule drops (e.g., weekly). Track package tasks explicitly (list in task comments or a package note). Ensure only green tasks enter a package.
- Before coding starts: confirm package scope with PM/Code Manager.
- Before tagging: verify all package tasks are `done` (Deployment/Docs complete) and merged with green checks.

## Workflow
1) Prep: when Code signals `ready for deployment`, check rollout (flags, migrations, health, monitoring, rollback). Comment with branch/repo/commit and links to CI/Release runs.
2) Deployment handoff: run `release_to_deployment <task>` and ensure Stage/Status updated.
3) Docs handoff: after deployment OK, run `release_to_docs <task>`; add release notes, PRs, branches, deployment notes; include user/ops docs.
4) Finalize: when docs complete, run `finalize_done <task>` and, if needed, `release_notes <tag>` for summary.

## Checklists
- Deployment readiness: flags/toggles, DB migrations, secrets/env, health checks, monitoring, rollback plan, links to PR/branch/commit/CI.
- Docs & notes: user + ops docs; release tag/notes/PR links; known issues/TODOs captured; Status set to `ready for docs` → `done`.
- CI/Release: CI (`ci.yml`) runs shfmt/shellcheck/tests on every push/PR; Release (`release.yml`) on tags `v*` runs the same checks then `action-gh-release` with auto notes. Release Manager monitors both and validates release output. Merge policy: only PRs with passing checks are merged.
- Rollback: Task documents rollback or fix/patch path if release fails.
- Release packages: ensure package tasks are complete/green before tagging; communicate package contents and schedule.

## Communication & Rules
- Keep tasks in stage folders (not lingering in `working/`).
- Every handoff comment must include repo, branch, commit SHA, links to CI/Release runs, and package membership (if applicable).
- Blockers → set `Status: needs refinement`, document why.
- Branch policy: merge via PR with green checks; branch naming `<SHORTCODE>-<COUNTER>-<name>` enforced by hook; main is protected.
