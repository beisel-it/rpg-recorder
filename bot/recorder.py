"""
recorder.py — ChunkedFileSink and RecordingSession

Key design choices (per RPGREC-001/005 research):
- Only discord.py + discord-ext-voice-recv work post-DAVE enforcement (2026-03-02)
- 5-minute WAV chunks prevent memory leaks for 2-4 h sessions
- Reconnect watchdog with exponential back-off handles voice disconnects
- Health monitor logs KB/min per speaker, warns on >60 s silence
- FLAC conversion via ffmpeg subprocess after session ends
"""

import asyncio
import logging
import threading
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import discord
from discord.ext import voice_recv

log = logging.getLogger(__name__)

# Discord voice PCM format: 48 kHz, 16-bit signed, stereo
SAMPLE_RATE = 48_000
CHANNELS = 2
SAMPLE_WIDTH = 2               # bytes per sample (s16le)
BYTES_PER_SEC = SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH   # 192 000 B/s

CHUNK_SECONDS = 300            # 5-minute chunks ≈ 55 MB each
CHUNK_BYTES = BYTES_PER_SEC * CHUNK_SECONDS


# ---------------------------------------------------------------------------
# Per-speaker state (used inside ChunkedFileSink)
# ---------------------------------------------------------------------------

@dataclass
class _SpeakerState:
    user_id: int
    username: str
    chunk_dir: Path
    chunk_index: int = 0
    bytes_in_chunk: int = 0
    total_bytes: int = 0
    started_at: float = field(default_factory=time.monotonic)
    last_audio_at: float = field(default_factory=time.monotonic)
    chunk_paths: list = field(default_factory=list)
    _wav: Optional[wave.Wave_write] = field(default=None, repr=False)

    def _open_chunk(self) -> None:
        if self._wav:
            self._wav.close()
        path = self.chunk_dir / f"{self.user_id}_chunk{self.chunk_index:04d}.wav"
        self.chunk_paths.append(path)
        wav = wave.open(str(path), "wb")
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH)
        wav.setframerate(SAMPLE_RATE)
        self._wav = wav
        self.bytes_in_chunk = 0
        self.chunk_index += 1
        log.debug("Opened chunk %s for %s", path.name, self.username)

    def write(self, pcm: bytes) -> None:
        if self._wav is None:
            self._open_chunk()
        if self.bytes_in_chunk >= CHUNK_BYTES:
            self._open_chunk()
        self._wav.writeframes(pcm)
        n = len(pcm)
        self.bytes_in_chunk += n
        self.total_bytes += n
        self.last_audio_at = time.monotonic()

    def close(self) -> None:
        if self._wav:
            self._wav.close()
            self._wav = None

    def kbpm(self, now: float) -> float:
        elapsed = max(1.0, now - self.started_at)
        return self.total_bytes / 1024.0 / elapsed * 60.0


# ---------------------------------------------------------------------------
# ChunkedFileSink
# ---------------------------------------------------------------------------

class ChunkedFileSink(voice_recv.AudioSink):
    """Per-speaker AudioSink that writes 5-minute WAV chunks to disk.

    Prevents unbounded memory growth for sessions of 2–4 h.
    Thread-safe: discord.py calls write() from its voice receive thread.
    """

    # Request decoded PCM rather than raw Opus packets
    wants_opus: bool = False

    def __init__(self, chunk_dir: Path) -> None:
        super().__init__()
        self._chunk_dir = chunk_dir
        self._chunk_dir.mkdir(parents=True, exist_ok=True)
        self._speakers: dict[int, _SpeakerState] = {}
        self._lock = threading.Lock()

    # AudioSink interface ---------------------------------------------------

    def write(self, user: Optional[discord.User], data: voice_recv.VoiceData) -> None:
        if user is None:
            return
        uid = user.id
        name = getattr(user, "display_name", None) or getattr(user, "name", str(uid))
        with self._lock:
            if uid not in self._speakers:
                log.info("New speaker detected: %s (%d)", name, uid)
                self._speakers[uid] = _SpeakerState(
                    user_id=uid,
                    username=name,
                    chunk_dir=self._chunk_dir,
                )
            self._speakers[uid].write(data.pcm)

    def cleanup(self) -> None:
        with self._lock:
            for sp in self._speakers.values():
                sp.close()

    # Extra helpers ---------------------------------------------------------

    def health(self) -> dict[str, dict]:
        """Thread-safe snapshot of per-speaker stats."""
        now = time.monotonic()
        with self._lock:
            return {
                sp.username: {
                    "total_bytes": sp.total_bytes,
                    "silent_secs": round(now - sp.last_audio_at, 1),
                    "chunks": len(sp.chunk_paths),
                    "kbpm": round(sp.kbpm(now), 1),
                }
                for sp in self._speakers.values()
            }

    def speaker_count(self) -> int:
        with self._lock:
            return len(self._speakers)

    async def finalize(self, out_dir: Path) -> list[Path]:
        """Merge per-speaker WAV chunks → FLAC files via ffmpeg.

        Returns list of successfully written FLAC paths.
        Cleans up intermediate WAV chunk files on success.
        """
        with self._lock:
            speakers = list(self._speakers.values())

        results: list[Path] = []
        for sp in speakers:
            paths = [p for p in sp.chunk_paths if p.exists() and p.stat().st_size > 44]
            if not paths:
                log.warning("No audio data for speaker %s — skipping", sp.username)
                continue

            flac_path = out_dir / f"{sp.user_id}.flac"

            if len(paths) == 1:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(paths[0]),
                    "-c:a", "flac",
                    str(flac_path),
                ]
                list_file = None
            else:
                list_file = out_dir / f"{sp.user_id}_chunks.txt"
                list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in paths))
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(list_file),
                    "-c:a", "flac",
                    str(flac_path),
                ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode != 0:
                log.error("ffmpeg failed for %s: %s", sp.username, stderr.decode(errors="replace"))
            else:
                log.info("Finalized %s → %s", sp.username, flac_path.name)
                results.append(flac_path)
                for p in paths:
                    p.unlink(missing_ok=True)
                if list_file:
                    list_file.unlink(missing_ok=True)

        return results


# ---------------------------------------------------------------------------
# RecordingSession
# ---------------------------------------------------------------------------

class RecordingSession:
    """Manages one recording session: voice connection, sink, watchdog, health monitor."""

    _WATCHDOG_INTERVAL = 5    # seconds between liveness checks
    _HEALTH_INTERVAL   = 60   # seconds between health log entries
    _SILENT_THRESHOLD  = 60   # seconds of speaker silence before warning

    def __init__(self, channel: discord.VoiceChannel, sessions_dir: Path) -> None:
        ts = int(time.time())
        self.session_dir = sessions_dir / f"session-{ts}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        chunk_dir = self.session_dir / "chunks"
        self.sink = ChunkedFileSink(chunk_dir)
        self.channel = channel
        self.start_time = time.time()
        self.vc: Optional[voice_recv.VoiceRecvClient] = None
        self._active = False
        self._watchdog_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self.vc = await self.channel.connect(cls=voice_recv.VoiceRecvClient)
        self.vc.listen(self.sink)
        self._active = True
        self._watchdog_task = asyncio.create_task(
            self._watchdog(), name="voice-watchdog"
        )
        self._health_task = asyncio.create_task(
            self._health_loop(), name="voice-health"
        )
        log.info(
            "Recording started — channel=%s  dir=%s",
            self.channel.name,
            self.session_dir.name,
        )

    async def stop(self) -> list[Path]:
        """Stop recording and produce FLAC files.  Returns list of output paths."""
        self._active = False

        for task in (self._watchdog_task, self._health_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        if self.vc:
            try:
                self.vc.stop_listening()
            except Exception:
                pass
            try:
                await self.vc.disconnect(force=True)
            except Exception:
                pass

        self.sink.cleanup()
        return await self.sink.finalize(self.session_dir)

    def duration_str(self) -> str:
        secs = int(time.time() - self.start_time)
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # Background tasks ------------------------------------------------------

    async def _watchdog(self) -> None:
        """Reconnect to voice channel on disconnect, with exponential back-off."""
        while self._active:
            await asyncio.sleep(self._WATCHDOG_INTERVAL)
            if not self.vc or self.vc.is_connected():
                continue
            log.warning("Voice connection lost — reconnecting to #%s", self.channel.name)
            for attempt in range(6):
                try:
                    self.vc = await self.channel.connect(cls=voice_recv.VoiceRecvClient)
                    self.vc.listen(self.sink)
                    log.info("Reconnected (attempt %d)", attempt + 1)
                    break
                except Exception as exc:
                    wait = min(2 ** attempt, 60)
                    log.error(
                        "Reconnect attempt %d failed: %s — retry in %ds",
                        attempt + 1, exc, wait,
                    )
                    await asyncio.sleep(wait)
            else:
                log.error("All reconnect attempts failed for #%s", self.channel.name)

    async def _health_loop(self) -> None:
        """Log per-speaker KB/min every minute; warn on prolonged silence."""
        while self._active:
            await asyncio.sleep(self._HEALTH_INTERVAL)
            for name, stats in self.sink.health().items():
                silent = stats["silent_secs"]
                if silent > self._SILENT_THRESHOLD:
                    log.warning(
                        "[health] %s: no audio for %.0fs", name, silent
                    )
                log.info(
                    "[health] %s: %.1f KB/min  chunks=%d  silent=%.0fs",
                    name, stats["kbpm"], stats["chunks"], silent,
                )
