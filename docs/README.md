# RPG Session Recorder

**Shortcode:** RPGREC  
**Status:** 🟢 Active  
**Priority:** P2  
**Start:** 2026-03-13  
**Target:** Phase 1 MVP in 2 Wochen  
**Repo:** github.com/beisel-it/rpg-recorder (privat)

## One-Liner
Discord-Bot der Voice-Sessions mit Sprechertrennung aufzeichnet, transkribiert und als Webseite mit synchronisierter Transkript-Timeline bereitstellt.

## Ziel
Vollständige Pipeline: `/record start` → separate .flac pro Sprecher → Whisper-Transkription → Downmix → statische Webseite mit Wavesurfer.js Player + Timeline.

## Phasen
- **Phase 1 (MVP):** Bot, /record start/stop, .flac pro Sprecher, Downmix, Plain-Transkript, Download-Link
- **Phase 2 (Web-UI):** Wavesurfer.js Player, synchronisierte Timeline, Sprecher-Farben/Filter
- **Phase 3 (Auto):** Autojoin/Autostop, Kapitel-Erkennung, Session-Index

## Stack
- discord.py + discord-ext-voice-receive
- ffmpeg (Downmix)
- Whisper lokal (faster-whisper, medium-Modell)
- Wavesurfer.js (Web-Player)
- Jinja2 → statisches HTML
- Nginx auf beisel.it
- systemd-Service

## Struktur
- `code/` — Bot + Pipeline
- `docs/` — Architektur, API-Doku
- `architecture/` — ADRs
- `tasks/` — Issues, Coding-Tasks, Research
