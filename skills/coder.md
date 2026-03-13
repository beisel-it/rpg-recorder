# Coder Skill (Projects)

Purpose: führt Implementierungen aus klar definierten Tasks, arbeitet sauber in eigener Working Copy.

## Setup & Branching
- Immer von aktuellem `main` branchen: fetch/pull, `git checkout -b feature/<task>`.
- Eigene Working Copy im Agent-Workspace (frischer Clone), keine geteilten Worktrees.
- Tasks sind nicht versioniert; Status/Notes lokal im Task-File halten.

## Helper-Skripte
- `select_project`, `load_context`, `list_stage`, `claim_task`, `release_task`, `add_status`, `add_comment`, `take_task`, `finish_task`, `new_task`.

## Workflow
1) `select_project PR`, `load_context PR`.
2) Task aus `tasks/code/` wählen, `claim_task <file>` → `code/working/`, Status: in progress.
3) Lockfile respektieren (siehe Code-Manager, TODO-Helper). Branch/Workspace notieren.
4) Implementieren, Tests/Checks laufen lassen. Fortschritt via `add_status`/`add_comment`.
5) Fertig: Handoff-Note (Branch, Repo, offene TODOs), `release_task <file>` mit `Status: ready for deployment` zurück aus `working/`.
6) Blocker/fehlende Inputs: `Status: needs refinement` + Kommentar, Lockfile bereinigen falls gesetzt.

## Hygiene
- Commits nur auf eigenem Branch; keine Task-Dateien committen.
- Dokumentiere Branch/Repo/Tests.
- Neuer Lauf → neue Working Copy.

## Hook
- pre-commit blockt commits auf main, führt shfmt, shellcheck, tests aus.
