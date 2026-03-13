# Task: Pipeline-Orchestrierung + Discord Webhook
Shortcode: RPGREC-003d
Epic: RPGREC-003
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-003a, RPGREC-003b, RPGREC-003c
Estimated: 2h

## Definition of Done
- [ ] Pipeline-Runner: ruft Whisper → Downmix → HTML-Gen nacheinander auf
- [ ] Startet automatisch nach `/record stop` (Subprocess, non-blocking)
- [ ] ETA-Nachricht im Discord: „⏳ Verarbeitung läuft (~X min)"
- [ ] Abschluss: „✅ Session #N bereit: https://rpg.beisel.it/sessions/N/"
- [ ] Fehler: „❌ Pipeline fehlgeschlagen: [Grund]. Audio gesichert unter ..."
- [ ] Timeout: Abbruch nach 2× Session-Dauer
- [ ] Queue: Wenn Pipeline läuft und neue Session endet → Warteschlange (FIFO)
- [ ] Nginx-Config: `rpg.beisel.it/sessions/` served statisch aus Output-Dir

## Acceptance Criteria
1. `/record stop` → innerhalb 5s kommt ETA-Nachricht, dann läuft Pipeline im Hintergrund
2. Pipeline fertig → Discord-Nachricht mit funktionierendem Link
3. Pipeline crasht → Fehler-Nachricht, Audio-Dateien trotzdem vorhanden
4. Zwei Sessions enden kurz nacheinander → zweite wartet, beide werden verarbeitet

## Comments
- Branch: `feature/RPGREC-003d-orchestration`
