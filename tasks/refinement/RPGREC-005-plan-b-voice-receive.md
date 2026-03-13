# Task: Plan B — Discord Voice Receive (Fallback für discord-ext-voice-receive)
Shortcode: RPGREC-005
Stage: refinement
Status: ready for refinement
Priority: P1
Definition of Done:
- Mindestens 1 konkreter Plan B dokumentiert falls discord-ext-voice-receive instabil ist
- Plan B ist produktionstauglich für 2-4h Sessions (≥2 concurrent users)
- Implementierungsaufwand bewertet (einfach/mittel/komplex)
- Empfehlung: Plan A behalten oder direkt auf Plan B gehen?

## Hintergrund
Nova (RPGREC-001): discord-ext-voice-receive ist Alpha, Single Maintainer, Risiko MITTEL.
Custom Sink der periodisch auf Disk schreibt ist als Workaround bekannt.
Für ein Produktionsprojekt brauchen wir einen validen Fallback.

## Kandidaten zur Evaluierung
- Custom Discord Gateway (WebSocket direkt, kein Wrapper)
- discord.py fork mit stabilerem Voice Receive
- Vollständiger Plattformwechsel zu Mumble + mumblerecbot (war ursprünglich diskutiert)
- Andere Python-Bibliotheken (disnake, py-cord)?

## Steps
- Kandidaten identifizieren + bewerten
- Implementierungsaufwand einschätzen
- Empfehlung formulieren: Plan A (ext-voice-receive + Custom Sink) vs. Plan B

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Ausgelöst durch Nova's Research: discord-ext-voice-receive = Alpha, Risiko MITTEL
- Refiner: Dawn
- Researcher: Nova
