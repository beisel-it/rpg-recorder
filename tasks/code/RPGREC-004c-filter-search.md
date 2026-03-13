# Task: Sprecher-Filter + Suche + Export
Shortcode: RPGREC-004c
Epic: RPGREC-004
Stage: code
Status: ready for code
Priority: P2
Assigned: Wilbur
Depends: RPGREC-004b
Estimated: 3h

## Definition of Done
- [ ] Sprecher-Filter: Checkboxen, Toggle blendet Segmente in Player + Timeline ein/aus
- [ ] Freitext-Suche: Ergebnis-Liste mit Sprecher, Text-Snippet, Jump-to-Button
- [ ] Export .txt: Plain text mit Zeitstempeln + Speaker Labels
- [ ] Export .srt: Standard-Subtitle-Format
- [ ] Download-Buttons für alle Formate sichtbar

## Acceptance Criteria
1. "Florian" ausblenden → seine Regions + Timeline-Einträge verschwinden
2. Suche "Schwert" → Treffer gelistet, Click springt zur Stelle
3. .srt Export → importierbar in VLC, Timing korrekt
4. .txt Export → lesbar, Format: `[HH:MM:SS Speaker] Text`

## Comments
- Branch: `feature/RPGREC-004c-filter`
