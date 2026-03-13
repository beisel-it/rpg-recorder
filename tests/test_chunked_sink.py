"""
test_chunked_sink.py — Tests for ChunkedFileSink (RPGREC-002c).

Acceptance criteria (from RPGREC-002c):
  - write() creates per-speaker WAV chunks ≤ 5 min
  - New chunk file opened when CHUNK_BYTES is exceeded
  - cleanup() closes all open wave files
  - health() returns per-speaker stats dict
  - finalize() produces FLAC output via ffmpeg
"""

import pytest
from unittest.mock import patch


def test_chunked_sink_creates_chunk_on_first_write(tmp_session_dir, fake_audio):
    from bot.recorder import ChunkedFileSink
    from tests.mocks.discord_mocks import MockUser, MockVoiceData

    sink = ChunkedFileSink(tmp_session_dir / "chunks")
    user = MockUser(user_id=1001, name="Alice")
    sink.write(user, MockVoiceData(pcm=fake_audio(duration=1)))
    sink.cleanup()

    chunks = list((tmp_session_dir / "chunks").glob("*.wav"))
    assert len(chunks) == 1


def test_chunked_sink_rolls_over_at_chunk_limit(tmp_session_dir, fake_audio):
    """ChunkedFileSink opens a new file after CHUNK_BYTES are written."""
    from bot.recorder import ChunkedFileSink
    from tests.mocks.discord_mocks import MockUser, MockVoiceData

    small_chunk_bytes = 1000

    with patch("bot.recorder.CHUNK_BYTES", small_chunk_bytes):
        sink = ChunkedFileSink(tmp_session_dir / "chunks")
        user = MockUser(user_id=1001, name="Alice")
        # First write fills chunk 0 past the limit
        sink.write(user, MockVoiceData(pcm=fake_audio(duration=1)))
        # Second write triggers rollover to chunk 1
        sink.write(user, MockVoiceData(pcm=fake_audio(duration=1)))
        sink.cleanup()

    chunks = list((tmp_session_dir / "chunks").glob("*.wav"))
    assert len(chunks) >= 2


def test_chunked_sink_health_returns_stats(tmp_session_dir, fake_audio):
    from bot.recorder import ChunkedFileSink
    from tests.mocks.discord_mocks import MockUser, MockVoiceData

    sink = ChunkedFileSink(tmp_session_dir / "chunks")
    user = MockUser(user_id=1001, name="Alice")
    sink.write(user, MockVoiceData(pcm=fake_audio(duration=2)))
    sink.cleanup()

    stats = sink.health()
    assert "Alice" in stats
    alice = stats["Alice"]
    assert alice["total_bytes"] > 0
    assert alice["chunks"] == 1
    assert alice["silent_secs"] >= 0
    assert alice["kbpm"] > 0


async def test_chunked_sink_finalize_produces_flac(tmp_session_dir, fake_audio):
    """finalize() calls ffmpeg and returns FLAC paths.  ffmpeg is mocked — no binary needed."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from bot.recorder import ChunkedFileSink
    from tests.mocks.discord_mocks import MockUser, MockVoiceData

    sink = ChunkedFileSink(tmp_session_dir / "chunks")
    user = MockUser(user_id=1001, name="Alice")
    sink.write(user, MockVoiceData(pcm=fake_audio(duration=5, channels=2)))
    sink.cleanup()

    # Mock asyncio.create_subprocess_exec so ffmpeg is never invoked
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)):
        # finalize() creates the flac path but doesn't actually write audio bytes;
        # we create a stub file so the existence check passes
        async def patched_finalize(out_dir):
            # call real finalize — ffmpeg is mocked, so returncode=0
            # but ffmpeg never writes the file; create a stub so results is non-empty
            result = await original_finalize(out_dir)
            for p in result:
                p.touch()
            return result

        original_finalize = sink.finalize
        flac_paths = await original_finalize(tmp_session_dir)

    # ffmpeg mock returns rc=0, so results list is populated
    assert len(flac_paths) == 1
    assert flac_paths[0].suffix == ".flac"
