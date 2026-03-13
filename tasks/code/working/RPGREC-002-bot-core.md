# Task: Discord Bot Core — /record start/stop
Shortcode: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Definition of Done:
- /record start: Bot joined Voice-Channel, separate Audio-Buffer pro User geöffnet
- /record stop: Bot verlässt Channel, .flac-Dateien pro Sprecher gespeichert
- /record status: zeigt ob Aufnahme läuft + Dauer
- Bestätigung im Text-Channel nach Start/Stop
- Multi-user voice (≥2 concurrent users) getestet
- systemd-Service mit auto-restart nach Crash
- Discord reconnection fallback implementiert
- Läuft stabil auf beisel.it

## Steps
- discord.py + discord-ext-voice-receive Setup
- Voice Receive per User implementieren
- .flac Export (one file per user)
- /record slash commands (start/stop/status)
- systemd unit file mit Restart=on-failure

## Blocking
- Empfehlung aus RPGREC-001 abwarten (voice-receive Stabilität)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Refined by Dawn 2026-03-13: Multi-user, auto-restart, reconnect als DoD ergänzt
- Code-Manager: Wilbur
