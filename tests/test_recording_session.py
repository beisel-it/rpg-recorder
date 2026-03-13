"""Tests for RecordingSession — start/stop/watchdog/health/metadata."""
import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.recorder import RecordingSession, ChunkedFileSink


def _make_channel(name: str = "test-channel") -> MagicMock:
    ch = MagicMock()
    ch.name = name
    return ch


def _make_vc(connected: bool = True) -> MagicMock:
    vc = MagicMock()
    vc.is_connected.return_value = connected
    vc.listen = MagicMock()
    vc.stop_listening = MagicMock()
    vc.disconnect = AsyncMock()
    return vc


class TestRecordingSessionInit:
    def test_session_dir_created(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        assert session.session_dir.exists()

    def test_sink_is_chunked(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        assert isinstance(session.sink, ChunkedFileSink)

    def test_not_active_before_start(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        assert session._active is False

    def test_duration_str_format(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        parts = session.duration_str().split(":")
        assert len(parts) == 3 and all(p.isdigit() for p in parts)


class TestRecordingSessionStart:
    @pytest.mark.asyncio
    async def test_start_connects_and_listens(self, tmp_path):
        ch = _make_channel()
        vc = _make_vc()
        ch.connect = AsyncMock(return_value=vc)
        with patch("bot.recorder.voice_recv"):
            session = RecordingSession(ch, tmp_path)
            await session.start()
        assert session._active is True
        vc.listen.assert_called_once_with(session.sink)
        # cleanup
        session._active = False
        for t in (session._watchdog_task, session._health_task):
            if t:
                t.cancel()
                await asyncio.gather(t, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_start_spawns_background_tasks(self, tmp_path):
        ch = _make_channel()
        ch.connect = AsyncMock(return_value=_make_vc())
        with patch("bot.recorder.voice_recv"):
            session = RecordingSession(ch, tmp_path)
            await session.start()
        assert session._watchdog_task is not None
        assert session._health_task is not None
        session._active = False
        session._watchdog_task.cancel()
        session._health_task.cancel()
        await asyncio.gather(session._watchdog_task, session._health_task, return_exceptions=True)


class TestRecordingSessionStop:
    @pytest.mark.asyncio
    async def test_stop_deactivates_and_disconnects(self, tmp_path):
        ch = _make_channel()
        vc = _make_vc()
        ch.connect = AsyncMock(return_value=vc)
        with patch("bot.recorder.voice_recv"):
            session = RecordingSession(ch, tmp_path)
            await session.start()
        with patch.object(session.sink, "finalize", new=AsyncMock(return_value=[])):
            await session.stop()
        assert session._active is False
        vc.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_writes_metadata(self, tmp_path):
        ch = _make_channel("lobby")
        ch.connect = AsyncMock(return_value=_make_vc())
        with patch("bot.recorder.voice_recv"):
            session = RecordingSession(ch, tmp_path)
            await session.start()
        with patch.object(session.sink, "finalize", new=AsyncMock(return_value=[])):
            await session.stop()
        meta = json.loads((session.session_dir / "metadata.json").read_text())
        assert meta["channel"] == "lobby"
        assert "duration_seconds" in meta

    @pytest.mark.asyncio
    async def test_stop_without_vc_does_not_crash(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        with patch.object(session.sink, "finalize", new=AsyncMock(return_value=[])):
            result = await session.stop()
        assert result == []

    @pytest.mark.asyncio
    async def test_stop_returns_flac_paths(self, tmp_path):
        ch = _make_channel()
        ch.connect = AsyncMock(return_value=_make_vc())
        fake_flac = tmp_path / "12345.flac"
        fake_flac.touch()
        with patch("bot.recorder.voice_recv"):
            session = RecordingSession(ch, tmp_path)
            await session.start()
        with patch.object(session.sink, "finalize", new=AsyncMock(return_value=[fake_flac])):
            result = await session.stop()
        assert fake_flac in result


class TestWriteMetadata:
    def test_metadata_fields(self, tmp_path):
        session = RecordingSession(_make_channel("general"), tmp_path)
        session._write_metadata([])
        meta = json.loads((session.session_dir / "metadata.json").read_text())
        assert meta["channel"] == "general"
        assert meta["flac_files"] == []
        assert meta["speakers"] == []

    def test_metadata_includes_flac_names(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        flac = session.session_dir / "99.flac"
        flac.touch()
        session._write_metadata([flac])
        meta = json.loads((session.session_dir / "metadata.json").read_text())
        assert "99.flac" in meta["flac_files"]


class TestWatchdog:
    @pytest.mark.asyncio
    async def test_watchdog_reconnects_on_disconnect(self, tmp_path):
        ch = _make_channel()
        vc_disconnected = _make_vc(connected=False)
        vc_reconnected = _make_vc(connected=True)
        ch.connect = AsyncMock(return_value=vc_reconnected)

        session = RecordingSession(ch, tmp_path)
        session.vc = vc_disconnected
        session._active = True
        session._WATCHDOG_INTERVAL = 0  # no waiting

        task = asyncio.create_task(session._watchdog())
        await asyncio.sleep(0.05)
        session._active = False
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

        ch.connect.assert_called()

    @pytest.mark.asyncio
    async def test_watchdog_skips_when_connected(self, tmp_path):
        ch = _make_channel()
        vc = _make_vc(connected=True)
        session = RecordingSession(ch, tmp_path)
        session.vc = vc
        session._active = True
        session._WATCHDOG_INTERVAL = 0

        call_count = 0
        orig_sleep = asyncio.sleep

        async def fake_sleep(s):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                session._active = False

        with patch("asyncio.sleep", new=fake_sleep):
            await session._watchdog()

        ch.connect.assert_not_called()


class TestHealthLoop:
    @pytest.mark.asyncio
    async def test_health_loop_runs_without_crash(self, tmp_path):
        session = RecordingSession(_make_channel(), tmp_path)
        session._active = True
        session._HEALTH_INTERVAL = 0

        sp = MagicMock()
        sp.username = "Alice"
        sp.total_bytes = 9600
        sp.last_audio_at = time.monotonic() - 10
        sp.chunk_paths = [Path("/tmp/chunk0.wav")]
        sp.kbpm = MagicMock(return_value=8.0)
        session.sink._speakers[1] = sp

        calls = 0

        async def fake_sleep(s):
            nonlocal calls
            calls += 1
            if calls >= 2:
                session._active = False

        with patch("asyncio.sleep", new=fake_sleep):
            await session._health_loop()

        assert calls >= 1
