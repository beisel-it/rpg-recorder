# Task: ChunkedFileSink — Disk-basiertes Recording
Shortcode: RPGREC-002c
Epic: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002b
Estimated: 3h

## Definition of Done
- [ ] `ChunkedFileSink(AudioSink)`: schreibt Audio in 5-Min WAV-Chunks auf Disk
- [ ] Pro User: eigenes Verzeichnis mit nummerierten Chunks (`chunk_001.wav`, ...)
- [ ] Kein RAM-Buffering der gesamten Session (Chunks werden geflushed + geschlossen)
- [ ] Bei Recording-Stop: alle offenen Chunks sauber geschlossen
- [ ] Chunk-Merge: Script/Funktion die Chunks → eine `.flac` pro User zusammenführt (ffmpeg)
- [ ] Session-Verzeichnis: `output/<session-id>/<username>/chunks/` + finale `<username>.flac`
- [ ] `metadata.json` pro Session: Start, Ende, Dauer, Teilnehmer-Liste

## Acceptance Criteria
1. 15-Min Aufnahme mit 2 Speakern → Chunks auf Disk, Memory-Usage <100MB
2. Kill -9 während Aufnahme → bisherige Chunks intakt + abspielbar
3. Chunk-Merge → .flac klingt lückenlos (keine Klicks/Pops an Chunk-Grenzen)
4. metadata.json enthält korrekte Dauer (±2s) und alle Teilnehmer

## Comments
- Chunk-Grenzen: exakt auf PCM-Frame-Boundary schneiden (keine halben Samples)
- Branch: `feature/RPGREC-002c-sink`
