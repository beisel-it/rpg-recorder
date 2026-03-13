# Task: Research Tech Stack
Shortcode: RPGREC-001
Stage: research
Status: ready for code
Priority: P1
Definition of Done:
- discord-ext-voice-receive: Stabilität, aktive Wartung, bekannte Bugs bei langen Sessions (2-4h) bewertet
- faster-whisper vs. openai-whisper: Empfehlung für DE/EN-Mix RPG mit Eigennamen
- Wavesurfer.js: Performance bei 2-4h Audio, Regions-Plugin für Speaker-Segmente bewertet
- Ergebnis als docs/research-tech-stack.md im Repo

## Steps
- discord-ext-voice-receive evaluieren (PyPI, GitHub Activity, Issues)
- faster-whisper vs. whisper: Geschwindigkeit, Qualität, CPU/GPU
- Wavesurfer.js: Long-audio performance, Regions plugin für Speaker timeline
- Empfehlung formulieren

## Comments
- Erstellt von Marie (PM) 2026-03-13
- Refined by Dawn 2026-03-13: DoD klar, ready for research
- Research-Agent: Nova
- 2026-03-13 Nova: Research abgeschlossen → docs/research-tech-stack.md
  - discord-ext-voice-recv: nutzbar aber Alpha (Risiko MITTEL)
  - faster-whisper + large-v3-turbo empfohlen (4× schneller, initial_prompt für RPG-Namen)
  - Wavesurfer.js: nur mit Pre-decoded Peaks für 2-4h Audio, Regions Plugin perfekt für Speaker-Segmente
  - Status: ready for code
