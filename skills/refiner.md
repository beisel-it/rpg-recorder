# Refiner Skill (Projects)

Purpose: schärft Aufgaben, liefert klare DoD und schiebt sie bereit für Research/Code.

## Kontexte & Pfade
- Tasks: `tasks/refinement/` (+ `working/`), handoff nach `tasks/research/`
- Command-Blocks: `skills/command-blocks.md`
- Helper-Skripte: `select_project`, `load_context`, `list_stage`, `claim_task`, `release_task`, `add_status`, `add_comment`, `take_task`, `new_task`

## Workflow
1) `select_project PR`, `load_context PR`.
2) `list_stage refinement` → wähle ein Item oder lege mit `new_task <name> refinement` an, `claim_task` (Status: in progress).
3) Ergänze DoD, Steps, Blocking. `add_status`/`add_comment` für Klarheit.
4) Wenn ready: `release_task <file>` mit `Status: ready for research` zurück aus `working/`.
5) Wenn unklar/input fehlt: `Status: needs refinement` + Kommentar, dann freigeben.

## Fallback / Requeue
- Unklare DoD, fehlende Artefakte → zurück an Refinement (`needs refinement`).
- Größere Pakete splitten (neue Tasks per `new_task`).

## Handoffs & Regeln
- DoD testbar halten.
- Stage/Status im Header pflegen.
- Hook: shfmt + shellcheck + tests/test_scripts.sh laufen im pre-commit.
