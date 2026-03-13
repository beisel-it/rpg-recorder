# Task: Web UI — Wavesurfer.js Player + Transkript-Timeline
Shortcode: RPGREC-004
Stage: code
Status: ready for code
Priority: P2
Assigned: Wilbur (Code Manager)
Depends: RPGREC-003

## User Stories
- US-009: Session-Webseite mit Player + synchronisiertem Transkript
- US-010: Sprecher ein-/ausblenden

## Definition of Done

### Player
- [ ] Wavesurfer.js v7+ mit Pre-decoded Peaks (KEINE Browser-Dekodierung!)
- [ ] Peaks via `peaks` Option laden (server-side generiert in RPGREC-003)
- [ ] Audio via MediaElement streamen (nicht komplett laden)
- [ ] Regions Plugin: Farbcodierte Segmente pro Sprecher
- [ ] Click auf Region → Playback ab dieser Stelle
- [ ] Keyboard: Space = Play/Pause, ←/→ = ±10s Seek, Shift+←/→ = ±60s

### Transkript-Timeline
- [ ] Scrollt synchron mit Playback (aktives Segment highlighted)
- [ ] Jeder Sprecher hat eigene Farbe (konsistent zwischen Player + Transkript)
- [ ] Click auf Transkript-Segment → Player springt zur Stelle
- [ ] Sprecher-Filter: Checkboxen zum Ein-/Ausblenden einzelner Sprecher
- [ ] Suchfunktion: Freitext-Suche im Transkript → Ergebnis-Liste mit Jump-to

### Export
- [ ] Transkript-Export als `.txt` (plain text mit Timestamps + Speaker)
- [ ] Transkript-Export als `.srt` (Subtitle-Format)
- [ ] Download-Links für alle Audio-Files (.flac Einzelspuren + .mp3 Downmix)

### Nicht-funktional
- [ ] Mobile responsive (≥375px Viewport)
- [ ] 4h Session mit 6 Speakern performant (kein UI-Freeze, <3s Initial Load)
- [ ] Funktioniert offline nach Initial Load (statisches HTML, alle Assets lokal)
- [ ] Dark Mode (da RPG-Sessions oft abends)
- [ ] Keine externen CDN-Dependencies (alle Assets self-hosted wg. Datenschutz)

### Acceptance Criteria
1. 3h Session laden → Waveform in <2s sichtbar, Play startet sofort
2. Beim Scrollen durch 4h Transkript: kein Lag, Scroll-Position synced mit Player
3. Sprecher "Florian" ausblenden → alle seine Segmente verschwinden aus Player + Transkript
4. Mobile (iPhone SE): Player + Transkript nutzbar, keine horizontale Scrollbar
5. Suche nach "Schwert" → alle Treffer gelistet, Click springt zur Stelle
6. `.srt` Export → korrekt importierbar in VLC
7. Seite funktioniert ohne Internetverbindung (nach Initial Load)

## Steps
1. Wavesurfer.js + Regions Plugin Setup
2. Peaks-Loading + MediaElement Playback
3. Transkript-JSON → Timeline-Rendering (Svelte/Vanilla JS)
4. Synchronisation Player ↔ Transkript
5. Sprecher-Farben + Filter-UI
6. Keyboard Shortcuts
7. Suchfunktion
8. Export (.txt, .srt)
9. Mobile Responsiveness + Dark Mode
10. Performance-Test: 4h/6-Speaker Session

## Research-Findings (relevant)
- **RPGREC-001**: Wavesurfer.js ohne Pre-decoded Peaks → Browser-Crash bei 2h+ Audio. MUSS Peaks nutzen.
- **RPGREC-001**: Regions Plugin ideal für Speaker-Segmente. Color-coding, click-to-play, drag-resize alles built-in.
- Peaks-Format: `audiowaveform -o peaks.json --pixels-per-second 2` (wenige KB pro Stunde)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Refined by Dawn: Mobile, Keyboard shortcuts, .srt Export ergänzt
- 2026-03-13 Nova: DoD erweitert mit Research-Findings (Pre-decoded Peaks mandatory, Performance-Kriterien, Acceptance Criteria, Dark Mode, Offline, Self-hosted Assets)
- Code-Manager: Wilbur
- Branch: `feature/RPGREC-004-web-ui`
