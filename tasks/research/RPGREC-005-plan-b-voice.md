# Task: Plan B Voice Receive
Shortcode: RPGREC-005
Stage: research
Status: ready for code
Priority: P1
Definition of Done:
- Kandidaten evaluiert: disnake, py-cord, WebSocket-custom, Mumble+mumblerecbot
- Kriterien: Maintenance-Status, Multi-User (≥2 concurrent), CPU/Memory, Maturity
- "Produktionstauglich" = Reconnect nach Voice-Drop, Logging, 2-4h stabil
- Implementierungsaufwand eingeschätzt
- Empfehlung: Plan A vs Plan B

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Research-Agent: Nova
- 2026-03-13 Nova: Research abgeschlossen → docs/research-plan-b-voice.md
  - KRITISCH: Discord DAVE/E2EE seit 2.3.2026 — Pycord kaputt (Error 4017), Disnake hat kein Voice Receive
  - discord.py + ext-voice-recv ist aktuell die EINZIGE funktionierende Option
  - Empfehlung: Plan A robust bauen (Custom Sink + Watchdog + Monitoring) statt auf Plan B hoffen
  - Kein realistischer Plan B verfügbar — Absicherung durch defensive Implementierung
  - Status: ready for code
