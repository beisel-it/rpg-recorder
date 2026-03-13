# Task: HTML-Generierung (Jinja2 Template)
Shortcode: RPGREC-003c
Epic: RPGREC-003
Stage: code
Status: ready for code
Priority: P2
Assigned: Wilbur
Depends: RPGREC-003a, RPGREC-003b
Estimated: 3h

## Definition of Done
- [ ] Jinja2-Template → `output/<session-id>/index.html`
- [ ] Eingebetteter Wavesurfer.js Player mit Pre-decoded Peaks
- [ ] Transkript-Timeline mit Sprecher-Labels + Farben (einfache Version)
- [ ] Click auf Segment → Player springt zur Stelle
- [ ] Download-Links: .mp3 Downmix + .flac Einzelspuren
- [ ] Session-Info: Datum, Dauer, Teilnehmer
- [ ] Alle Assets (JS, CSS) self-hosted (kein CDN)
- [ ] Dark Mode Default

## Acceptance Criteria
1. `index.html` öffnen → Waveform sichtbar in <2s, Play funktioniert
2. Transkript scrollbar, Click auf Segment → Player springt
3. Keine externe Netzwerk-Requests (offline-fähig nach Load)

## Comments
- Das ist die einfache Version. RPGREC-004 macht das fancy (Filter, Suche, Keyboard Shortcuts)
- Branch: `feature/RPGREC-003c-html`
