# Task: Post-Processing Pipeline (Whisper + ffmpeg + HTML)
Shortcode: RPGREC-003
Stage: code
Status: ready for code
Priority: P1
Definition of Done:
- Whisper (faster-whisper) lokal über jede Sprecher-Spur → JSON {speaker, start, end, text}
- Error handling: einzelne Spur schlägt fehl → andere Spuren laufen weiter, Fehler dokumentiert
- ffmpeg Downmix aller Spuren → session-N_full.mp3, normalisiert auf -23 LUFS
- Timeout/Queue für Sessions bis 6+ Stunden
- Jinja2-Template → session-N/index.html (Wavesurfer.js Player + Transkript-Timeline)
- Discord-Webhook postet Download-Link nach Abschluss
- Pipeline startet vollautomatisch nach /record stop, kein manueller Eingriff

## Steps
- faster-whisper Integration (per-speaker)
- ffmpeg Downmix + Normalisierung (-23 LUFS)
- Transkript-JSON zusammenführen (Zeitstempel sortiert)
- Jinja2 → statisches HTML generieren
- Nginx-Serving auf beisel.it
- Discord-Webhook Integration

## Blocking
- RPGREC-001 (Tech Stack), RPGREC-002 (Bot Core)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Refined by Dawn: Error-Handling, LUFS-Target, Timeout/Queue ergänzt
- Code-Manager: Wilbur
