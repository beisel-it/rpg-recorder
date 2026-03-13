# RPG Session Recorder — Rohentwurf
_Stand: 2026-03-13 | Autor: Marie_

---

## Vision

Eine vollständige Pipeline, die aus einer Discord-Voice-Session ein archiviertes, durchsuchbares Session-Protokoll macht: Separate Audiospuren pro Sprecher, vollständiges Transkript mit Zeitstempeln und Sprecher-Labels, Downmix zum Abhören, und eine Webseite die alles zusammenhält.

---

## Globale Definition of Done (DoD)

- [ ] Bot läuft stabil auf beisel.it (systemd-Service, auto-restart)
- [ ] `/record start` und `/record stop` funktionieren in jedem Voice-Channel des Servers
- [ ] Pro Session entsteht ein Ordner mit: `.flac` pro Sprecher + Downmix + Transkript-JSON + HTML-Webseite
- [ ] Download-Link wird nach Session-Ende automatisch im Discord-Channel gepostet
- [ ] Webseite zeigt: Audio-Player (Downmix), synchronisierte Transkript-Timeline mit Sprecher-Labels, Timestamp-Navigation
- [ ] Kein manueller Eingriff nach `/record stop` nötig — Pipeline läuft vollautomatisch durch
- [ ] Whisper läuft lokal (kein Cloud-Datenschutzproblem)
- [ ] Links sind temporär oder passwortgeschützt (keine öffentliche RPG-Session)

---

## User Stories

### Bot & Aufnahme

**US-001 — Session starten**
> Als Spielleiter möchte ich mit `/record start` die Aufnahme starten, damit der Bot dem Voice-Channel beitritt und sofort mit der Aufnahme beginnt, ohne dass andere Spieler etwas tun müssen.

- Bot joint automatisch den Voice-Channel des aufrufenden Users
- Bestätigung im Text-Channel: „🔴 Aufnahme läuft — Session #42 gestartet"
- Pro verbundenem User wird ein separater Audio-Buffer geöffnet

**US-002 — Session beenden**
> Als Spielleiter möchte ich mit `/record stop` die Aufnahme beenden, damit die Pipeline automatisch anläuft und ich einen Link zum Ergebnis bekomme.

- Bot verlässt Voice-Channel
- Bestätigung: „⏳ Aufnahme beendet — Verarbeitung läuft (ETA: ~X min)"
- Nach Abschluss: „✅ Session #42 bereit: https://rpg.beisel.it/sessions/42"

**US-003 — Statusabfrage**
> Als Spieler möchte ich mit `/record status` sehen ob gerade eine Aufnahme läuft und wie lange sie schon geht.

**US-004 — Autojoin (Phase 2)**
> Als Gruppe möchten wir dass der Bot automatisch jointt wenn mindestens 2 Spieler in einem definierten Voice-Channel sind, und automatisch stoppt wenn alle gegangen sind.

- Konfigurierbarer Channel per Config-Datei
- Threshold: min. N User (konfigurierbar, default: 2)

---

### Audio

**US-005 — Separate Spuren**
> Als Session-Archivar möchte ich eine separate .flac-Datei pro Sprecher, damit ich einzelne Stimmen in der Nachbearbeitung isolieren kann.

- Dateiname: `session-42_florian.flac`, `session-42_tobias.flac` etc.
- Discord-Username als Dateiname

**US-006 — Downmix**
> Als Hörer möchte ich eine einzelne Audiodatei für die gesamte Session, damit ich sie bequem von Anfang bis Ende hören kann.

- ffmpeg-Downmix aller Spuren mit normalisierter Lautstärke
- Format: `.mp3` (kleinere Dateigröße für Web-Player)
- Dateiname: `session-42_full.mp3`

---

### Transkription

**US-007 — Vollständiges Transkript**
> Als Spielleiter möchte ich ein vollständiges Transkript der Session, damit ich im Nachhinein Ereignisse, Entscheidungen und Dialoge nachschlagen kann.

- Whisper läuft lokal über jede Sprecher-Spur separat
- Output: JSON mit Segmenten `{ speaker, start, end, text }`
- Kein Cloud-Upload — alles lokal

**US-008 — Sprecher-Labels im Transkript**
> Als Leser des Transkripts möchte ich sehen wer was gesagt hat, damit das Transkript lesbar und navigierbar ist.

- Discord-Username als Speaker-Label
- Format: `[12:34 Florian]: "Das Schwert leuchtet auf..."` 

---

### Web-Präsentation

**US-009 — Session-Webseite**
> Als Gruppe möchten wir eine Webseite pro Session, auf der wir die Session anhören und das Transkript mitlesen können.

- Statisches HTML (kein Backend nötig nach Generierung)
- Audio-Player (Wavesurfer.js): Downmix mit Waveform-Visualisierung
- Transkript-Timeline rechts/unten: scrollt synchron mit Playback
- Jeder Sprecher hat eine eigene Farbe
- Klick auf Transkript-Segment → Player springt zur Stelle

**US-010 — Sprecher-Filter**
> Als Leser möchte ich einzelne Sprecher ein- und ausblenden können, damit ich mich auf bestimmte Charaktere konzentrieren kann.

**US-011 — Session-Übersichtsseite (Phase 2)**
> Als Gruppe möchten wir eine Übersicht aller archivierten Sessions, damit wir gezielt ältere Sessions abrufen können.

- Index-Seite: Session-Datum, Dauer, Teilnehmer, Link
- Automatisch aktualisiert nach jeder neuen Session

---

## Architektur

```
Discord Voice Channel
        │
        ▼
[discord-recorder-bot]  (Python, discord.py + discord-ext-voice-receive)
        │
        ├── .flac pro User (raw audio streams)
        │
        ▼
[pipeline.py]  (Post-Processing, startet nach /record stop)
        │
        ├── whisper  →  transcripts/session-42-<user>.json
        ├── ffmpeg   →  session-42_full.mp3  (Downmix)
        └── jinja2   →  session-42/index.html  (Webseite)
                              │
                              ▼
                    [Nginx auf beisel.it]
                    https://rpg.beisel.it/sessions/42/
                              │
                              ▼
                    [Discord Webhook]
                    „✅ Session bereit: <link>"
```

---

## Tech Stack

| Komponente | Tech | Begründung |
|------------|------|------------|
| Bot | Python 3.11 + discord.py 2.x | Stabil, großes Ökosystem |
| Audio-Capture | discord-ext-voice-receive | Per-User-Streams in Discord |
| Audio-Format | .flac (Rohaufnahme) + .mp3 (Downmix) | Verlustfrei für Archiv, klein für Web |
| Transkription | OpenAI Whisper (lokal, medium-Modell) | Offline, gut für Deutsch + Englisch |
| Post-Processing | ffmpeg | Downmix + Normalisierung |
| Web-Player | Wavesurfer.js | Audio-Waveform + Timeline, besser als Three.js für diesen Use Case |
| Webseite | Jinja2-Templates → statisches HTML | Kein Backend nach Generierung nötig |
| Hosting | Nginx + beisel.it | Bereits vorhanden |
| Service | systemd user-service | Wie zeus-punch |

---

## Phasen

### Phase 1 — MVP (Wil)
- `/record start` / `/record stop`
- .flac pro Sprecher
- Downmix
- Transkript (plain text)
- Download-Link im Discord

### Phase 2 — Web-UI (Wil + Nova Research)
- Wavesurfer.js Player
- Synchronisierte Transkript-Timeline
- Sprecher-Farben + Filter
- Session-Index-Seite

### Phase 3 — Autojoin + Smart Features
- Autojoin/Autostop
- Kapitel-Erkennung (lange Pausen = neue Szene)
- Stichwort-Suche über alle Sessions

---

## Offene Fragen (für Nova Research)
1. Ist `discord-ext-voice-receive` in 2025 stabil und aktiv gewartet?
2. Gibt es bekannte Probleme mit Packet Loss / Audio-Lücken bei längeren Sessions (2-4h)?
3. Welches Whisper-Modell ist optimal für Deutsch/Englisch-Mix RPG (Dialoge, Eigennamen)?
4. Gibt es ein besseres Python-Paket als Whisper für lokale Transkription (z.B. faster-whisper)?
5. Wavesurfer.js — Erfahrungen mit sehr langen Audiodateien (2-4h)?
6. Alternative: Regions-Plugin in Wavesurfer für Speaker-Segmente?

---

## Nicht im Scope
- Video-Recording
- Live-Transkription während der Session
- Automatische NPC/PC-Erkennung
- Cloud-basierte Transkription (Datenschutz)

---

_Nächster Schritt: Delegation an Nova (Research) + Wilbur (Phase 1 MVP)_
