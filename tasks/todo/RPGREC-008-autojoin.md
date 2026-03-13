# Task: Autojoin / Autostop
Shortcode: RPGREC-008
Stage: todo
Status: needs refinement
Priority: P3
Assigned: TBD
Depends: RPGREC-002

## User Story
- US-004: Bot joint automatisch wenn ≥N User in definiertem Channel, stoppt wenn alle weg

## Definition of Done (Draft — needs Dawn refinement)
- [ ] Konfigurierbare Channel-Liste (welche Channels überwacht werden)
- [ ] Konfigurierbare Threshold (min. N User, default: 2)
- [ ] Debounce: Nicht sofort joinen/leaven bei kurzen Fluktuationen (z.B. 30s Delay)
- [ ] Consent-Check beim Autojoin (siehe RPGREC-007)
- [ ] Graceful Stop: Wie `/record stop` — Pipeline wird getriggert
- [ ] Override: `/record stop` beendet auch eine Auto-Session manuell

## Offene Fragen (für Refinement)
- Soll der Bot eine Nachricht senden wenn er auto-joint? ("🔴 Automatische Aufnahme gestartet")
- Was wenn nur 1 Person übrig bleibt — sofort stoppen oder N Minuten warten?
- Konfigurations-Interface: `.env`/Config-File oder Discord-Commands?

## Comments
- Erstellt von Nova 2026-03-13
- Phase 2 — nach MVP
- Needs Refinement by Dawn bevor Research/Code starten kann
