# RPG Recorder

Discord bot that records per-speaker voice audio from RPG sessions and exports FLAC files.

## Requirements

- Python 3.11+
- `ffmpeg` installed on the host (`apt install ffmpeg` / `brew install ffmpeg`)
- Discord bot token with **Voice** and **Slash Commands** permissions

## Setup

```bash
# 1. Clone and install dependencies
git clone <repo-url>
cd rpg-recorder
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
$EDITOR .env          # fill in DISCORD_TOKEN at minimum

# 3. Run the bot
python -m bot
```

Expected output when the bot is online:

```
2026-01-01 12:00:00  INFO      rpg-recorder — Logged in as YourBot#1234 (id=...) — Ready
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | **yes** | — | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `GUILD_ID` | no | *(global)* | Guild ID for instant slash-command sync (dev mode) |
| `SESSIONS_DIR` | no | `sessions` | Directory where session folders are written |
| `LOG_LEVEL` | no | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Missing `DISCORD_TOKEN` → bot exits with a `KeyError: 'DISCORD_TOKEN'` at startup.

## Slash Commands

| Command | Description |
|---|---|
| `/record start` | Join your voice channel and start recording |
| `/record stop` | Stop recording and export FLAC files per speaker |
| `/record status` | Show recording state and per-speaker health stats |

## Development

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests with coverage
pytest
```
