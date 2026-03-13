"""
pipeline.py — Post-processing pipeline orchestration (RPGREC-003d).

Public API
----------
run_pipeline(session_dir, flac_paths, notify_channel=None) → dict
    Orchestrate Whisper → Downmix → HTML-Gen for one session.
    Posts Discord status messages to notify_channel.
    Returns {"speakers", "transcript_path", "mp3_path", "html_path"} on success
    or {"error": <reason>} on failure.

enqueue_pipeline(session_dir, flac_paths, notify_channel=None) → None
    Add a completed session to the global FIFO pipeline queue.
    Starts the background worker if not already running.
    Use this from the Discord cog so overlapping sessions are queued, not dropped.

Timeout
-------
asyncio.wait_for wraps the entire pipeline with a 6-hour deadline.

Queue
-----
A single asyncio worker task drains the FIFO queue sequentially, so two sessions
ending at the same time are both processed — the second waits for the first.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

PIPELINE_TIMEOUT: float = 6 * 3600  # 6 h max per session
SESSION_URL_BASE: str = "https://rpg.beisel.it/sessions/"

# ---------------------------------------------------------------------------
# Global FIFO queue + background worker
# ---------------------------------------------------------------------------

_queue: asyncio.Queue | None = None
_worker_task: asyncio.Task | None = None


def _get_queue() -> asyncio.Queue:
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


async def _pipeline_worker() -> None:
    """Background coroutine — drains the pipeline queue in FIFO order."""
    q = _get_queue()
    while True:
        session_dir, flac_paths, notify_channel = await q.get()
        try:
            await run_pipeline(session_dir, flac_paths, notify_channel)
        except Exception:
            log.exception("Unhandled error in pipeline worker for %s", session_dir)
        finally:
            q.task_done()


def enqueue_pipeline(
    session_dir: Path,
    flac_paths: list[Path],
    notify_channel: Any = None,
) -> None:
    """Add a completed session to the FIFO pipeline queue.

    Starts the background worker task if it is not already running.
    Safe to call from within a running event loop (e.g. a Discord command handler).
    """
    global _worker_task
    _get_queue().put_nowait((session_dir, flac_paths, notify_channel))
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.get_event_loop().create_task(_pipeline_worker())
        log.info("Pipeline worker started")


# ---------------------------------------------------------------------------
# Main pipeline coroutine
# ---------------------------------------------------------------------------


async def run_pipeline(
    session_dir: Path,
    flac_paths: list[Path],
    notify_channel: Any = None,
) -> dict:
    """Orchestrate the full post-processing pipeline for one recording session.

    Parameters
    ----------
    session_dir:    Session output directory (contains FLAC files + metadata.json).
    flac_paths:     Per-speaker FLAC paths to process.
    notify_channel: discord.abc.Messageable (or None) for progress messages.

    Returns
    -------
    On success: {"speakers", "transcript_path", "mp3_path", "html_path"}.
    On error:   {"error": <description>}.
    """
    session_name = session_dir.name
    duration_secs = _read_duration(session_dir)
    eta_min = max(1, round(duration_secs / 60 * 0.3)) if duration_secs else 5

    if notify_channel:
        await _safe_send(
            notify_channel,
            f"⏳ Processing `{session_name}` (~{eta_min} min)…",
        )

    try:
        result = await asyncio.wait_for(
            _run_steps(session_dir, flac_paths, notify_channel),
            timeout=PIPELINE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        msg = (
            f"❌ Pipeline timed out after 6 h for `{session_name}`. "
            f"Audio preserved at `{session_dir}`."
        )
        log.error(msg)
        if notify_channel:
            await _safe_send(notify_channel, msg)
        return {"error": "timeout"}
    except Exception as exc:
        msg = (
            f"❌ Pipeline failed: {exc}. "
            f"Audio preserved at `{session_dir}`."
        )
        log.exception("Pipeline failed for %s", session_name)
        if notify_channel:
            await _safe_send(notify_channel, msg)
        return {"error": str(exc)}

    return result


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------


async def _run_steps(
    session_dir: Path,
    flac_paths: list[Path],
    notify_channel: Any,
) -> dict:
    """Execute all pipeline steps sequentially; return result dict."""
    session_name = session_dir.name
    result: dict = {}

    # ------------------------------------------------------------------
    # Step 1: Transcription (per-speaker; transcribe_session isolates errors)
    # ------------------------------------------------------------------
    log.info("[%s] Step 1/3: Transcribing %d speaker(s)…", session_name, len(flac_paths))

    speaker_files: dict[str, Path] = {
        p.stem: p
        for p in flac_paths
        if p.exists() and p.stat().st_size > 0
    }

    transcript: list[dict] = []
    if speaker_files:
        from .transcribe import transcribe_session  # noqa: PLC0415

        transcript = transcribe_session(speaker_files)

    transcript_path = session_dir / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False))
    result["transcript_path"] = transcript_path
    result["speakers"] = list(speaker_files.keys())

    # ------------------------------------------------------------------
    # Step 2: Downmix all FLACs → session_full.mp3
    # ------------------------------------------------------------------
    log.info("[%s] Step 2/3: Downmixing…", session_name)
    mp3_path = session_dir / "session_full.mp3"
    try:
        from .downmix import downmix  # noqa: PLC0415

        await downmix(flac_paths, mp3_path)
        result["mp3_path"] = mp3_path
    except ValueError as exc:
        log.warning("[%s] Downmix skipped: %s", session_name, exc)
        result["mp3_path"] = None

    # ------------------------------------------------------------------
    # Step 3: HTML player generation
    # ------------------------------------------------------------------
    log.info("[%s] Step 3/3: Generating HTML player…", session_name)
    html_path = session_dir / "index.html"
    try:
        from .html_gen import generate_session_html  # noqa: PLC0415

        generate_session_html(session_dir, transcript, flac_paths)
    except ImportError:
        # html_gen not yet merged (RPGREC-003c) — write a minimal placeholder
        _write_stub_html(html_path, session_name, transcript, result.get("mp3_path"))
    result["html_path"] = html_path

    # ------------------------------------------------------------------
    # Step 4: Discord completion message
    # ------------------------------------------------------------------
    url = f"{SESSION_URL_BASE}{session_name}/"
    summary = (
        f"✅ Session `{session_name}` ready!\n"
        f"Speakers: **{len(result['speakers'])}** | "
        f"Segments: **{len(transcript)}**\n"
        f"🔗 {url}"
    )
    if notify_channel:
        await _safe_send(notify_channel, summary)

    log.info("[%s] Pipeline complete.", session_name)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_duration(session_dir: Path) -> float:
    """Read duration_seconds from metadata.json, or 0.0 if unavailable."""
    meta = session_dir / "metadata.json"
    if meta.exists():
        try:
            return float(json.loads(meta.read_text()).get("duration_seconds", 0.0))
        except Exception:
            pass
    return 0.0


async def _safe_send(channel: Any, text: str) -> None:
    """Send a Discord message, logging any failure without raising."""
    try:
        await channel.send(text)
    except Exception as exc:
        log.warning("Failed to send Discord notification: %s", exc)


def _write_stub_html(
    html_path: Path,
    session_name: str,
    transcript: list[dict],
    mp3_path: Path | None,
) -> None:
    """Write a minimal HTML placeholder (used when html_gen.py is not yet available)."""
    mp3_link = (
        f'<p><a href="{mp3_path.name}">Download MP3</a></p>'
        if mp3_path and mp3_path.exists()
        else ""
    )
    segments_html = "\n".join(
        f"<p><b>[{e['speaker']}]</b> "
        f"{e['start']:.1f}s – {e['end']:.1f}s: {e['text']}</p>"
        for e in transcript
    )
    html = (
        f"<!DOCTYPE html>\n"
        f"<html lang=\"en\">\n"
        f"<head><meta charset=\"utf-8\"><title>Session {session_name}</title></head>\n"
        f"<body>\n"
        f"<h1>Session {session_name}</h1>\n"
        f"{mp3_link}\n"
        f"<h2>Transcript</h2>\n"
        f"{segments_html or '<p><em>No transcript available.</em></p>'}\n"
        f"</body></html>"
    )
    html_path.write_text(html, encoding="utf-8")
