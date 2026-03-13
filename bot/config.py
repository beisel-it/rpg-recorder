"""
config.py — Runtime configuration loaded from environment / .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
SESSIONS_DIR: Path = Path(os.getenv("SESSIONS_DIR", "sessions"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
