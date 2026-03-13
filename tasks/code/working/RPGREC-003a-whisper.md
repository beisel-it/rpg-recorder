# Task: faster-whisper Integration
Shortcode: RPGREC-003a
Epic: RPGREC-003
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002c (braucht .flac Output-Format)
Estimated: 3h

## Definition of Done
- [ ] faster-whisper mit `large-v3-turbo` Modell, läuft lokal
- [ ] Transkribiert eine .flac-Datei → JSON `[{speaker, start, end, text, confidence}]`
- [ ] Audio wird in ≤10-Min Chunks an Whisper übergeben (gegen Halluzinationen)
- [ ] `vad_filter=True` aktiviert
- [ ] `condition_on_previous_text=False`
- [ ] `initial_prompt` konfigurierbar via Config (RPG-Eigennamen)
- [ ] Fehlertoleranz: eine Spur schlägt fehl → Exception geloggt, andere Spuren laufen weiter
- [ ] Transkript-Merge: Alle Sprecher-JSONs → ein sortiertes `session-N.json`

## Acceptance Criteria
1. 10-Min .flac (Deutsch) → JSON mit plausiblen Zeitstempeln (±2s), Text lesbar
2. `initial_prompt="Thalindra, Grimjaw"` → diese Namen erscheinen korrekt im Transkript (wenn gesprochen)
3. .flac mit 5 Min Stille am Ende → keine Halluzinationen ("Danke fürs Zuschauen" etc.)
4. Kaputte .flac (0 Bytes) → Fehler geloggt, andere Spuren normal transkribiert

## Comments
- Modell-Download: ~3GB, beim ersten Start. In Deploy-Script berücksichtigen.
- Branch: `feature/RPGREC-003a-whisper`
