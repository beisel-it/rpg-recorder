"""
config.py — Runtime configuration loaded from environment / .env file.

Exports
-------
DISCORD_TOKEN   str            Required. Bot token from Discord Developer Portal.
GUILD_ID        int | None     Optional. Guild ID for fast slash-command sync.
SESSIONS_DIR    Path           Where session folders are written (default: sessions/).
LOG_LEVEL       str            Logging level string, e.g. "INFO" (default: INFO).
config          Config         Typed dataclass bundling all settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Raw values — keep module-level names for backward compatibility
# ---------------------------------------------------------------------------

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]  # KeyError → clear missing-var signal

_guild_id_raw = os.getenv("GUILD_ID")
GUILD_ID: int | None = int(_guild_id_raw) if _guild_id_raw else None

SESSIONS_DIR: Path = Path(os.getenv("SESSIONS_DIR", "sessions"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
# Role name required to use /record start and /record stop.
# Set to None (unset) to allow everyone.
RECORDER_ROLE_NAME: str | None = os.getenv("RECORDER_ROLE_NAME") or None

# Whisper transcription settings (RPGREC-003a)
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_INITIAL_PROMPT: str | None = os.getenv("WHISPER_INITIAL_PROMPT") or None

# Autojoin settings (RPGREC-008)
# Comma-separated list of voice channel IDs to monitor (empty = disabled)
_autojoin_raw = os.getenv("AUTOJOIN_CHANNELS", "")
AUTOJOIN_CHANNELS: list[int] = (
    [int(cid.strip()) for cid in _autojoin_raw.split(",") if cid.strip()]
    if _autojoin_raw.strip()
    else []
)
# Minimum number of users in a channel before auto-recording starts
AUTOJOIN_MIN_USERS: int = int(os.getenv("AUTOJOIN_MIN_USERS", "2"))


# ---------------------------------------------------------------------------
# Typed Config object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Config:
    discord_token: str
    guild_id: int | None
    sessions_dir: Path
    log_level: str
    recorder_role_name: str | None
    whisper_model: str
    whisper_initial_prompt: str | None
    autojoin_channels: list[int]
    autojoin_min_users: int


config = Config(
    discord_token=DISCORD_TOKEN,
    guild_id=GUILD_ID,
    sessions_dir=SESSIONS_DIR,
    log_level=LOG_LEVEL,
    recorder_role_name=RECORDER_ROLE_NAME,
    whisper_model=WHISPER_MODEL,
    whisper_initial_prompt=WHISPER_INITIAL_PROMPT,
    autojoin_channels=AUTOJOIN_CHANNELS,
    autojoin_min_users=AUTOJOIN_MIN_USERS,
)
