# Task: Post-Processing Pipeline (Whisper + ffmpeg + HTML)
Shortcode: RPGREC-003
Stage: refinement
Status: ready for refinement
Priority: P1
Definition of Done:
- Whisper läuft lokal über jede Sprecher-Spur → JSON mit {speaker, start, end, text}
- ffmpeg Downmix aller Spuren → session-N_full.mp3 (normalisiert)
- Jinja2-Template → session-N/index.html (Wavesurfer.js Player + Transkript-Timeline)
- Discord-Webhook postet Download-Link nach Abschluss
- Pipeline startet vollautomatisch nach /record stop, kein manueller Eingriff

## Steps
- faster-whisper Integration (per-speaker)
- ffmpeg Downmix + Normalisierung
- Transkript-JSON zusammenführen (Zeitstempel sortiert)
- Jinja2 → statisches HTML generieren
- Nginx-Serving auf beisel.it konfigurieren
- Discord-Webhook Integration

## Blocking
- Abhängig von RPGREC-001 (Tech Stack), RPGREC-002 (Bot Core)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Code-Manager: Wilbur
