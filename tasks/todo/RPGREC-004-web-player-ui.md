# Task: Web Player — Wavesurfer.js + synchronisierte Transkript-Timeline
Shortcode: RPGREC-004
Stage: todo
Status: todo
Priority: P2
Assigned: Wilbur (Code Manager)
Definition of Done:
- Statisches HTML pro Session (generiert via Jinja2)
- Wavesurfer.js Player mit Waveform-Visualisierung (Downmix)
- Transkript-Timeline: scrollt synchron mit Playback
- Sprecher-Labels mit je eigener Farbe
- Klick auf Transkript-Segment → Player springt zur Stelle
- Sprecher-Filter (ein/ausblenden)
- Funktioniert bei 2-4h Sessions ohne Performance-Probleme

## Steps
- Wavesurfer.js + Regions-Plugin für Speaker-Segmente
- Jinja2-Template für HTML-Generierung
- Transkript-JSON → Timeline-Rendering
- Sprecher-Farben-Mapping
- Performance-Test mit 3h Audio

## Blocking
- RPGREC-003 muss done sein
- RPGREC-001 (Wavesurfer.js Research)

## Comments
- Branch: feature/RPGREC-004-web-ui
- Keine Server-Side-Rendering-Abhängigkeit nach Generierung
