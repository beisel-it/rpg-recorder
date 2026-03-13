# Task: Post-Processing Pipeline — Whisper + ffmpeg + HTML
Shortcode: RPGREC-003
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur (Code Manager)
Depends: RPGREC-002

## User Stories
- US-005: Separate .flac pro Sprecher (Input von RPGREC-002)
- US-006: Downmix → session-N_full.mp3
- US-007: Vollständiges Transkript mit Zeitstempeln
- US-008: Sprecher-Labels im Transkript

## Definition of Done

### Transkription
- [ ] faster-whisper mit `large-v3-turbo` Modell, lokal (kein Cloud-Upload)
- [ ] Jede Sprecher-Spur separat transkribiert
- [ ] `initial_prompt` mit RPG-Eigennamen konfigurierbar (pro Server/Gruppe)
- [ ] `vad_filter=True` aktiviert (gegen Halluzinationen bei Stille)
- [ ] `condition_on_previous_text=False` (gegen Halluzinations-Kaskaden)
- [ ] Audio wird in ≤10-Min Chunks an Whisper übergeben (gegen Long-Audio-Bugs)
- [ ] Output: `transcripts/session-N.json` mit Schema `[{speaker, start, end, text, confidence}]`
- [ ] Fehlertoleranz: eine Spur schlägt fehl → andere laufen weiter, Fehler in metadata.json dokumentiert

### Audio-Downmix
- [ ] ffmpeg Downmix aller Spuren → `session-N_full.mp3`
- [ ] Lautstärke normalisiert auf -23 LUFS (EBU R128)
- [ ] Peaks-File generiert via `audiowaveform` → `session-N_peaks.json` (für Wavesurfer.js)

### HTML-Generierung
- [ ] Jinja2-Template → `session-N/index.html` (statisch, kein Backend)
- [ ] Eingebetteter Wavesurfer.js Player mit Pre-decoded Peaks
- [ ] Transkript-Timeline mit Sprecher-Labels + Farben
- [ ] Download-Links für .flac-Einzelspuren + Downmix

### Automation
- [ ] Pipeline startet automatisch nach `/record stop` (Subprocess oder Queue)
- [ ] ETA-Nachricht im Discord: „⏳ Verarbeitung läuft (~X min)"
- [ ] Abschluss-Nachricht: „✅ Session #N bereit: https://rpg.beisel.it/sessions/N/"
- [ ] Timeout: Pipeline bricht nach 2× Session-Dauer ab + Fehler-Nachricht
- [ ] Queue: Wenn Pipeline läuft und neue Session endet → Warteschlange

### Technisch
- [ ] Nginx-Config für `rpg.beisel.it/sessions/` (statische Files)
- [ ] Sessions passwortgeschützt oder mit Token-URLs (kein öffentlicher Zugriff)
- [ ] Cleanup: Sessions älter als N Tage automatisch löschen (konfigurierbar)

### Acceptance Criteria
1. `/record stop` → ohne manuellen Eingriff: .mp3, .json, index.html, peaks.json generiert
2. 3h Session mit 4 Speakern → Pipeline komplett in <45 Min (auf beisel.it Hardware)
3. Transkript enthält korrekte Sprecher-Labels, Zeitstempel ±2s genau
4. Downmix klingt sauber (keine Pegelspitzen, keine Stille-Artefakte)
5. `rpg.beisel.it/sessions/N/` erreichbar, Player funktioniert, Transkript scrollt synchron
6. Eine Spur mit 0 Bytes Audio → Pipeline läuft trotzdem, Fehler dokumentiert

## Steps
1. faster-whisper Integration (per-speaker, chunked)
2. initial_prompt Config-System
3. ffmpeg Downmix + LUFS-Normalisierung
4. audiowaveform Peaks-Generierung
5. Transkript-JSON Merge + Sortierung nach Zeitstempel
6. Jinja2 → statisches HTML
7. Nginx Config + Token-URLs
8. Discord Webhook Integration
9. Queue/Timeout-System
10. Cleanup-Cron

## Research-Findings (relevant)
- **RPGREC-001**: faster-whisper 4× schneller als openai-whisper, gleiche Accuracy. `initial_prompt` für RPG-Eigennamen. `vad_filter=True` + Chunks gegen Halluzinationen.
- **RPGREC-001**: Wavesurfer.js MUSS Pre-decoded Peaks nutzen für 2-4h Audio. `audiowaveform` (BBC Tool) server-side.
- **RPGREC-001**: large-v3-turbo > large-v3 (weniger Halluzinationen) > large-v2 (Fallback)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Refined by Dawn: Error-Handling, LUFS-Target, Timeout/Queue ergänzt
- 2026-03-13 Nova: DoD erweitert mit Research-Findings (Whisper-Config, Peaks, Chunking, Acceptance Criteria)
- Code-Manager: Wilbur
- Branch: `feature/RPGREC-003-pipeline`
