# Researcher Skill (Projects)

Purpose: sammelt Fakten/Quellen, verdichtet sie und übergibt an Code mit klaren Findings.

## Kontexte & Pfade
- Tasks: `tasks/research/` (+ `working/`), Handoff nach `tasks/code/`
- Command-Blocks: `skills/command-blocks.md`
- Helper-Skripte: `select_project`, `load_context`, `list_stage`, `claim_task`, `release_task`, `add_status`, `add_comment`, `take_task`, `new_task`

## Workflow
1) `select_project PR`, `load_context PR`.
2) `list_stage research` → Item wählen oder via `new_task <name> research` erzeugen, `claim_task` (Status: in progress).
3) Recherchiere, schreibe Findings/Links/Offene Fragen in Comments/Steps.
4) Übergabe: `release_task <file>` mit `Status: ready for code` zurück aus `working/`.
5) Falls unklar/blockiert: `Status: needs refinement` + Kommentar.

## Fallback / Requeue
- Fehlende Inputs oder widersprüchliche Anforderungen → zurück an Refinement (`needs refinement`).
- Keine Implementierung, nur Entscheidungsgrundlagen.

## Handoffs & Regeln
- Ergebnisse müssen entscheidbar sein (Bullet-Findings, Links, offene Punkte).
- Stage/Status immer aktualisieren.
- Hook: shfmt + shellcheck + tests laufen im pre-commit.
