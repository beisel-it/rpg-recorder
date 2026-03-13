"""
transcribe.py — faster-whisper integration for RPG session transcription (RPGREC-003a).

Public API
----------
transcribe(flac_path, speaker, *, model, timeout) → list[dict]
    Transcribe a single audio file for one speaker.
    Returns [{speaker, start, end, text, confidence}, ...] sorted by start.

transcribe_session(speaker_files, *, model, timeout_per_speaker) → list[dict]
    Transcribe multiple speaker files, merge and sort by start time.
    One speaker failure logs an error and continues with the others.

Environment variables
---------------------
WHISPER_MODEL           Model name passed to WhisperModel (default: large-v3-turbo).
WHISPER_INITIAL_PROMPT  Optional prompt to bias vocabulary (e.g. RPG character names).
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (read once at module import; tests can monkeypatch these)
# ---------------------------------------------------------------------------

WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_INITIAL_PROMPT: str | None = os.getenv("WHISPER_INITIAL_PROMPT") or None

CHUNK_SECONDS: int = 600        # 10-minute chunks to prevent hallucinations
SESSION_TIMEOUT: float = 6 * 3600  # 6 h max per speaker


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_model() -> Any:
    """Lazily load WhisperModel — avoids GPU init at import time (and in tests)."""
    from faster_whisper import WhisperModel  # noqa: PLC0415

    return WhisperModel(WHISPER_MODEL, device="auto", compute_type="auto")


def _transcribe_chunks(
    audio_path: Path,
    model: Any,
    speaker: str,
) -> list[dict]:
    """Core transcription logic.

    Reads *audio_path* with soundfile, splits into ≤10-minute chunks, and runs
    faster-whisper on each chunk sequentially.  The per-chunk time-offset is
    added to segment timestamps so the final times are relative to the start of
    the full file.

    Parameters
    ----------
    audio_path: Path to the audio file (.flac or .wav).
    model:      Loaded WhisperModel instance.
    speaker:    Label embedded in every output segment.

    Returns
    -------
    List of ``{speaker, start, end, text, confidence}`` dicts.
    """
    import numpy as np       # noqa: PLC0415
    import soundfile as sf   # noqa: PLC0415

    # Guard: empty or missing file
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        log.warning("Skipping %s: file empty or missing", audio_path.name)
        return []

    audio, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)

    # stereo → mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if audio.size == 0:
        return []

    chunk_samples = int(CHUNK_SECONDS * sample_rate)
    entries: list[dict] = []

    chunk_ranges = range(0, len(audio), chunk_samples)
    for chunk_start in chunk_ranges:
        chunk: Any = audio[chunk_start : chunk_start + chunk_samples]
        offset_secs: float = chunk_start / sample_rate

        segments, _info = model.transcribe(
            chunk,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=WHISPER_INITIAL_PROMPT,
        )

        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            entries.append(
                {
                    "speaker": speaker,
                    "start": round(seg.start + offset_secs, 3),
                    "end": round(seg.end + offset_secs, 3),
                    "text": text,
                    "confidence": round(getattr(seg, "avg_logprob", 0.0), 4),
                }
            )

    return entries


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def transcribe(
    flac_path: Path,
    speaker: str = "unknown",
    *,
    model: Any | None = None,
    timeout: float = SESSION_TIMEOUT,
) -> list[dict]:
    """Transcribe a single audio file for one speaker.

    Parameters
    ----------
    flac_path:  Path to the .flac (or .wav) audio file.
    speaker:    Speaker label embedded in every output segment.
    model:      Pre-loaded WhisperModel; loaded lazily when omitted.
    timeout:    Max wall-clock seconds for the transcription (default: 6 h).

    Returns
    -------
    List of ``{speaker, start, end, text, confidence}`` dicts sorted by start.
    Returns ``[]`` for empty / corrupt input or on timeout.
    """
    if model is None:
        model = _get_model()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_transcribe_chunks, flac_path, model, speaker)
        try:
            entries = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            log.error(
                "Transcription timed out for %s after %.0f s", flac_path.name, timeout
            )
            return []

    return sorted(entries, key=lambda e: e["start"])


def transcribe_session(
    speaker_files: dict[str, Path],
    *,
    model: Any | None = None,
    timeout_per_speaker: float = SESSION_TIMEOUT,
) -> list[dict]:
    """Transcribe all speaker files; merge and sort by start time.

    Per-speaker errors are caught, logged, and do not abort the other speakers.

    Parameters
    ----------
    speaker_files:       ``{speaker_name: path_to_flac}`` mapping.
    model:               Shared WhisperModel; loaded lazily when omitted.
    timeout_per_speaker: Max seconds per speaker (default: 6 h).

    Returns
    -------
    Single merged list of ``{speaker, start, end, text, confidence}`` dicts,
    sorted by start time.
    """
    if model is None:
        model = _get_model()

    all_entries: list[dict] = []

    for speaker, path in speaker_files.items():
        try:
            entries = transcribe(
                path, speaker, model=model, timeout=timeout_per_speaker
            )
            all_entries.extend(entries)
            log.info(
                "Transcribed %s: %d segments from %s",
                speaker,
                len(entries),
                path.name,
            )
        except Exception as exc:
            log.error(
                "Transcription failed for speaker %s (%s): %s",
                speaker,
                path.name,
                exc,
                exc_info=True,
            )

    return sorted(all_entries, key=lambda e: e["start"])
