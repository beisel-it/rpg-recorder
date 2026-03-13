# PM Skill (Projects)

Purpose: steuert das Projekt, priorisiert Aufgaben und sorgt für klare Übergaben zwischen den Stages.

## Kontexte & Pfade
- Projekt-Root: `projects/projects/`
- Tasks: `tasks/<stage>/` plus `working/` pro Stage
- Command-Blocks: `skills/command-blocks.md`
- Helper-Skripte: `scripts/new_task`, `select_project`, `list_stage`, `claim_task`, `release_task`, `add_status`, `add_comment`, `finish_task`, `take_task`

## Workflow
1) `select_project PR` und `load_context PR` vor jeder Auswahl.
2) `new_task <name>` für neue Items oder `list_stage refinement`/`todo` prüfen; picke 1–2 Items nach Priority.
3) `claim_task <file>` → Stage `refinement/working`, `Status: in progress`.
4) DoD prüfen/ergänzen, fehlende Infos als `add_comment` + ggf. `Status: needs refinement`.
5) Wenn klar definiert: `release_task <file>` mit `Status: ready for research` zurück nach `refinement/`.
6) Falls Repo fehlt: `create_repo PR` (Stub) und `add_comment` mit URL (manuell eintragen).
7) PR/Merge Flow: Branch-Naming `<SHORTCODE>-<COUNTER>-name`, Merge via GitHub PR (keine direkten main-Commits; Hook erzwingt es).

## Handoffs & Regeln
- Jede Übergabe aktualisiert `Stage` + `Status` im Task-Header.
- Blocker dokumentieren.
- Tasks ohne klare DoD nicht weitergeben.
- Tests/Hook: pre-commit formatiert (shfmt), lintet (shellcheck) und läuft `tests/test_scripts.sh`.
