# Task: Transkript-Timeline + Synchronisation
Shortcode: RPGREC-004b
Epic: RPGREC-004
Stage: code
Status: ready for code
Priority: P2
Assigned: Wilbur
Depends: RPGREC-004a
Estimated: 3h

## Definition of Done
- [ ] Transkript-Timeline scrollt automatisch mit Playback
- [ ] Aktives Segment visuell hervorgehoben
- [ ] Jeder Sprecher hat konsistente Farbe (Player-Regions + Timeline)
- [ ] Click auf Segment → Player springt zur Stelle
- [ ] Große Sessions (4h, 6 Sprecher): kein Lag beim Scrollen
- [ ] Virtualisierung: Nur sichtbare Segmente im DOM (für Performance)

## Acceptance Criteria
1. Play drücken → Transkript scrollt mit, aktives Segment highlighted
2. Click auf Segment 2h rein → Player springt, Transkript scrollt mit
3. 4h Session mit 2000+ Segmenten → Scroll flüssig (60fps)

## Comments
- Branch: `feature/RPGREC-004b-timeline`
