"""
test_chunked_sink.py — Tests for ChunkedFileSink (RPGREC-002c).

All tests are skipped until RPGREC-002c is merged.  The fixture usage below
serves as a template for the real test implementation.

Acceptance criteria (from RPGREC-002c):
  - write() creates per-speaker WAV chunks ≤ 5 min
  - New chunk file opened when CHUNK_BYTES is exceeded
  - cleanup() closes all open wave files
  - health() returns per-speaker stats dict
  - finalize() produces FLAC output via ffmpeg
"""

import pytest


@pytest.mark.skip(reason="waiting for RPGREC-002c implementation")
def test_chunked_sink_creates_chunk_on_first_write(tmp_session_dir, fake_audio):
    from bot.recorder import ChunkedFileSink
    from tests.mocks.discord_mocks import MockUser

    sink = ChunkedFileSink(tmp_session_dir / "chunks")
    user = MockUser(user_id=1001, name="Alice")
    sink.write(user, type("VD", (), {"pcm": fake_audio(duration=1)})())
    sink.cleanup()

    chunks = list((tmp_session_dir / "chunks").glob("*.wav"))
    assert len(chunks) == 1


@pytest.mark.skip(reason="waiting for RPGREC-002c implementation")
def test_chunked_sink_rolls_over_at_chunk_limit(tmp_session_dir, fake_audio):
    """ChunkedFileSink opens a new file after CHUNK_BYTES are written."""
    pass


@pytest.mark.skip(reason="waiting for RPGREC-002c implementation")
def test_chunked_sink_health_returns_stats(tmp_session_dir, fake_audio):
    pass


@pytest.mark.skip(reason="waiting for RPGREC-002c implementation")
async def test_chunked_sink_finalize_produces_flac(tmp_session_dir, fake_audio):
    pass
