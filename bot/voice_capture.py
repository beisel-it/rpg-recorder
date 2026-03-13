"""
voice_capture.py — Voice join + per-user raw PCM capture (RPGREC-002b).

Provides the simplest possible voice capture to validate that
discord.py + discord-ext-voice-recv + DAVE work end-to-end.

This is intentionally simple — production recording uses ChunkedFileSink
in recorder.py (RPGREC-002c).  This module is the "does the stack work?"
proof-of-concept required by RPGREC-002b.

Usage (programmatic, no slash command required):

    session = VoiceCaptureSession(voice_channel, out_dir=Path("sessions/test"))
    await session.start()
    # ... wait / let audio flow ...
    pcm_files = await session.stop()
    # → [Path("sessions/test/1234567890.pcm"), Path("sessions/test/9876543210.pcm")]
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import IO, Optional

import discord
from discord.ext import voice_recv

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RawPCMSink — simple test sink that writes raw PCM per speaker
# ---------------------------------------------------------------------------

class RawPCMSink(voice_recv.AudioSink):
    """Per-speaker AudioSink that appends raw PCM bytes to one file per user.

    Intentionally minimal — no chunking, no WAV headers, no FLAC conversion.
    Purpose: validate that the discord.py + discord-ext-voice-recv + DAVE
    pipeline delivers audio, and that per-user demultiplexing works.

    Thread-safe: discord.py calls write() from its voice receive thread.
    """

    # Request decoded PCM from voice_recv rather than raw Opus packets.
    wants_opus: bool = False

    def __init__(self, out_dir: Path) -> None:
        super().__init__()
        self._out_dir = out_dir
        self._out_dir.mkdir(parents=True, exist_ok=True)
        self._handles: dict[int, IO[bytes]] = {}  # user_id → open file handle
        self._paths: dict[int, Path] = {}          # user_id → output path (tracks all seen)
        self._names: dict[int, str] = {}           # user_id → display name
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # AudioSink interface
    # ------------------------------------------------------------------

    def write(self, user: Optional[discord.User], data: voice_recv.VoiceData) -> None:
        """Receive a PCM chunk for *user* and append to their output file."""
        if user is None:
            return

        uid = user.id
        name = getattr(user, "display_name", None) or getattr(user, "name", str(uid))

        with self._lock:
            if uid not in self._handles:
                log.info("Speaker detected: %s (user_id=%d)", name, uid)
                path = self._out_dir / f"{uid}.pcm"
                self._handles[uid] = open(path, "wb")
                self._paths[uid] = path
                self._names[uid] = name
            self._handles[uid].write(data.pcm)

    def cleanup(self) -> None:
        """Close all open file handles.  Called by voice_recv on sink removal."""
        with self._lock:
            for fh in self._handles.values():
                fh.close()
            self._handles.clear()

    # ------------------------------------------------------------------
    # Inspection helpers (safe to call after cleanup)
    # ------------------------------------------------------------------

    @property
    def speakers(self) -> dict[int, str]:
        """Return {user_id: display_name} for every speaker seen so far."""
        with self._lock:
            return dict(self._names)

    def speaker_count(self) -> int:
        """Number of distinct speakers detected."""
        with self._lock:
            return len(self._paths)

    def output_files(self) -> list[Path]:
        """Return paths of all .pcm output files (safe to call after cleanup)."""
        with self._lock:
            return list(self._paths.values())


# ---------------------------------------------------------------------------
# VoiceCaptureSession — programmatic voice join + capture (no slash command)
# ---------------------------------------------------------------------------

class VoiceCaptureSession:
    """Join a voice channel and capture raw PCM per speaker (RPGREC-002b).

    Connects using VoiceRecvClient so that:
    - DAVE/E2EE handshake is handled automatically by discord.py
    - Per-user audio streams are demultiplexed by discord-ext-voice-recv
    - Each speaker gets a separate .pcm file in *out_dir*

    For production use (chunking, FLAC export, watchdog) see
    RecordingSession in recorder.py (RPGREC-002c+).

    Example::

        session = VoiceCaptureSession(channel, Path("sessions/test"))
        await session.start()
        await asyncio.sleep(30)
        files = await session.stop()
    """

    def __init__(self, channel: discord.VoiceChannel, out_dir: Path) -> None:
        self.channel = channel
        self.out_dir = out_dir
        self.sink = RawPCMSink(out_dir)
        self.vc: Optional[voice_recv.VoiceRecvClient] = None

    async def start(self) -> None:
        """Connect to the voice channel and start receiving audio.

        Uses VoiceRecvClient as the voice client class, which triggers the
        DAVE/E2EE handshake automatically.  A successful connect means
        Error 4017 did NOT occur.
        """
        channel_name = getattr(self.channel, "name", str(self.channel))
        guild_name = getattr(getattr(self.channel, "guild", None), "name", "unknown")
        log.info(
            "Connecting to #%s (guild=%s) with VoiceRecvClient",
            channel_name,
            guild_name,
        )
        # VoiceRecvClient handles the DAVE/E2EE handshake.
        # Error 4017 at this point → discord.py build lacks DAVE support.
        self.vc = await self.channel.connect(cls=voice_recv.VoiceRecvClient)
        log.info("DAVE handshake complete — connected, starting to listen")
        self.vc.listen(self.sink)

    async def stop(self) -> list[Path]:
        """Stop capturing, disconnect, and return list of written .pcm files.

        Safe to call even if start() was never called, or if the voice
        connection was already lost.
        """
        if self.vc is not None:
            try:
                self.vc.stop_listening()
            except Exception:
                pass
            try:
                await self.vc.disconnect(force=True)
            except Exception:
                pass

        self.sink.cleanup()

        files = [p for p in self.sink.output_files() if p.exists() and p.stat().st_size > 0]
        for uid, name in self.sink.speakers.items():
            log.info("Captured audio for: %s (user_id=%d)", name, uid)

        return files
