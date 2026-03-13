# Task: Post-Processing Pipeline — Whisper + ffmpeg Downmix + Download-Link
Shortcode: RPGREC-003
Stage: todo
Status: todo
Priority: P1
Assigned: Wilbur (Code Manager)
Definition of Done:
- Nach /record stop läuft Pipeline automatisch durch
- faster-whisper transkribiert jede Sprecher-Spur → JSON {speaker, start, end, text}
- ffmpeg Downmix aller Spuren → session-X_full.mp3 (normalisiert)
- Download-Link wird im Discord-Channel gepostet
- ETA-Nachricht: "⏳ Verarbeitung läuft (~X min)"

## Steps
- faster-whisper Integration (lokal, medium-Modell)
- ffmpeg Downmix mit Lautstärkenormalisierung
- Nginx-served temporäre Links auf beisel.it
- Discord Webhook für Ergebnis-Nachricht

## Blocking
- RPGREC-002 muss done sein

## Comments
- Kein Cloud-Upload (Datenschutz)
- Branch: feature/RPGREC-003-pipeline
