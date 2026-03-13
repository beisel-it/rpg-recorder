# Task: Project Setup + Bot Skeleton
Shortcode: RPGREC-002a
Epic: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Estimated: 2h

## Definition of Done
- [ ] Python 3.11+ Projekt mit pyproject.toml oder requirements.txt
- [ ] discord.py 2.x (mit DAVE-Support) + discord-ext-voice-recv installierbar
- [ ] `.env.example` mit allen Config-Variablen (Token, Guild-ID, Output-Dir)
- [ ] Config-Modul: lädt .env, validiert Pflichtfelder, typed Config-Objekt
- [ ] Bot startet, loggt sich ein, zeigt "Ready" im Log
- [ ] Strukturiertes Logging (JSON oder formatiert, Level via ENV konfigurierbar)
- [ ] .gitignore, README.md mit Setup-Anleitung

## Acceptance Criteria
1. `pip install -r requirements.txt && python -m bot` → Bot ist online, "Ready" im Log
2. Fehlende ENV-Variable → klare Fehlermeldung, kein Crash ohne Kontext
3. `LOG_LEVEL=DEBUG` → Debug-Output sichtbar

## Comments
- Branch: `feature/RPGREC-002a-setup`
