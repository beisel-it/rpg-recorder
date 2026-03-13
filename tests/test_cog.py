"""Tests for RecordCog — /record start, stop, status + _has_permission."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.cog import RecordCog, _has_permission


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_member(roles: list[str] | None = None) -> MagicMock:
    m = MagicMock()
    m.roles = []
    for r in (roles or []):
        role = MagicMock()
        role.name = r
        m.roles.append(role)
    return m


def _make_interaction(guild_id: int = 1, member=None, in_voice: bool = True) -> MagicMock:
    ix = MagicMock()
    ix.guild_id = guild_id
    ix.user = MagicMock(id=42)
    ix.guild = MagicMock()
    ix.guild.get_member.return_value = member or _make_member(["Recorder"])
    ix.response = MagicMock()
    ix.response.defer = AsyncMock()
    ix.response.send_message = AsyncMock()
    ix.followup = MagicMock()
    ix.followup.send = AsyncMock()

    if in_voice:
        vc_chan = MagicMock()
        vc_chan.name = "general"
        ix.guild.get_member.return_value.voice = MagicMock(channel=vc_chan)
    else:
        ix.guild.get_member.return_value.voice = None

    return ix


def _make_cog() -> RecordCog:
    bot = MagicMock()
    return RecordCog(bot)


# ---------------------------------------------------------------------------
# _has_permission
# ---------------------------------------------------------------------------

class TestHasPermission:
    def test_no_role_required_allows_all(self):
        assert _has_permission(_make_member(), role_name=None) is True

    def test_member_with_required_role(self):
        m = _make_member(["Recorder"])
        assert _has_permission(m, role_name="Recorder") is True

    def test_member_without_required_role(self):
        m = _make_member(["Guest"])
        assert _has_permission(m, role_name="Recorder") is False

    def test_member_with_multiple_roles(self):
        m = _make_member(["Guest", "Recorder", "Admin"])
        assert _has_permission(m, role_name="Recorder") is True


# ---------------------------------------------------------------------------
# /record start
# ---------------------------------------------------------------------------

class TestRecordStart:
    @pytest.mark.asyncio
    async def test_start_no_voice_channel(self):
        cog = _make_cog()
        ix = _make_interaction(in_voice=False)
        await cog.record_start.callback(cog, ix)
        ix.followup.send.assert_called_once()
        assert "voice channel" in ix.followup.send.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_start_already_recording(self):
        cog = _make_cog()
        cog._sessions[1] = MagicMock()  # existing session
        ix = _make_interaction(guild_id=1)
        await cog.record_start.callback(cog, ix)
        msg = ix.followup.send.call_args[0][0]
        assert "already running" in msg or "already" in msg.lower()

    @pytest.mark.asyncio
    async def test_start_no_permission(self):
        cog = _make_cog()
        ix = _make_interaction()
        ix.guild.get_member.return_value = _make_member(["Guest"])

        with patch("bot.cog.RECORDER_ROLE_NAME", "Recorder"):
            await cog.record_start.callback(cog, ix)

        msg = ix.followup.send.call_args[0][0]
        assert "permission" in msg.lower()

    @pytest.mark.asyncio
    async def test_start_success_adds_session(self):
        cog = _make_cog()
        ix = _make_interaction(guild_id=99)

        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.session_dir = MagicMock(name="session-123")
        mock_session.session_dir.name = "session-123"

        with patch("bot.cog.RecordingSession", return_value=mock_session):
            await cog.record_start.callback(cog, ix)

        assert 99 in cog._sessions
        ix.followup.send.assert_called_once()
        assert "started" in ix.followup.send.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_start_passes_notify_channel(self):
        """RecordingSession must be constructed with notify_channel=interaction.channel."""
        cog = _make_cog()
        ix = _make_interaction(guild_id=77)
        # interaction.channel is a MagicMock attribute on ix
        expected_channel = ix.channel

        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.session_dir = MagicMock()
        mock_session.session_dir.name = "session-77"

        with patch("bot.cog.RecordingSession", return_value=mock_session) as mock_cls:
            await cog.record_start.callback(cog, ix)

        _, kwargs = mock_cls.call_args
        assert kwargs.get("notify_channel") is expected_channel

    @pytest.mark.asyncio
    async def test_start_session_exception_sends_error(self):
        cog = _make_cog()
        ix = _make_interaction()

        mock_session = MagicMock()
        mock_session.start = AsyncMock(side_effect=RuntimeError("connect failed"))

        with patch("bot.cog.RecordingSession", return_value=mock_session):
            await cog.record_start.callback(cog, ix)

        msg = ix.followup.send.call_args[0][0]
        assert "could not" in msg.lower() or "❌" in msg


# ---------------------------------------------------------------------------
# /record stop
# ---------------------------------------------------------------------------

class TestRecordStop:
    @pytest.mark.asyncio
    async def test_stop_no_active_session(self):
        cog = _make_cog()
        ix = _make_interaction(guild_id=1)
        await cog.record_stop.callback(cog, ix)
        msg = ix.followup.send.call_args[0][0]
        assert "no recording" in msg.lower()

    @pytest.mark.asyncio
    async def test_stop_no_permission(self):
        cog = _make_cog()
        cog._sessions[1] = MagicMock()
        ix = _make_interaction(guild_id=1)
        ix.guild.get_member.return_value = _make_member(["Guest"])

        with patch("bot.cog.RECORDER_ROLE_NAME", "Recorder"):
            await cog.record_stop.callback(cog, ix)

        msg = ix.followup.send.call_args[0][0]
        assert "permission" in msg.lower()

    @pytest.mark.asyncio
    async def test_stop_success_with_flac_files(self):
        cog = _make_cog()
        fake_flac = MagicMock()
        fake_flac.name = "42.flac"

        session = MagicMock()
        session.stop = AsyncMock(return_value=[fake_flac])
        session.duration_str.return_value = "00:05:00"
        session.session_dir.name = "session-999"
        cog._sessions[1] = session

        ix = _make_interaction(guild_id=1)
        await cog.record_stop.callback(cog, ix)

        assert 1 not in cog._sessions  # session removed
        calls = [c[0][0] for c in ix.followup.send.call_args_list]
        final_msg = " ".join(calls)
        assert "complete" in final_msg.lower() or "✅" in final_msg

    @pytest.mark.asyncio
    async def test_stop_no_audio_warns(self):
        cog = _make_cog()
        session = MagicMock()
        session.stop = AsyncMock(return_value=[])
        session.duration_str.return_value = "00:00:10"
        session.session_dir.name = "session-000"
        cog._sessions[1] = session

        ix = _make_interaction(guild_id=1)
        await cog.record_stop.callback(cog, ix)

        calls = " ".join(c[0][0] for c in ix.followup.send.call_args_list)
        assert "no audio" in calls.lower() or "⚠️" in calls

    @pytest.mark.asyncio
    async def test_stop_exception_sends_error(self):
        cog = _make_cog()
        session = MagicMock()
        session.stop = AsyncMock(side_effect=RuntimeError("ffmpeg died"))
        session.duration_str.return_value = "00:01:00"
        session.session_dir.name = "session-err"
        cog._sessions[1] = session

        ix = _make_interaction(guild_id=1)
        await cog.record_stop.callback(cog, ix)

        calls = " ".join(c[0][0] for c in ix.followup.send.call_args_list)
        assert "error" in calls.lower() or "❌" in calls


# ---------------------------------------------------------------------------
# /record status
# ---------------------------------------------------------------------------

class TestRecordStatus:
    @pytest.mark.asyncio
    async def test_status_no_session(self):
        cog = _make_cog()
        ix = _make_interaction(guild_id=1)
        await cog.record_status.callback(cog, ix)
        ix.response.send_message.assert_called_once()
        msg = ix.response.send_message.call_args[0][0]
        assert "no recording" in msg.lower()

    @pytest.mark.asyncio
    async def test_status_active_with_speakers(self):
        cog = _make_cog()
        session = MagicMock()
        session.duration_str.return_value = "00:10:00"
        session.session_dir.name = "session-live"
        session.channel.name = "general"
        session.sink.health.return_value = {
            "Alice": {"kbpm": 12.3, "chunks": 2, "silent_secs": 5}
        }
        cog._sessions[1] = session

        ix = _make_interaction(guild_id=1)
        await cog.record_status.callback(cog, ix)

        msg = ix.response.send_message.call_args[0][0]
        assert "Alice" in msg
        assert "12.3" in msg

    @pytest.mark.asyncio
    async def test_status_active_no_speakers_yet(self):
        cog = _make_cog()
        session = MagicMock()
        session.duration_str.return_value = "00:00:05"
        session.session_dir.name = "session-new"
        session.channel.name = "lobby"
        session.sink.health.return_value = {}
        cog._sessions[1] = session

        ix = _make_interaction(guild_id=1)
        await cog.record_status.callback(cog, ix)

        msg = ix.response.send_message.call_args[0][0]
        assert "no speakers" in msg.lower()

    @pytest.mark.asyncio
    async def test_status_warns_silent_speaker(self):
        cog = _make_cog()
        session = MagicMock()
        session.duration_str.return_value = "00:02:00"
        session.session_dir.name = "session-sil"
        session.channel.name = "voice"
        session.sink.health.return_value = {
            "Bob": {"kbpm": 0.0, "chunks": 1, "silent_secs": 120}
        }
        cog._sessions[1] = session

        ix = _make_interaction(guild_id=1)
        await cog.record_status.callback(cog, ix)

        msg = ix.response.send_message.call_args[0][0]
        assert "⚠️" in msg or "silent" in msg.lower()
