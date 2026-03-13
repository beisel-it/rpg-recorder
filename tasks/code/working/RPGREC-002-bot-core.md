# Task: Discord Bot Core — /record start/stop
Shortcode: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur (Code Manager)
Depends: RPGREC-001 ✅, RPGREC-005 ✅

## User Stories
- US-001: `/record start` → Bot joint Voice, Aufnahme läuft
- US-002: `/record stop` → Bot verlässt Channel, .flac gespeichert, Pipeline getriggert
- US-003: `/record status` → Zeigt ob Aufnahme läuft + Dauer + Teilnehmer

## Definition of Done

### Funktional
- [ ] `/record start`: Bot joint den Voice-Channel des aufrufenden Users
- [ ] Bestätigung im Text-Channel: „🔴 Aufnahme läuft — Session #N gestartet"
- [ ] Pro verbundenem User wird ein separater Audio-Stream aufgenommen
- [ ] `/record stop`: Bot verlässt Channel, pro Sprecher eine `.flac`-Datei gespeichert
- [ ] Bestätigung: „⏹️ Aufnahme beendet — N Spuren gespeichert (X min)"
- [ ] `/record status`: Zeigt Aufnahme-Status, Dauer, Liste der aktuellen Sprecher
- [ ] Multi-User: ≥4 gleichzeitige Sprecher getestet (typische RPG-Gruppe)
- [ ] Sessions ≥2h stabil (kein Memory-Leak, kein Audio-Verlust)

### Robustheit (aus RPGREC-005 Research)
- [ ] **ChunkedFileSink**: Audio wird in 5-Min WAV-Chunks auf Disk geschrieben (kein RAM-Buffering der gesamten Session)
- [ ] **Reconnect-Watchdog**: Bei Voice-Drop automatischer Rejoin + Sink-Restart innerhalb 10s
- [ ] **Health-Monitoring**: Bytes/Minute pro Speaker geloggt; Warning wenn Speaker >60s kein Audio liefert
- [ ] **DAVE/E2EE**: discord.py mit DAVE-Support (PR #10300) — Voice-Verbindung über E2EE verifiziert
- [ ] Graceful Shutdown: Bei Bot-Crash/Restart werden offene Audio-Chunks sauber geschlossen (kein Datenverlust)

### Technisch
- [ ] Python 3.11+, discord.py 2.x (mit DAVE), discord-ext-voice-recv
- [ ] `.flac` pro Sprecher: `output/<session-id>/<username>.flac`
- [ ] Session-Metadata: `output/<session-id>/metadata.json` (Start, Ende, Teilnehmer, Dauer)
- [ ] systemd user-service mit `Restart=on-failure`, `RestartSec=5`
- [ ] Config via `.env` oder `config.toml` (Token, Output-Dir, Guild-ID)
- [ ] Logging: strukturiert (JSON oder richtig formatiert), Level konfigurierbar

### Acceptance Criteria
1. Bot startet, joint Voice, nimmt 5 Min mit 2+ Speakern auf → separate .flac pro Speaker vorhanden + korrekt abspielbar
2. Während Aufnahme: ein Speaker disconnected kurz → Audio der anderen Speakers lückenlos, reconnected Speaker wird wieder aufgenommen
3. `/record stop` → alle .flac geschrieben, metadata.json korrekt, kein offener File-Handle
4. Bot-Process kill -9 während Aufnahme → nach Restart sind die bisherigen Chunks recoverable
5. 2h Dauertest mit 3 Speakern → Memory-Usage bleibt unter 500MB, keine Audio-Artefakte

## Steps
1. discord.py + discord-ext-voice-recv Setup mit DAVE-fähiger Version
2. ChunkedFileSink implementieren (5-Min WAV-Chunks → .flac Konvertierung nach Stop)
3. Slash Commands: /record start, stop, status
4. Reconnect-Watchdog als Background-Task
5. Health-Monitoring + Logging
6. Session-Metadata generieren
7. systemd Unit-File
8. Integration-Test: 30-Min Session mit 3+ Speakern

## Blocking
- ~~RPGREC-001 (Tech Stack Research)~~ ✅ Erledigt
- ~~RPGREC-005 (Plan B / DAVE Research)~~ ✅ Erledigt

## Research-Findings (relevant)
- **RPGREC-001**: discord-ext-voice-recv Alpha, Single Maintainer, aber einzige Option. Custom Sink nötig.
- **RPGREC-005**: DAVE/E2EE seit 2.3.2026 mandatory. Pycord kaputt, nur discord.py funktioniert. Plan A robust bauen statt Plan B.
- **Whisper**: faster-whisper + large-v3-turbo empfohlen (relevant für Pipeline-Interface)

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Refined by Dawn 2026-03-13: Multi-user, auto-restart, reconnect als DoD ergänzt
- 2026-03-13 Nova: DoD erweitert mit RPGREC-005 Findings (ChunkedFileSink, Watchdog, DAVE, Health-Monitoring, Acceptance Criteria)
- Code-Manager: Wilbur
- Branch: `feature/RPGREC-002-bot-core`
