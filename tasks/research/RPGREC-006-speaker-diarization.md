# Task: Research Speaker Diarization
Shortcode: RPGREC-006
Stage: research
Status: todo
Priority: P2
Assigned: Nova (Researcher)

## Kontext
In Phase 1 identifizieren wir Sprecher über Discord-User-IDs (jeder User = separater Audio-Stream). Aber: Was wenn die Gruppe eine gemischte Aufnahme importiert (manuell aufgenommen, kein Bot)? Dann brauchen wir automatische Speaker Diarization.

## Research-Fragen
1. **pyannote.audio**: Accuracy für DE/EN, GPU-Requirements, Lizenz (kommerziell erlaubt?), Setup-Aufwand?
2. **NeMo MSDD** (Nvidia): Vergleich zu pyannote, Performance bei 2-4h Audio?
3. **WhisperX** (mit integrierter Diarization): Taugt das als All-in-One Alternative zu faster-whisper + separater Diarization?
4. Wie verhält sich Diarization bei RPG-Sessions (viele kurze Wechsel, Zwischenrufe, lachen)?
5. Fallback: Kann man Diarization optional machen? (Bot-Aufnahme = User-IDs, Import = Diarization)

## Definition of Done
- [ ] Vergleichsmatrix: pyannote vs NeMo vs WhisperX (Accuracy, Speed, GPU, Lizenz)
- [ ] Empfehlung mit Begründung
- [ ] Performance-Schätzung für 3h Audio auf beisel.it Hardware (ARM64 oder GPU?)
- [ ] Architektur-Vorschlag: Wie integriert sich Diarization in die Pipeline?
- [ ] Ergebnis: `docs/research-speaker-diarization.md`

## Acceptance Criteria
1. Dokument enthält testbare Aussagen (nicht nur "ist gut")
2. GPU-Requirements klar beziffert (VRAM, Dauer pro Stunde Audio)
3. Lizenz-Frage geklärt (kommerziell nutzbar?)

## Comments
- Erstellt von Nova (Researcher) 2026-03-13
- Phase 2 Feature — nicht blocking für MVP
