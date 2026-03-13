# Task: Research Session Security & Access Control
Shortcode: RPGREC-007
Stage: research
Status: todo
Priority: P2
Assigned: Nova (Researcher)

## Kontext
Sessions enthalten private Gespräche. Die URLs müssen geschützt sein — keine öffentlichen RPG-Sessions.

## Research-Fragen
1. **Token-URLs**: Wie lang sollte der Token sein? Expiry? Revoke-Mechanismus?
2. **Nginx Auth**: Basic Auth vs. Token-URL vs. Lua-basierte Token-Prüfung — was ist am einfachsten mit statischem HTML?
3. **Discord-basierte Auth**: Kann man den Zugriff auf Session-Teilnehmer beschränken? (OAuth2 → Discord-User-ID → war in der Session?)
4. **Datenhaltung**: Wie lange Sessions aufbewahren? Auto-Cleanup? DSGVO-Aspekte (Stimme = biometrisches Datum)?
5. **Consent**: Wie sicherstellen dass alle Teilnehmer der Aufnahme zustimmen? (Bot-Nachricht beim Join?)

## Definition of Done
- [ ] Empfehlung für Access-Control-Modell (Token-URL, Auth, oder Hybrid)
- [ ] DSGVO-Einschätzung: Stimme als biometrisches Datum — was müssen wir beachten?
- [ ] Consent-Flow-Vorschlag für Bot
- [ ] Ergebnis: `docs/research-session-security.md`

## Acceptance Criteria
1. Mindestens 2 Access-Control-Varianten verglichen (Aufwand, Sicherheit, UX)
2. DSGVO-Einschätzung basiert auf konkreten Artikeln, nicht Bauchgefühl
3. Consent-Flow beschrieben (wann, wie, was passiert bei Ablehnung)

## Comments
- Erstellt von Nova (Researcher) 2026-03-13
- DSGVO ist kein Nice-to-have — Stimmaufnahmen sind sensibel
