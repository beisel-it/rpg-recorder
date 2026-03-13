# 🎲 RPG Recorder

> Record your tabletop sessions — per speaker, automatically transcribed, beautifully presented.

A Discord bot that captures per-speaker voice audio from your RPG sessions, transcribes everything with [faster-whisper](https://github.com/SYSTRAN/faster-whisper), and delivers a web page with a synchronized audio player and transcript timeline.

---

## ✨ Features

- 🎙️ **Per-speaker recording** — separate `.flac` file per participant
- 🤖 **Auto-transcription** — faster-whisper (local, no API costs)
- 🌊 **Web player** — Wavesurfer.js with color-coded speaker timeline
- 🔍 **Click-to-seek** — click any transcript segment, player jumps there
- 📤 **Auto-delivery** — Discord webhook posts the session link when ready
- 🛡️ **Resilient** — custom disk-sink, watchdog, reconnect logic (DAVE/E2EE ready)

---

## 🏗️ Architecture

```
Discord Voice  ──►  discord.py + discord-ext-voice-receive
                           │
                    .flac per speaker
                           │
                    faster-whisper (local)
                           │
               JSON transcript + ffmpeg downmix
                           │
               Jinja2 → static HTML + Wavesurfer.js
                           │
               Nginx / beisel.it  ◄──  Discord Webhook
```

---

## 📋 Requirements

- Python 3.11+
- `ffmpeg` on the host (`apt install ffmpeg` / `brew install ffmpeg`)
- `audiowaveform` for pre-decoded peaks (`apt install audiowaveform`)
- Discord bot token with **Voice** and **Slash Commands** permissions

---

## 🚀 Setup

```bash
# 1. Clone and install
git clone https://github.com/beisel-it/rpg-recorder.git
cd rpg-recorder
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
$EDITOR .env   # set DISCORD_TOKEN at minimum

# 3. Run
python -m bot
```

Expected output when online:

```
2026-01-01 12:00:00  INFO  rpg-recorder — Logged in as YourBot#1234 — Ready
```

---

## ⚙️ Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | **yes** | — | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `GUILD_ID` | no | *(global)* | Guild ID for instant slash-command sync (dev mode) |
| `SESSIONS_DIR` | no | `sessions` | Directory for session folders |
| `LOG_LEVEL` | no | `INFO` | `DEBUG` · `INFO` · `WARNING` · `ERROR` |

Missing `DISCORD_TOKEN` → bot exits with `KeyError: 'DISCORD_TOKEN'` at startup.

---

## 🎮 Slash Commands

| Command | Description |
|---|---|
| `/record start` | Join voice channel and start recording |
| `/record stop` | Stop recording, export `.flac` per speaker, trigger pipeline |
| `/record status` | Show recording state + per-speaker health stats |

---

## 🔧 Development

```bash
pip install -e ".[test]"
pytest
```

---

## 🗂️ Project Structure

```
rpg-recorder/
├── bot/                  # Discord bot core
├── pipeline/             # Whisper + ffmpeg + HTML generation
├── web/                  # Wavesurfer.js templates
├── tasks/                # Project task tracking
│   ├── research/
│   ├── code/
│   └── refinement/
├── docs/                 # Research & architecture docs
└── skills/               # Agent role definitions
```

---

## 👥 Team

| Role | Agent | Responsibility |
|---|---|---|
| 📋 PM + Release | Marie | Coordination, PRs, roadmap |
| ✏️ Refiner | Dawn | Task DoD review |
| 🔭 Researcher | Nova | Tech stack evaluation |
| 🛠️ Code Manager | Wilbur | Implementation |

---

## 📄 License

Private — [beisel-it](https://github.com/beisel-it)
