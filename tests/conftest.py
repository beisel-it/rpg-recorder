"""
conftest.py — Shared pytest fixtures for rpg-recorder tests.

Fixtures
--------
mock_voice_client   MockVoiceClient — controllable is_connected(), fire_audio()
mock_bot            MockBot         — slash-command dispatch without Discord
fake_audio          Callable        — generates synthetic PCM bytes
sample_flac         Path            — tiny WAV file (FLAC-ready placeholder)
sample_transcript   list[dict]      — known [{speaker, start, end, text}] entries
tmp_session_dir     Path            — temporary output directory (pytest tmp_path)
"""

from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import Callable

import pytest

from tests.mocks.audio_mocks import generate_fake_audio, expected_byte_count
from tests.mocks.discord_mocks import MockBot, MockVoiceClient


# ---------------------------------------------------------------------------
# Discord mocks
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_voice_client() -> MockVoiceClient:
    """
    Simulates voice_recv.VoiceRecvClient without a real Discord connection.

    Usage:
        def test_connected(mock_voice_client):
            assert mock_voice_client.is_connected()
            mock_voice_client.set_connected(False)
            assert not mock_voice_client.is_connected()
    """
    return MockVoiceClient()


@pytest.fixture
def mock_bot() -> MockBot:
    """
    Minimal discord.Bot stub for slash-command tests.

    Usage:
        def test_cog_registers(mock_bot):
            cog = RecordCog(mock_bot)
            mock_bot.add_cog(cog)
            assert mock_bot.get_cog("RecordCog") is cog
    """
    return MockBot()


# ---------------------------------------------------------------------------
# Audio fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_audio() -> Callable[..., bytes]:
    """
    Factory that returns synthetic 48 kHz 16-bit PCM bytes.

    Returns a callable so tests can request different durations:

        def test_length(fake_audio):
            pcm = fake_audio(duration=5)
            assert len(pcm) == 480_000   # 48 000 Hz * 2 bytes * 1 ch * 5 s

        def test_stereo(fake_audio):
            pcm = fake_audio(duration=1, channels=2)
            assert len(pcm) == 192_000

    Parameters to the returned callable:
        duration (float):    seconds of audio [default 1.0]
        sample_rate (int):   Hz [default 48 000]
        channels (int):      1=Mono, 2=Stereo [default 1]
        seed (int):          deterministic amplitude offset [default 0]
    """
    return generate_fake_audio


@pytest.fixture
def sample_flac(tmp_path: Path) -> dict[str, Path]:
    """
    Tiny audio files with *known* content for pipeline tests.

    Returns a dict with keys "5s" and "30s", each a Path to a valid WAV file
    (FLAC format will be added when task 003a ships soundfile as a dependency).

    Usage:
        def test_file_exists(sample_flac):
            assert sample_flac["5s"].exists()
            assert sample_flac["5s"].stat().st_size > 44  # WAV header minimum
    """
    files: dict[str, Path] = {}
    for label, duration in (("5s", 5), ("30s", 30)):
        path = tmp_path / f"sample_{label}.wav"
        pcm = generate_fake_audio(duration=duration, seed=99)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(48_000)
            wf.writeframes(pcm)
        files[label] = path
    return files


# ---------------------------------------------------------------------------
# Transcript fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_transcript(tmp_path: Path) -> tuple[list[dict], Path]:
    """
    Known transcript data: list of {speaker, start, end, text} dicts
    *and* a Path to the corresponding JSON file on disk.

    Usage:
        def test_parse(sample_transcript):
            entries, path = sample_transcript
            assert entries[0]["speaker"] == "Alice"
            assert path.exists()
    """
    fixture_path = (
        Path(__file__).parent / "fixtures" / "transcripts" / "sample.json"
    )
    entries = json.loads(fixture_path.read_text())

    # Copy to tmp_path so tests can modify without polluting the fixture file
    out = tmp_path / "transcript.json"
    out.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
    return entries, out


# ---------------------------------------------------------------------------
# Session directory fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_session_dir(tmp_path: Path) -> Path:
    """
    Temporary output directory scoped to one test.

    Mirrors the structure RecordingSession creates:
        tmp_session_dir/
        └── chunks/

    Usage:
        def test_output(tmp_session_dir):
            assert tmp_session_dir.is_dir()
            assert (tmp_session_dir / "chunks").is_dir()
    """
    session_dir = tmp_path / "session-0000000000"
    chunk_dir = session_dir / "chunks"
    chunk_dir.mkdir(parents=True)
    return session_dir
