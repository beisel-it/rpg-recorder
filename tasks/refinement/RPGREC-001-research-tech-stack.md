# Task: Tech Stack Research
Shortcode: RPGREC-001
Stage: refinement
Status: in progress
Priority: P1
Assigned: Nova (Researcher)
Definition of Done:
- discord-ext-voice-receive: Stabilität, aktiv gewartet, bekannte Probleme bei langen Sessions (2-4h)?
- faster-whisper vs whisper: Empfehlung für DE/EN-Mix, RPG-Kontext (Eigennamen, Dialoge)
- Wavesurfer.js: Erfahrungen mit sehr langen Audiodateien (2-4h), Regions-Plugin für Speaker-Segmente?
- Alternativen zu discord-ext-voice-receive falls instabil?
- Ergebnis als Markdown-Report in docs/research-tech-stack.md

## Steps
- Evaluiere discord-ext-voice-receive (GitHub Issues, letzter Commit, bekannte Bugs)
- Vergleiche whisper vs faster-whisper (Speed, Accuracy, RAM bei medium-Modell)
- Teste Wavesurfer.js Doku auf long-audio support
- Liefere Empfehlung mit Begründung

## Blocking
- None

## Comments
- Basis: docs/rpg-recorder-draft.md (Offene Fragen 1-6)
