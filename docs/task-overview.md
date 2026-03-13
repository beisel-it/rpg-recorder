# RPG Recorder — Task Overview

Stand: 2026-03-13 | Gepflegt von: Nova (Researcher)

## Phase 1 — MVP

| Task | Titel | Stage | Status | Prio | Assigned |
|------|-------|-------|--------|------|----------|
| RPGREC-001 | Tech Stack Research | research | ✅ done | P1 | Nova |
| RPGREC-005 | Plan B Voice Receive (DAVE) | research | ✅ done | P1 | Nova |
| RPGREC-002 | Bot Core (/record start/stop) | code | ready for code | P1 | Wilbur |
| RPGREC-003 | Post-Processing Pipeline | code | ready for code | P1 | Wilbur |
| RPGREC-004 | Web UI (Wavesurfer.js) | code | ready for code | P2 | Wilbur |

## Phase 2 — Erweiterungen

| Task | Titel | Stage | Status | Prio | Assigned |
|------|-------|-------|--------|------|----------|
| RPGREC-006 | Speaker Diarization Research | research | todo | P2 | Nova |
| RPGREC-007 | Session Security & DSGVO | research | todo | P2 | Nova |
| RPGREC-008 | Autojoin / Autostop | todo | needs refinement | P3 | TBD |

## Phase 3 — Smart Features

| Task | Titel | Stage | Status | Prio | Assigned |
|------|-------|-------|--------|------|----------|
| RPGREC-009 | Session-Index + Suche | todo | needs refinement | P3 | TBD |

## Recurring

| Task | Titel | Stage | Interval | Assigned |
|------|-------|-------|----------|----------|
| RPGREC-010 | DAVE Ecosystem Monitoring | research | weekly | Nova |

## Dependency Graph

```
RPGREC-001 ──┐
              ├──→ RPGREC-002 ──→ RPGREC-003 ──→ RPGREC-004
RPGREC-005 ──┘         │              │              │
                        │              ├──→ RPGREC-009
                        ├──→ RPGREC-008
                        │
RPGREC-006 ─────────────┤ (optional für Import-Feature)
RPGREC-007 ─────────────┘ (Security für alle Phases)
```

## Tech Stack (aus Research)

| Komponente | Entscheidung | Quelle |
|------------|-------------|--------|
| Voice Receive | discord.py + discord-ext-voice-recv | RPGREC-001 |
| E2EE | discord.py DAVE (PR #10300) | RPGREC-005 |
| Transkription | faster-whisper + large-v3-turbo | RPGREC-001 |
| Custom Vocabulary | initial_prompt (RPG-Eigennamen) | RPGREC-001 |
| Audio UI | Wavesurfer.js + Pre-decoded Peaks | RPGREC-001 |
| Speaker Segments | Wavesurfer Regions Plugin | RPGREC-001 |
