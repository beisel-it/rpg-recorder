# Task: Voice Join + Per-User Audio Capture
Shortcode: RPGREC-002b
Epic: RPGREC-002
Stage: code
Status: ready for deployment
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002a
Estimated: 3h

## Definition of Done
- [x] Bot kann einem Voice-Channel joinen (via Code-Aufruf, noch kein Slash Command)
- [x] `VoiceRecvClient` als Voice-Client-Klasse konfiguriert
- [x] DAVE/E2EE Handshake funktioniert (kein Error 4017)
- [x] Audio pro User empfangen (PCM-Daten im Callback)
- [x] Einfacher Test-Sink: schreibt Raw PCM in eine Datei pro User
- [x] Multi-User getestet: ≥2 gleichzeitige Sprecher → separate Dateien
- [x] Speaker-Detection: Log-Ausgabe wer gerade spricht

## Acceptance Criteria
1. Bot joint Channel, 2 User sprechen 30s → 2 separate PCM-Dateien, beide abspielbar
2. DAVE-Handshake im Log sichtbar (keine 4017-Errors)
3. User joint/leaved während Aufnahme → kein Crash, Audio der anderen intakt

## Comments
- Das ist der kritischste Task — hier zeigt sich ob discord-ext-voice-recv + DAVE funktioniert
- Branch: `feature/RPGREC-002b-voice`
- Implementation started on branch feature/RPGREC-002b-voice
- PR: https://github.com/beisel-it/rpg-recorder/pull/3
