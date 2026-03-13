# Task: Slash Commands — /record start/stop/status
Shortcode: RPGREC-002d
Epic: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002c
Estimated: 2h

## Definition of Done
- [ ] `/record start`: Bot joint Voice-Channel des aufrufenden Users, startet ChunkedFileSink
- [ ] Bestätigung: „🔴 Aufnahme läuft — Session #N gestartet (X Teilnehmer)"
- [ ] `/record stop`: Bot stoppt Sink, merged Chunks → .flac, verlässt Channel
- [ ] Bestätigung: „⏹️ Aufnahme beendet — N Spuren gespeichert (Xh Ym)"
- [ ] `/record status`: Zeigt ob Aufnahme läuft, Dauer, aktive Sprecher
- [ ] Fehlerbehandlung: User nicht in Voice → klare Meldung. Bereits am Aufnehmen → Meldung.
- [ ] Permission-Check: Nur User mit bestimmter Rolle dürfen /record start/stop

## Acceptance Criteria
1. `/record start` ohne in Voice zu sein → "Du musst in einem Voice-Channel sein"
2. `/record start` während Aufnahme läuft → "Aufnahme läuft bereits seit X Min"
3. `/record stop` ohne laufende Aufnahme → "Keine aktive Aufnahme"
4. Kompletter Flow: start → 5 Min reden → stop → .flac Dateien + metadata.json vorhanden

## Comments
- Session-Counter: Auto-Increment, persistent (JSON-File oder Ordner-Zählung)
- Branch: `feature/RPGREC-002d-commands`
