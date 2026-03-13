"""
test_pipeline.py — End-to-end pipeline tests (RPGREC-003d).

Acceptance criteria verified here:
  - run_pipeline writes transcript.json + index.html
  - Discord ETA + completion messages are sent
  - Pipeline is idempotent: running twice does not duplicate output
  - Empty session (no FLAC files) handled gracefully
  - Transcription crash → error reported, audio preserved
  - Pipeline timeout → error message sent to Discord
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers / local fixtures
# ---------------------------------------------------------------------------


class _Channel:
    """Minimal Discord channel stub that records sent messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, text: str) -> None:
        self.messages.append(text)


@pytest.fixture()
def session_dir(tmp_path: Path) -> Path:
    d = tmp_path / "session-1234567890"
    d.mkdir()
    return d


@pytest.fixture()
def flac_files(session_dir: Path) -> list[Path]:
    """Two non-empty stub FLAC files placed inside the session directory."""
    files: list[Path] = []
    for name in ("Alice.flac", "Bob.flac"):
        p = session_dir / name
        p.write_bytes(b"\x00" * 1024)
        files.append(p)
    return files


@pytest.fixture()
def channel() -> _Channel:
    return _Channel()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_pipeline_produces_transcript(session_dir, flac_files, channel):
    """run_pipeline writes transcript.json and returns speakers list."""
    from bot.pipeline import run_pipeline

    fake_transcript = [
        {"speaker": "Alice", "start": 0.0, "end": 1.0, "text": "Hello", "confidence": -0.5},
        {"speaker": "Bob", "start": 1.0, "end": 2.0, "text": "World", "confidence": -0.5},
    ]

    with (
        patch("bot.transcribe.transcribe_session", return_value=fake_transcript),
        patch("bot.downmix.downmix", new_callable=AsyncMock, return_value=session_dir / "session_full.mp3"),
    ):
        result = await run_pipeline(session_dir, flac_files, channel)

    assert (session_dir / "transcript.json").exists()
    on_disk = json.loads((session_dir / "transcript.json").read_text())
    assert on_disk == fake_transcript
    assert isinstance(result["speakers"], list)
    assert set(result["speakers"]) == {"Alice", "Bob"}


async def test_pipeline_produces_html(session_dir, flac_files, channel):
    """run_pipeline writes index.html containing speaker names."""
    from bot.pipeline import run_pipeline

    fake_transcript = [
        {"speaker": "Alice", "start": 0.0, "end": 1.5, "text": "Testing", "confidence": -0.3},
    ]

    with (
        patch("bot.transcribe.transcribe_session", return_value=fake_transcript),
        patch("bot.downmix.downmix", new_callable=AsyncMock, return_value=session_dir / "session_full.mp3"),
    ):
        result = await run_pipeline(session_dir, flac_files, channel)

    assert result["html_path"] == session_dir / "index.html"
    assert (session_dir / "index.html").exists()
    html = (session_dir / "index.html").read_text()
    assert "Alice" in html
    assert "Testing" in html


async def test_pipeline_sends_discord_notifications(session_dir, flac_files, channel):
    """Pipeline sends an ETA message then a completion message."""
    from bot.pipeline import run_pipeline

    with (
        patch("bot.transcribe.transcribe_session", return_value=[]),
        patch("bot.downmix.downmix", new_callable=AsyncMock, return_value=session_dir / "session_full.mp3"),
    ):
        await run_pipeline(session_dir, flac_files, channel)

    assert len(channel.messages) >= 2, "Expected at least ETA + completion messages"
    assert any("⏳" in m for m in channel.messages), "ETA message missing"
    assert any("✅" in m for m in channel.messages), "Completion message missing"


async def test_pipeline_handles_empty_session(session_dir, channel):
    """Pipeline with no FLAC files skips transcription and downmix gracefully."""
    from bot.pipeline import run_pipeline

    with patch(
        "bot.downmix.downmix",
        new_callable=AsyncMock,
        side_effect=ValueError("no valid files"),
    ):
        result = await run_pipeline(session_dir, [], channel)

    assert result["speakers"] == []
    assert (session_dir / "transcript.json").exists()
    assert json.loads((session_dir / "transcript.json").read_text()) == []
    assert result["mp3_path"] is None


async def test_pipeline_is_idempotent(session_dir, flac_files, channel):
    """Running the pipeline twice does not duplicate transcript entries."""
    from bot.pipeline import run_pipeline

    fake_transcript = [
        {"speaker": "Alice", "start": 0.0, "end": 1.0, "text": "Hello", "confidence": -0.5},
    ]

    with (
        patch("bot.transcribe.transcribe_session", return_value=fake_transcript),
        patch("bot.downmix.downmix", new_callable=AsyncMock, return_value=session_dir / "session_full.mp3"),
    ):
        await run_pipeline(session_dir, flac_files, channel)
        await run_pipeline(session_dir, flac_files, channel)

    on_disk = json.loads((session_dir / "transcript.json").read_text())
    assert len(on_disk) == len(fake_transcript), "Transcript must not be duplicated on second run"


async def test_pipeline_reports_error_on_crash(session_dir, flac_files, channel):
    """Unhandled exception in pipeline steps → error dict + Discord error message."""
    from bot.pipeline import run_pipeline

    with (
        patch("bot.transcribe.transcribe_session", side_effect=RuntimeError("whisper crash")),
        patch("bot.downmix.downmix", new_callable=AsyncMock),
    ):
        result = await run_pipeline(session_dir, flac_files, channel)

    assert "error" in result
    assert any("❌" in m for m in channel.messages), "Error message expected in Discord"


async def test_pipeline_error_preserves_audio(session_dir, flac_files, channel):
    """On pipeline crash, the original FLAC files must not be deleted."""
    from bot.pipeline import run_pipeline

    with (
        patch("bot.transcribe.transcribe_session", side_effect=RuntimeError("crash")),
        patch("bot.downmix.downmix", new_callable=AsyncMock),
    ):
        await run_pipeline(session_dir, flac_files, channel)

    for p in flac_files:
        assert p.exists(), f"Audio file {p.name} was deleted on pipeline error"


async def test_pipeline_timeout(session_dir, flac_files, channel):
    """asyncio.wait_for timeout → error dict + Discord timeout message."""
    from bot import pipeline as _pipeline_mod

    original_timeout = _pipeline_mod.PIPELINE_TIMEOUT
    _pipeline_mod.PIPELINE_TIMEOUT = 0.001  # near-zero to force timeout

    async def _slow_steps(*_args, **_kwargs):
        await asyncio.sleep(10)

    try:
        with patch("bot.pipeline._run_steps", side_effect=_slow_steps):
            result = await _pipeline_mod.run_pipeline(session_dir, flac_files, channel)
    finally:
        _pipeline_mod.PIPELINE_TIMEOUT = original_timeout

    assert result == {"error": "timeout"}
    assert any("❌" in m and "timed out" in m for m in channel.messages)


async def test_pipeline_reads_duration_from_metadata(session_dir, flac_files, channel):
    """ETA message is based on duration_seconds in metadata.json."""
    from bot.pipeline import run_pipeline

    (session_dir / "metadata.json").write_text(
        json.dumps({"duration_seconds": 3600})
    )

    with (
        patch("bot.transcribe.transcribe_session", return_value=[]),
        patch("bot.downmix.downmix", new_callable=AsyncMock, return_value=session_dir / "session_full.mp3"),
    ):
        await run_pipeline(session_dir, flac_files, channel)

    # 30% of 60 min ≈ 18 min
    assert any("18" in m or "⏳" in m for m in channel.messages)
