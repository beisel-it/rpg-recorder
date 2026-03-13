"""
test_voice_capture.py — Tests for RawPCMSink and VoiceCaptureSession (RPGREC-002b).

Acceptance criteria (from RPGREC-002b):
  - Bot can join a voice channel (via code call, no slash command)
  - VoiceRecvClient is configured as the voice client class
  - Audio received per user (PCM data in callback)
  - Simple test sink: writes raw PCM to one file per user
  - Multi-user: ≥2 simultaneous speakers → separate files
  - Speaker detection: log output for who is speaking

Unit tests use mock_voice_client fixture to avoid real Discord connections.
Integration tests (requiring live Discord) are marked @pytest.mark.integration
and auto-skipped in CI.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.mocks.discord_mocks import MockUser, MockVoiceData, MockVoiceChannel, MockVoiceClient


# ---------------------------------------------------------------------------
# RawPCMSink unit tests
# ---------------------------------------------------------------------------


class TestRawPCMSink:
    """Unit tests for the per-speaker PCM file sink."""

    def test_creates_output_dir(self, tmp_path: Path) -> None:
        """RawPCMSink creates its output directory if it doesn't exist."""
        from bot.voice_capture import RawPCMSink

        out_dir = tmp_path / "new_subdir" / "audio"
        sink = RawPCMSink(out_dir)
        assert out_dir.is_dir()
        sink.cleanup()

    def test_write_none_user_ignored(self, tmp_path: Path, fake_audio) -> None:
        """write() with user=None must be a no-op (no crash, no files)."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        sink.write(None, MockVoiceData(pcm=fake_audio(duration=1)))
        sink.cleanup()

        assert sink.speaker_count() == 0
        assert sink.output_files() == []

    def test_write_single_speaker_creates_pcm_file(self, tmp_path: Path, fake_audio) -> None:
        """A single speaker's audio is written to a .pcm file."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        user = MockUser(user_id=1001, name="Alice")
        pcm = fake_audio(duration=1)
        sink.write(user, MockVoiceData(pcm=pcm))
        sink.cleanup()

        pcm_files = list(tmp_path.glob("*.pcm"))
        assert len(pcm_files) == 1
        assert pcm_files[0].name == "1001.pcm"

    def test_write_appends_multiple_chunks_for_same_user(self, tmp_path: Path, fake_audio) -> None:
        """Multiple write() calls for the same user accumulate in one file."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        user = MockUser(user_id=2001, name="Bob")
        pcm = fake_audio(duration=1)

        # Write three chunks
        for _ in range(3):
            sink.write(user, MockVoiceData(pcm=pcm))
        sink.cleanup()

        pcm_file = tmp_path / "2001.pcm"
        assert pcm_file.exists()
        assert pcm_file.stat().st_size == len(pcm) * 3

    def test_write_two_simultaneous_speakers_separate_files(
        self, tmp_path: Path, fake_audio
    ) -> None:
        """≥2 speakers each produce a separate .pcm file (DoD: Multi-User)."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        alice = MockUser(user_id=1001, name="Alice")
        bob = MockUser(user_id=2002, name="Bob")

        # Interleave audio from both speakers
        for _ in range(3):
            sink.write(alice, MockVoiceData(pcm=fake_audio(duration=1, seed=1)))
            sink.write(bob, MockVoiceData(pcm=fake_audio(duration=1, seed=2)))

        sink.cleanup()

        assert (tmp_path / "1001.pcm").exists()
        assert (tmp_path / "2002.pcm").exists()
        assert sink.speaker_count() == 2

    def test_speaker_count_tracks_distinct_users(self, tmp_path: Path, fake_audio) -> None:
        """speaker_count() returns the number of distinct users seen."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        for uid in (1001, 2002, 3003):
            user = MockUser(user_id=uid, name=f"User{uid}")
            sink.write(user, MockVoiceData(pcm=fake_audio(duration=1)))

        assert sink.speaker_count() == 3
        sink.cleanup()

    def test_speakers_property_returns_id_name_mapping(self, tmp_path: Path, fake_audio) -> None:
        """speakers property returns {user_id: display_name} for all seen speakers."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        alice = MockUser(user_id=1001, name="Alice")
        bob = MockUser(user_id=2002, name="Bob")
        sink.write(alice, MockVoiceData(pcm=fake_audio()))
        sink.write(bob, MockVoiceData(pcm=fake_audio()))
        sink.cleanup()

        speakers = sink.speakers
        assert speakers == {1001: "Alice", 2002: "Bob"}

    def test_speakers_property_uses_display_name(self, tmp_path: Path, fake_audio) -> None:
        """display_name takes precedence over name in speaker detection."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        # MockUser sets both name and display_name to the same value by default
        user = MockUser(user_id=5005, name="RealName")
        user.display_name = "DisplayAlias"
        sink.write(user, MockVoiceData(pcm=fake_audio()))
        sink.cleanup()

        assert sink.speakers[5005] == "DisplayAlias"

    def test_output_files_returns_all_paths(self, tmp_path: Path, fake_audio) -> None:
        """output_files() returns a path for each speaker seen."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        for uid in (1001, 2002):
            user = MockUser(user_id=uid)
            sink.write(user, MockVoiceData(pcm=fake_audio()))
        sink.cleanup()

        paths = sink.output_files()
        names = {p.name for p in paths}
        assert names == {"1001.pcm", "2002.pcm"}

    def test_cleanup_closes_all_handles(self, tmp_path: Path, fake_audio) -> None:
        """cleanup() closes open file handles without error."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        alice = MockUser(user_id=1001, name="Alice")
        sink.write(alice, MockVoiceData(pcm=fake_audio()))

        # Should not raise
        sink.cleanup()

        # After cleanup, _handles is empty (closed & cleared)
        assert len(sink._handles) == 0

    def test_cleanup_is_idempotent(self, tmp_path: Path, fake_audio) -> None:
        """Calling cleanup() twice must not raise."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        alice = MockUser(user_id=1001)
        sink.write(alice, MockVoiceData(pcm=fake_audio()))
        sink.cleanup()
        sink.cleanup()  # second call must be harmless

    def test_wants_opus_is_false(self, tmp_path: Path) -> None:
        """RawPCMSink must request decoded PCM (wants_opus=False)."""
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        assert sink.wants_opus is False
        sink.cleanup()

    def test_speaker_detection_logged(self, tmp_path: Path, fake_audio, caplog) -> None:
        """Speaker detection must produce a log entry (DoD: Speaker-Detection)."""
        import logging
        from bot.voice_capture import RawPCMSink

        sink = RawPCMSink(tmp_path)
        user = MockUser(user_id=7777, name="Charlie")

        with caplog.at_level(logging.INFO, logger="bot.voice_capture"):
            sink.write(user, MockVoiceData(pcm=fake_audio()))

        assert any("Charlie" in rec.message for rec in caplog.records)
        assert any("7777" in rec.message for rec in caplog.records)
        sink.cleanup()


# ---------------------------------------------------------------------------
# VoiceCaptureSession unit tests
# ---------------------------------------------------------------------------


class TestVoiceCaptureSession:
    """Unit tests for VoiceCaptureSession (joins channel, captures PCM)."""

    async def test_start_connects_with_voice_recv_client(self, tmp_path: Path) -> None:
        """start() must call channel.connect(cls=VoiceRecvClient) — DoD: VoiceRecvClient."""
        from bot.voice_capture import VoiceCaptureSession
        from discord.ext import voice_recv

        channel = MockVoiceChannel(name="game-table")
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        assert channel.last_connect_cls is voice_recv.VoiceRecvClient

        await session.stop()

    async def test_start_registers_sink_as_listener(self, tmp_path: Path) -> None:
        """After start(), the voice client's sink is our RawPCMSink."""
        from bot.voice_capture import VoiceCaptureSession, RawPCMSink

        channel = MockVoiceChannel(name="game-table")
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        assert channel._vc._sink is session.sink
        assert isinstance(session.sink, RawPCMSink)

        await session.stop()

    async def test_start_logs_dave_handshake(self, tmp_path: Path, caplog) -> None:
        """start() logs a message indicating DAVE handshake completion."""
        import logging
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel(name="game-table")
        session = VoiceCaptureSession(channel, tmp_path)

        with caplog.at_level(logging.INFO, logger="bot.voice_capture"):
            await session.start()

        assert any("DAVE" in rec.message for rec in caplog.records)
        await session.stop()

    async def test_stop_without_start_is_safe(self, tmp_path: Path) -> None:
        """stop() must not raise even when start() was never called."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        # No start() call — must be safe
        files = await session.stop()
        assert files == []

    async def test_stop_returns_pcm_files_for_active_speakers(
        self, tmp_path: Path, fake_audio
    ) -> None:
        """stop() returns paths to non-empty .pcm files for each speaker."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        # Simulate audio from two users via the voice client
        vc = channel._vc
        alice = MockUser(user_id=1001, name="Alice")
        bob = MockUser(user_id=2002, name="Bob")
        vc.fire_audio(alice, fake_audio(duration=1, channels=2))
        vc.fire_audio(bob, fake_audio(duration=1, channels=2))
        # Fire a second chunk for Alice to ensure appending works
        vc.fire_audio(alice, fake_audio(duration=1, channels=2))

        files = await session.stop()

        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"1001.pcm", "2002.pcm"}
        # Both files must have non-zero content
        for f in files:
            assert f.stat().st_size > 0

    async def test_stop_excludes_empty_pcm_files(self, tmp_path: Path, fake_audio) -> None:
        """stop() only returns files with actual content (size > 0)."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        # Write an empty-data chunk (zero-length bytes) — should not appear in output
        vc = channel._vc
        user = MockUser(user_id=9999, name="Ghost")
        vc.fire_audio(user, b"")  # zero bytes

        files = await session.stop()
        # The file is created but its size is 0 → excluded from result
        assert all(f.stat().st_size > 0 for f in files)

    async def test_stop_logs_captured_speakers(
        self, tmp_path: Path, fake_audio, caplog
    ) -> None:
        """stop() logs which speakers were captured (DoD: Speaker-Detection)."""
        import logging
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        vc = channel._vc
        alice = MockUser(user_id=1001, name="Alice")
        vc.fire_audio(alice, fake_audio(duration=1))

        with caplog.at_level(logging.INFO, logger="bot.voice_capture"):
            await session.stop()

        assert any("Alice" in rec.message for rec in caplog.records)

    async def test_stop_calls_stop_listening_and_disconnect(self, tmp_path: Path) -> None:
        """stop() calls stop_listening() and disconnect(force=True) on the vc."""
        from bot.voice_capture import VoiceCaptureSession
        from unittest.mock import AsyncMock, MagicMock

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        # Wrap the voice client methods for inspection
        vc = channel._vc
        original_stop = vc.stop_listening
        original_disconnect = vc.disconnect

        stop_called = []
        disconnect_called = []

        def mock_stop():
            stop_called.append(True)
            original_stop()

        async def mock_disconnect(**kwargs):
            disconnect_called.append(kwargs)
            await original_disconnect(**kwargs)

        vc.stop_listening = mock_stop
        vc.disconnect = mock_disconnect

        await session.stop()

        assert len(stop_called) == 1
        assert len(disconnect_called) == 1
        assert disconnect_called[0].get("force") is True

    async def test_multi_user_audio_in_separate_files(
        self, tmp_path: Path, fake_audio
    ) -> None:
        """DoD: ≥2 simultaneous speakers produce separate files with distinct content."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        vc = channel._vc
        users = [
            MockUser(user_id=1001, name="Player1"),
            MockUser(user_id=2002, name="Player2"),
            MockUser(user_id=3003, name="Player3"),
        ]

        # Each user speaks with a unique seed so content is distinguishable
        for seed, user in enumerate(users):
            for _ in range(5):
                vc.fire_audio(user, fake_audio(duration=1, seed=seed * 10))

        files = await session.stop()

        assert len(files) == 3
        # All three files must have unique content
        contents = [f.read_bytes() for f in sorted(files)]
        assert len(set(contents)) == 3  # all distinct

    async def test_stop_handles_stop_listening_exception(self, tmp_path: Path) -> None:
        """stop() must not raise if stop_listening() throws (e.g. already disconnected)."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        # Make stop_listening() raise to exercise the except branch
        def boom():
            raise RuntimeError("already stopped")

        channel._vc.stop_listening = boom

        # Must not propagate the exception
        files = await session.stop()
        assert isinstance(files, list)

    async def test_stop_handles_disconnect_exception(self, tmp_path: Path) -> None:
        """stop() must not raise if disconnect() throws (e.g. network error)."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        async def boom(**kwargs):
            raise OSError("network gone")

        channel._vc.disconnect = boom

        # Must not propagate the exception
        files = await session.stop()
        assert isinstance(files, list)

    async def test_user_leaves_during_capture_no_crash(
        self, tmp_path: Path, fake_audio
    ) -> None:
        """DoD: User joining/leaving during recording must not crash; other audio intact."""
        from bot.voice_capture import VoiceCaptureSession

        channel = MockVoiceChannel()
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        vc = channel._vc
        alice = MockUser(user_id=1001, name="Alice")
        bob = MockUser(user_id=2002, name="Bob")

        # Alice speaks
        vc.fire_audio(alice, fake_audio(duration=2, seed=1))

        # Bob speaks (arrives mid-session)
        vc.fire_audio(bob, fake_audio(duration=1, seed=2))

        # Bob "leaves" — no more audio from him, but Alice continues
        vc.fire_audio(alice, fake_audio(duration=2, seed=1))

        files = await session.stop()

        # Both should have data — no crash
        assert len(files) == 2
        alice_file = next(f for f in files if f.name == "1001.pcm")
        assert alice_file.stat().st_size > 0


# ---------------------------------------------------------------------------
# Integration test (real Discord — skipped in CI)
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_integration_join_and_capture_real_discord(tmp_path: Path) -> None:
    """
    Integration test: bot joins a real voice channel and receives PCM audio.

    Requires:
        DISCORD_TOKEN env var
        INTEGRATION_GUILD_ID env var
        INTEGRATION_VOICE_CHANNEL_ID env var

    Run with:
        pytest -m integration
    """
    import os
    import asyncio
    import discord
    from discord.ext import commands, voice_recv
    from bot.voice_capture import VoiceCaptureSession

    token = os.environ.get("DISCORD_TOKEN", "")
    guild_id = int(os.environ.get("INTEGRATION_GUILD_ID", "0"))
    channel_id = int(os.environ.get("INTEGRATION_VOICE_CHANNEL_ID", "0"))

    if not token or not guild_id or not channel_id:
        pytest.skip("Integration env vars not set")

    intents = discord.Intents.default()
    intents.voice_states = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    captured_files: list[Path] = []

    @bot.event
    async def on_ready():
        guild = bot.get_guild(guild_id)
        assert guild is not None, "Guild not found"
        channel = guild.get_channel(channel_id)
        assert channel is not None, "Voice channel not found"
        assert isinstance(channel, discord.VoiceChannel)

        # Connect using VoiceRecvClient (DAVE handshake happens here)
        session = VoiceCaptureSession(channel, tmp_path)
        await session.start()

        # Record for 5 seconds to collect any ambient audio
        await asyncio.sleep(5)

        files = await session.stop()
        captured_files.extend(files)
        await bot.close()

    await asyncio.wait_for(bot.start(token), timeout=30)

    # After 5s of silence, there may be no files — the important thing is no error
    # DAVE handshake success is implicit (no DiscordException with code 4017)
