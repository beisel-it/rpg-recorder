# Task: Discord Bot Core — /record start/stop
Shortcode: RPGREC-002
Stage: refinement
Status: ready for refinement
Priority: P1
Definition of Done:
- /record start: Bot joined Voice-Channel, separate Audio-Buffer pro User geöffnet
- /record stop: Bot verlässt Channel, .flac-Dateien pro Sprecher gespeichert
- /record status: zeigt ob Aufnahme läuft + Dauer
- Bestätigung im Text-Channel nach Start/Stop
- Läuft als systemd-Service auf beisel.it, auto-restart

## Steps
- discord.py + discord-ext-voice-receive Setup
- Voice Receive per User implementieren
- .flac Export (one file per user)
- /record slash commands (start/stop/status)
- systemd unit file

## Blocking
- Abhängig von RPGREC-001 (Tech Stack Research)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Code-Manager: Wilbur
