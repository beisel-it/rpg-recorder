# Task: Session-Übersichtsseite + Stichwort-Suche
Shortcode: RPGREC-009
Stage: todo
Status: needs refinement
Priority: P3
Assigned: TBD
Depends: RPGREC-003, RPGREC-004

## User Story
- US-011: Index aller archivierten Sessions (Datum, Dauer, Teilnehmer, Link)
- Phase 3: Stichwort-Suche über alle Sessions

## Definition of Done (Draft — needs Dawn refinement)
- [ ] Statische Index-Seite: automatisch nach jeder neuen Session aktualisiert
- [ ] Pro Session: Datum, Dauer, Teilnehmer, Thumbnail-Waveform, Link
- [ ] Sortierung: neueste zuerst, Filter nach Teilnehmer
- [ ] Volltextsuche über alle Transkripte (Stichwort → Session + Zeitstempel)
- [ ] Suchindex: Pre-built (z.B. Lunr.js oder MiniSearch) — kein Backend nötig

## Offene Fragen
- Reicht ein statischer Suchindex (Lunr.js) oder brauchen wir ein Backend (SQLite + API)?
- Wie groß wird der Suchindex bei 50+ Sessions à 3h?
- Design: Separate Seite oder integriert in Session-Viewer?

## Comments
- Erstellt von Nova 2026-03-13
- Phase 3 — nach Web-UI
- Needs Research (Suchindex-Technologie) + Refinement
