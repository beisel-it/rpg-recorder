# New Project Skill

Purpose: bootstrap a project repo with task structure, templates, and a pre-commit hook that blocks commits to main.

## Usage
- From repo root: `scripts/new_project`
- Creates directories: architecture, code, decisions, docs, scripts, skills, tasks/* with working/, tests/
- Adds `tasks/templates/PR-TASK-template.md`
- Writes `scripts/pre-commit.template` and installs it to `.git/hooks/pre-commit` (if .git exists)
  - Hook blocks commits to `main`, runs shfmt/shellcheck if available, and `tests/test_scripts.sh` when present

## Notes
- Tasks remain gitignored (only templates/README tracked as needed)
- If run outside git, hook is only written as template; install manually when git is initialized.
