"""
test_slash_commands.py — Tests for /record start|stop|status (RPGREC-002d).

Acceptance criteria (from RPGREC-002d):
  1. /record start without voice channel → user-friendly error message
  2. /record start while recording active → "already running" error
  3. /record stop without active recording → "no active recording" error
  4. Full flow: start → stop → flac paths returned, completion message sent
  5. Permission check: user without recorder role is denied start/stop
  6. Permission check: user with recorder role is allowed
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.mocks.discord_mocks import MockBot, MockInteraction, MockVoiceChannel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cog(bot: MockBot):
    """Instantiate RecordCog and register it on bot."""
    from bot.cog import RecordCog

    cog = RecordCog(bot)
    bot.add_cog(cog)
    return cog


def _interaction_no_voice(guild_id: int = 9999) -> MockInteraction:
    """Interaction where the invoking user has no active voice channel."""
    ix = MockInteraction(guild_id=guild_id)
    ix.guild.get_member.return_value.voice.channel = None
    return ix


def _interaction_in_voice(
    guild_id: int = 9999,
    channel_name: str = "game-table",
) -> tuple[MockInteraction, MockVoiceChannel]:
    """Interaction where the invoking user sits in a voice channel."""
    channel = MockVoiceChannel(name=channel_name)
    ix = MockInteraction(guild_id=guild_id, voice_channel=channel)
    return ix, channel


# ---------------------------------------------------------------------------
# /record start
# ---------------------------------------------------------------------------


class TestRecordStart:
    async def test_ac1_user_not_in_voice_channel(self, mock_bot):
        """AC1: /record start without voice → friendly error, no session created."""
        cog = _make_cog(mock_bot)
        ix = _interaction_no_voice()

        await cog.record_start.callback(cog, ix)

        reply = ix.last_reply().lower()
        assert "voice" in reply
        assert 9999 not in cog._sessions

    async def test_ac2_already_recording(self, mock_bot):
        """AC2: /record start while session is active → 'already running' message."""
        cog = _make_cog(mock_bot)
        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:03:00"
        cog._sessions[9999] = fake_session

        ix, _ = _interaction_in_voice()
        await cog.record_start.callback(cog, ix)

        reply = ix.last_reply().lower()
        assert "already" in reply
        # Session must not have been replaced
        assert cog._sessions[9999] is fake_session

    async def test_start_happy_path_sends_confirmation(self, mock_bot, tmp_path):
        """Happy path: start joins channel, stores session, sends 🔴 message."""
        cog = _make_cog(mock_bot)
        ix, _ = _interaction_in_voice()

        with patch("bot.cog.RecordingSession") as MockSession:
            instance = AsyncMock()
            instance.session_dir = tmp_path / "session-1234"
            instance.session_dir.mkdir()
            MockSession.return_value = instance

            await cog.record_start.callback(cog, ix)

        assert 9999 in cog._sessions
        assert "🔴" in ix.last_reply()

    async def test_start_handles_session_exception(self, mock_bot):
        """If RecordingSession.start() raises, an error message is sent."""
        cog = _make_cog(mock_bot)
        ix, _ = _interaction_in_voice()

        with patch("bot.cog.RecordingSession") as MockSession:
            instance = AsyncMock()
            instance.start.side_effect = RuntimeError("no voice backend")
            MockSession.return_value = instance

            await cog.record_start.callback(cog, ix)

        assert "❌" in ix.last_reply()
        assert 9999 not in cog._sessions


# ---------------------------------------------------------------------------
# /record stop
# ---------------------------------------------------------------------------


class TestRecordStop:
    async def test_ac3_no_active_recording(self, mock_bot):
        """AC3: /record stop with no active session → clear error message."""
        cog = _make_cog(mock_bot)
        ix = MockInteraction(guild_id=9999)

        await cog.record_stop.callback(cog, ix)

        reply = ix.last_reply().lower()
        assert "no recording" in reply or "keine" in reply or "not currently" in reply

    async def test_stop_happy_path_confirms_completion(self, mock_bot, tmp_path):
        """AC4 (stop half): stop ends session, sends ✅ with file list."""
        cog = _make_cog(mock_bot)

        flac = tmp_path / "111.flac"
        flac.touch()

        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:02:30"
        fake_session.stop = AsyncMock(return_value=[flac])
        fake_session.session_dir = tmp_path
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        await cog.record_stop.callback(cog, ix)

        # Session removed from registry
        assert 9999 not in cog._sessions

        # Final message confirms completion
        all_replies = " ".join(ix.sent_messages)
        assert "✅" in all_replies
        assert "111.flac" in all_replies

    async def test_stop_with_no_audio_sends_warning(self, mock_bot, tmp_path):
        """When stop() returns no flac paths, a warning (not crash) is sent."""
        cog = _make_cog(mock_bot)

        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:00:05"
        fake_session.stop = AsyncMock(return_value=[])
        fake_session.session_dir = tmp_path
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        await cog.record_stop.callback(cog, ix)

        assert 9999 not in cog._sessions
        assert "⚠️" in " ".join(ix.sent_messages)

    async def test_stop_handles_finalize_exception(self, mock_bot):
        """If session.stop() raises, an error message is sent."""
        cog = _make_cog(mock_bot)

        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:01:00"
        fake_session.stop = AsyncMock(side_effect=RuntimeError("ffmpeg not found"))
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        await cog.record_stop.callback(cog, ix)

        assert "❌" in " ".join(ix.sent_messages)


# ---------------------------------------------------------------------------
# /record status
# ---------------------------------------------------------------------------


class TestRecordStatus:
    async def test_status_no_session(self, mock_bot):
        """Status with no active session → idle message."""
        cog = _make_cog(mock_bot)
        ix = MockInteraction(guild_id=9999)

        await cog.record_status.callback(cog, ix)

        reply = ix.last_reply().lower()
        assert "no recording" in reply or "keine" in reply or "not" in reply

    async def test_status_active_session_shows_details(self, mock_bot):
        """Status with active session → duration, channel, speaker stats."""
        cog = _make_cog(mock_bot)

        fake_sink = MagicMock()
        fake_sink.health.return_value = {
            "Alice": {"kbpm": 55.0, "chunks": 2, "silent_secs": 5},
        }

        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:10:00"
        fake_session.session_dir.name = "session-1234"
        fake_session.channel.name = "game-table"
        fake_session.sink = fake_sink
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        await cog.record_status.callback(cog, ix)

        reply = ix.last_reply()
        assert "🔴" in reply
        assert "Alice" in reply
        assert "00:10:00" in reply

    async def test_status_no_speakers_yet(self, mock_bot):
        """Status with session but no speakers → 'no speakers detected' note."""
        cog = _make_cog(mock_bot)

        fake_sink = MagicMock()
        fake_sink.health.return_value = {}

        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:00:30"
        fake_session.session_dir.name = "session-5678"
        fake_session.channel.name = "lobby"
        fake_session.sink = fake_sink
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        await cog.record_status.callback(cog, ix)

        assert "no speakers" in ix.last_reply().lower() or "_(no speakers" in ix.last_reply()

    async def test_status_warns_on_silent_speaker(self, mock_bot):
        """Status marks a speaker as silent when silent_secs > 30."""
        cog = _make_cog(mock_bot)

        fake_sink = MagicMock()
        fake_sink.health.return_value = {
            "Bob": {"kbpm": 0.1, "chunks": 1, "silent_secs": 90},
        }

        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:05:00"
        fake_session.session_dir.name = "session-9999"
        fake_session.channel.name = "dungeon"
        fake_session.sink = fake_sink
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        await cog.record_status.callback(cog, ix)

        assert "⚠️" in ix.last_reply()


# ---------------------------------------------------------------------------
# Permission check
# ---------------------------------------------------------------------------


def _reload_cog_with_role(monkeypatch, role_name: str | None):
    """Reload bot.cog (and bot.config) with RECORDER_ROLE_NAME set."""
    monkeypatch.setenv("DISCORD_TOKEN", "dev-dummy-token")
    if role_name:
        monkeypatch.setenv("RECORDER_ROLE_NAME", role_name)
    else:
        monkeypatch.delenv("RECORDER_ROLE_NAME", raising=False)

    for mod in ("bot.config", "bot.cog"):
        sys.modules.pop(mod, None)

    from bot.cog import RecordCog

    return RecordCog


class TestPermissions:
    async def test_start_denied_without_required_role(self, mock_bot, monkeypatch):
        """User without the recorder role cannot start a recording."""
        RecordCog = _reload_cog_with_role(monkeypatch, "Recorder")
        cog = RecordCog(mock_bot)

        ix, _ = _interaction_in_voice()
        ix.guild.get_member.return_value.roles = []  # no roles

        await cog.record_start.callback(cog, ix)

        reply = ix.last_reply().lower()
        assert "permission" in reply or "role" in reply
        assert 9999 not in cog._sessions

    async def test_start_allowed_with_required_role(self, mock_bot, tmp_path, monkeypatch):
        """User with the recorder role can start a recording."""
        RecordCog = _reload_cog_with_role(monkeypatch, "Recorder")
        cog = RecordCog(mock_bot)

        ix, _ = _interaction_in_voice()
        role = MagicMock()
        role.name = "Recorder"
        ix.guild.get_member.return_value.roles = [role]

        with patch("bot.cog.RecordingSession") as MockSession:
            instance = AsyncMock()
            instance.session_dir = tmp_path / "session-1234"
            instance.session_dir.mkdir()
            MockSession.return_value = instance

            await cog.record_start.callback(cog, ix)

        assert "🔴" in ix.last_reply()
        assert 9999 in cog._sessions

    async def test_stop_denied_without_required_role(self, mock_bot, monkeypatch):
        """User without the recorder role cannot stop a recording."""
        RecordCog = _reload_cog_with_role(monkeypatch, "Recorder")
        cog = RecordCog(mock_bot)

        fake_session = AsyncMock()
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        ix.guild.get_member.return_value.roles = []

        await cog.record_stop.callback(cog, ix)

        reply = ix.last_reply().lower()
        assert "permission" in reply or "role" in reply
        # Session must NOT have been removed
        assert 9999 in cog._sessions

    async def test_stop_allowed_with_required_role(self, mock_bot, tmp_path, monkeypatch):
        """User with the recorder role can stop a recording."""
        RecordCog = _reload_cog_with_role(monkeypatch, "Recorder")
        cog = RecordCog(mock_bot)

        flac = tmp_path / "222.flac"
        flac.touch()
        fake_session = MagicMock()
        fake_session.duration_str.return_value = "00:01:00"
        fake_session.stop = AsyncMock(return_value=[flac])
        fake_session.session_dir = tmp_path
        cog._sessions[9999] = fake_session

        ix = MockInteraction(guild_id=9999)
        role = MagicMock()
        role.name = "Recorder"
        ix.guild.get_member.return_value.roles = [role]

        await cog.record_stop.callback(cog, ix)

        assert 9999 not in cog._sessions
        assert "✅" in " ".join(ix.sent_messages)

    async def test_no_role_restriction_allows_everyone(self, mock_bot, tmp_path, monkeypatch):
        """When RECORDER_ROLE_NAME is unset, any user can start recording."""
        RecordCog = _reload_cog_with_role(monkeypatch, None)
        cog = RecordCog(mock_bot)

        ix, _ = _interaction_in_voice()
        ix.guild.get_member.return_value.roles = []  # no roles, but no restriction

        with patch("bot.cog.RecordingSession") as MockSession:
            instance = AsyncMock()
            instance.session_dir = tmp_path / "session-open"
            instance.session_dir.mkdir()
            MockSession.return_value = instance

            await cog.record_start.callback(cog, ix)

        assert "🔴" in ix.last_reply()

    async def test_cog_registers_on_bot(self, mock_bot):
        """RecordCog must be retrievable by name after add_cog()."""
        from bot.cog import RecordCog

        cog = RecordCog(mock_bot)
        mock_bot.add_cog(cog)
        assert mock_bot.get_cog("RecordCog") is cog
