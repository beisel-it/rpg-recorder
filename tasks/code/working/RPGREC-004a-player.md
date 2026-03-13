# Task: Wavesurfer.js Player (Advanced)
Shortcode: RPGREC-004a
Epic: RPGREC-004
Stage: code
Status: ready for code
Priority: P2
Assigned: Wilbur
Depends: RPGREC-003c (Basis-HTML existiert)
Estimated: 3h

## Definition of Done
- [ ] Wavesurfer.js v7+ mit Regions Plugin
- [ ] Pre-decoded Peaks laden (KEINE Browser-Dekodierung)
- [ ] Audio via MediaElement streamen
- [ ] Farbcodierte Regions pro Sprecher
- [ ] Keyboard: Space = Play/Pause, ←/→ = ±10s, Shift+←/→ = ±60s
- [ ] Playback-Speed: 0.5x, 1x, 1.5x, 2x
- [ ] Mobile responsive (≥375px)

## Acceptance Criteria
1. 3h Session → Waveform in <2s, Play startet sofort, kein UI-Freeze
2. Keyboard Shortcuts funktionieren (Space, Pfeiltasten)
3. Mobile (375px): Player nutzbar, Regions sichtbar

## Comments
- Baut auf der einfachen Version aus RPGREC-003c auf
- Branch: `feature/RPGREC-004a-player`
