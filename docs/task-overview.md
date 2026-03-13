# RPG Recorder — Task Overview

Stand: 2026-03-13 | Gepflegt von: Nova (Researcher)

## Phase 1 — MVP

### Research (✅ done)
| Task | Titel | Status |
|------|-------|--------|
| RPGREC-001 | Tech Stack Research | ✅ done |
| RPGREC-005 | Plan B Voice / DAVE | ✅ done |

### RPGREC-002 — Bot Core (6 Arbeitspakete)
| Task | Titel | Est. | Depends | Status |
|------|-------|------|---------|--------|
| 002a | Project Setup + Bot Skeleton | 2h | — | ready |
| 002b | Voice Join + Per-User Capture | 3h | 002a | ready |
| 002c | ChunkedFileSink (Disk Recording) | 3h | 002b | ready |
| 002d | Slash Commands (/record) | 2h | 002c | ready |
| 002e | Reconnect-Watchdog + Monitoring | 2h | 002d | ready |
| 002f | systemd + Deployment | 1h | 002e | ready |

### RPGREC-003 — Pipeline (4 Arbeitspakete)
| Task | Titel | Est. | Depends | Status |
|------|-------|------|---------|--------|
| 003a | faster-whisper Integration | 3h | 002c | ready |
| 003b | ffmpeg Downmix + Peaks | 2h | 002c | ready |
| 003c | HTML-Generierung (Jinja2) | 3h | 003a, 003b | ready |
| 003d | Pipeline-Orchestrierung + Webhook | 2h | 003a-c | ready |

### RPGREC-004 — Web UI (3 Arbeitspakete)
| Task | Titel | Est. | Depends | Status |
|------|-------|------|---------|--------|
| 004a | Wavesurfer.js Player (Advanced) | 3h | 003c | ready |
| 004b | Transkript-Timeline + Sync | 3h | 004a | ready |
| 004c | Sprecher-Filter + Suche + Export | 3h | 004b | ready |

**Phase 1 Gesamt: ~30h Code (13 Arbeitspakete)**

## Phase 2 — Erweiterungen

| Task | Titel | Stage | Status | Prio |
|------|-------|-------|--------|------|
| RPGREC-006 | Speaker Diarization Research | research | todo | P2 |
| RPGREC-007 | Session Security & DSGVO | research | todo | P2 |
| RPGREC-008 | Autojoin / Autostop | todo | needs refinement | P3 |

## Phase 3 — Smart Features

| Task | Titel | Stage | Status | Prio |
|------|-------|-------|--------|------|
| RPGREC-009 | Session-Index + Suche | todo | needs refinement | P3 |

## Recurring
| Task | Titel | Interval |
|------|-------|----------|
| RPGREC-010 | DAVE Ecosystem Monitoring | weekly |

## Dependency Graph

```
002a → 002b → 002c → 002d → 002e → 002f
                 │
                 ├→ 003a ─┐
                 └→ 003b ─┼→ 003c → 003d
                          │
                          └→ 004a → 004b → 004c
```

**Kritischer Pfad:** 002a → 002b → 002c → 003a → 003c → 003d
**Parallelisierbar:** 003a + 003b können gleichzeitig (beide brauchen nur 002c)
