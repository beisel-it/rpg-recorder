# Task: ffmpeg Downmix + Peaks-Generierung
Shortcode: RPGREC-003b
Epic: RPGREC-003
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002c
Estimated: 2h

## Definition of Done
- [ ] ffmpeg Downmix aller Sprecher-.flac → `session-N_full.mp3`
- [ ] Lautstärke normalisiert auf -23 LUFS (EBU R128, zwei-Pass)
- [ ] `audiowaveform` generiert `session-N_peaks.json` (--pixels-per-second 2)
- [ ] Peaks-File <50KB auch für 4h Sessions
- [ ] Funktioniert mit 1 bis 8 Sprecher-Spuren

## Acceptance Criteria
1. 3 Sprecher-Spuren → Downmix klingt sauber, alle hörbar, keine Pegelspitzen
2. `ffmpeg -i session-N_full.mp3 -af loudnorm=print_format=json -f null -` → measured_I ≈ -23 LUFS
3. Peaks-File ladbar in Wavesurfer.js (Format-Validierung)
4. 1 Sprecher-Spur = 0 Bytes → Downmix enthält nur die anderen Spuren, kein Crash

## Comments
- `audiowaveform` muss installiert sein (apt: audiowaveform, oder build from source)
- Branch: `feature/RPGREC-003b-downmix`
