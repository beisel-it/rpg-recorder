# Task: Discord Bot MVP — /record start/stop + .flac pro Sprecher
Shortcode: RPGREC-002
Stage: refinement
Status: in progress
Priority: P1
Assigned: Wilbur (Code Manager)
Definition of Done:
- /record start: Bot joint Voice-Channel des aufrufenden Users, Aufnahme läuft
- /record stop: Bot verlässt Channel, .flac pro Sprecher wird gespeichert
- /record status: Zeigt ob Aufnahme läuft + Dauer
- .flac Dateien: benannt nach Discord-Username + Session-ID
- Bot läuft als systemd-Service auf beisel.it (auto-restart)
- Kein Crash bei Sessions > 2h

## Steps
- discord.py 2.x + discord-ext-voice-receive einrichten
- Slash Commands implementieren
- Per-User Audio Buffer → .flac schreiben
- systemd Unit File
- Tests: kurze Session (5min), Disconnect-Verhalten

## Blocking
- RPGREC-001 (Tech Stack Research) — warten auf Bestätigung voice-receive stabil

## Comments
- Repo: github.com/beisel-it/rpg-recorder
- Branch: feature/RPGREC-002-discord-bot-mvp
- Stack: Python 3.11, discord.py, discord-ext-voice-receive
