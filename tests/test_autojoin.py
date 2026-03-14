"""
test_autojoin.py — Tests for RPGREC-008: AutojoinCog

Coverage:
  1. on_voice_state_update ignored when AUTOJOIN_CHANNELS is empty
  2. Join debounce starts when user count reaches AUTOJOIN_MIN_USERS
  3. Join debounce cancelled when users leave before timer fires
  4. After debounce, session started + notification sent
  5. After debounce, join skipped if session already active
  6. After debounce, join skipped if users left again
  7. Stop debounce starts when 0 humans remain in monitored channel
  8. Stop debounce cancelled when users rejoin before timer fires
  9. After stop debounce, session finalized + pipeline enqueued
 10. After stop debounce, stop skipped if session already gone (manual stop)
 11. After stop debounce, stop skipped if users returned to channel
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import bot.autojoin as aj_mod
from bot.autojoin import AutojoinCog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CHANNEL_ID = 111
_GUILD_ID = 9999


def _make_member(bot: bool = False) -> MagicMock:
    m = MagicMock()
    m.bot = bot
    return m


def _make_guild(guild_id: int = _GUILD_ID) -> MagicMock:
    guild = MagicMock()
    guild.id = guild_id
    guild.system_channel = None
    guild.text_channels = []
    guild.me = MagicMock()
    return guild


def _make_channel(
    channel_id: int = _CHANNEL_ID,
    members: list | None = None,
    guild=None,
) -> MagicMock:
    ch = MagicMock()
    ch.id = channel_id
    ch.name = "game-table"
    ch.members = members if members is not None else []
    ch.guild = guild or _make_guild()
    return ch


def _make_voice_state(channel=None) -> MagicMock:
    vs = MagicMock()
    vs.channel = channel
    return vs


def _make_cog(sessions=None) -> AutojoinCog:
    """Create AutojoinCog with a mock bot and optional sessions dict."""
    bot_stub = MagicMock()
    return AutojoinCog(bot_stub, sessions if sessions is not None else {})


# ---------------------------------------------------------------------------
# 1. Ignored when AUTOJOIN_CHANNELS is empty
# ---------------------------------------------------------------------------


async def test_no_monitored_channels_ignores_event():
    cog = _make_cog()
    member = _make_member()
    channel = _make_channel(_CHANNEL_ID)
    before = _make_voice_state(channel=channel)
    after = _make_voice_state(channel=None)

    with patch.object(aj_mod, "AUTOJOIN_CHANNELS", []):
        await cog.on_voice_state_update(member, before, after)

    assert cog._pending == {}


# ---------------------------------------------------------------------------
# 2. Join debounce starts when threshold reached
# ---------------------------------------------------------------------------


async def test_join_debounce_started_when_threshold_reached():
    cog = _make_cog()
    humans = [_make_member() for _ in range(2)]
    guild = _make_guild()
    channel = _make_channel(_CHANNEL_ID, members=humans, guild=guild)
    member = humans[0]
    before = _make_voice_state(channel=None)
    after = _make_voice_state(channel=channel)

    with (
        patch.object(aj_mod, "AUTOJOIN_CHANNELS", [_CHANNEL_ID]),
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
        patch.object(cog, "_schedule_join", new=AsyncMock()) as mock_join,
    ):
        await cog.on_voice_state_update(member, before, after)
        mock_join.assert_called_once_with(channel)


# ---------------------------------------------------------------------------
# 3. Pending timer cancelled when users drop below threshold
# ---------------------------------------------------------------------------


async def test_pending_timer_cancelled_when_below_threshold():
    sessions = {}
    cog = _make_cog(sessions=sessions)

    fake_task = MagicMock()
    fake_task.done.return_value = False
    cog._pending[_GUILD_ID] = fake_task

    guild = _make_guild()
    # Only 1 human remains — below min_users=2
    channel = _make_channel(_CHANNEL_ID, members=[_make_member()], guild=guild)
    member = _make_member()
    before = _make_voice_state(channel=channel)
    after = _make_voice_state(channel=None)

    with (
        patch.object(aj_mod, "AUTOJOIN_CHANNELS", [_CHANNEL_ID]),
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
    ):
        await cog.on_voice_state_update(member, before, after)

    fake_task.cancel.assert_called_once()
    assert _GUILD_ID not in cog._pending


# ---------------------------------------------------------------------------
# 4. After debounce, session started + notification sent
# ---------------------------------------------------------------------------


async def test_debounced_join_starts_session_and_notifies(tmp_path):
    sessions = {}
    cog = _make_cog(sessions=sessions)

    humans = [_make_member() for _ in range(2)]
    guild = _make_guild()
    notify_ch = AsyncMock()
    channel = _make_channel(_CHANNEL_ID, members=humans, guild=guild)

    with (
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
        patch.object(aj_mod, "DEBOUNCE_SECS", 0),
        patch("bot.autojoin.RecordingSession") as MockSession,
        patch("bot.autojoin._find_notify_channel", return_value=notify_ch),
    ):
        instance = AsyncMock()
        instance.session_dir = tmp_path / "session-1234"
        instance.session_dir.mkdir()
        MockSession.return_value = instance

        await cog._debounced_join(channel)

    assert _GUILD_ID in sessions
    notify_ch.send.assert_called_once()
    msg = notify_ch.send.call_args[0][0]
    assert "🔴" in msg
    assert "2" in msg


# ---------------------------------------------------------------------------
# 5. Join skipped if session already active
# ---------------------------------------------------------------------------


async def test_debounced_join_skipped_if_session_active():
    fake_session = MagicMock()
    sessions = {_GUILD_ID: fake_session}
    cog = _make_cog(sessions=sessions)

    humans = [_make_member(), _make_member()]
    guild = _make_guild()
    channel = _make_channel(_CHANNEL_ID, members=humans, guild=guild)

    with (
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
        patch.object(aj_mod, "DEBOUNCE_SECS", 0),
        patch("bot.autojoin.RecordingSession") as MockSession,
    ):
        await cog._debounced_join(channel)
        MockSession.assert_not_called()

    assert sessions[_GUILD_ID] is fake_session


# ---------------------------------------------------------------------------
# 6. Join skipped if users left again before timer fired
# ---------------------------------------------------------------------------


async def test_debounced_join_skipped_if_users_left():
    sessions = {}
    cog = _make_cog(sessions=sessions)

    guild = _make_guild()
    # Only 1 human remains
    channel = _make_channel(_CHANNEL_ID, members=[_make_member()], guild=guild)

    with (
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
        patch.object(aj_mod, "DEBOUNCE_SECS", 0),
        patch("bot.autojoin.RecordingSession") as MockSession,
    ):
        await cog._debounced_join(channel)
        MockSession.assert_not_called()

    assert _GUILD_ID not in sessions


# ---------------------------------------------------------------------------
# 7. Stop debounce starts when 0 humans remain
# ---------------------------------------------------------------------------


async def test_stop_debounce_started_when_empty():
    fake_session = MagicMock()
    sessions = {_GUILD_ID: fake_session}
    cog = _make_cog(sessions=sessions)

    guild = _make_guild()
    channel = _make_channel(_CHANNEL_ID, members=[], guild=guild)
    member = _make_member()
    before = _make_voice_state(channel=channel)
    after = _make_voice_state(channel=None)

    with (
        patch.object(aj_mod, "AUTOJOIN_CHANNELS", [_CHANNEL_ID]),
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
        patch.object(cog, "_schedule_stop", new=AsyncMock()) as mock_stop,
    ):
        await cog.on_voice_state_update(member, before, after)
        mock_stop.assert_called_once_with(channel.guild)


# ---------------------------------------------------------------------------
# 8. Stop timer cancelled when users return (schedule_join replaces it)
# ---------------------------------------------------------------------------


async def test_stop_timer_cancelled_when_users_return():
    fake_session = MagicMock()
    sessions = {_GUILD_ID: fake_session}
    cog = _make_cog(sessions=sessions)

    fake_task = MagicMock()
    fake_task.done.return_value = False
    cog._pending[_GUILD_ID] = fake_task

    guild = _make_guild()
    # 2 humans return — threshold met, new join timer would start
    # but there's already a session, so _cancel_pending is called
    humans = [_make_member(), _make_member()]
    channel = _make_channel(_CHANNEL_ID, members=humans, guild=guild)
    member = humans[0]
    before = _make_voice_state(channel=None)
    after = _make_voice_state(channel=channel)

    with (
        patch.object(aj_mod, "AUTOJOIN_CHANNELS", [_CHANNEL_ID]),
        patch.object(aj_mod, "AUTOJOIN_MIN_USERS", 2),
        # session already exists → _cancel_pending called, not _schedule_join
    ):
        await cog.on_voice_state_update(member, before, after)

    fake_task.cancel.assert_called_once()


# ---------------------------------------------------------------------------
# 9. After stop debounce, session finalized + pipeline enqueued
# ---------------------------------------------------------------------------


async def test_debounced_stop_finalizes_and_enqueues(tmp_path):
    flac = tmp_path / "111.flac"
    flac.touch()

    guild = _make_guild()
    # 0 humans in channel
    voice_ch = _make_channel(_CHANNEL_ID, members=[], guild=guild)

    fake_session = MagicMock()
    fake_session.duration_str.return_value = "00:05:00"
    fake_session.session_dir = tmp_path
    fake_session.stop = AsyncMock(return_value=[flac])
    fake_session.notify_channel = None
    fake_session.channel = voice_ch

    sessions = {_GUILD_ID: fake_session}
    cog = _make_cog(sessions=sessions)

    notify_ch = AsyncMock()

    with (
        patch.object(aj_mod, "DEBOUNCE_SECS", 0),
        patch("bot.autojoin._find_notify_channel", return_value=notify_ch),
        patch("bot.autojoin.enqueue_pipeline") as mock_enqueue,
    ):
        await cog._debounced_stop(guild)

    assert _GUILD_ID not in sessions
    fake_session.stop.assert_called_once()
    mock_enqueue.assert_called_once()
    notify_ch.send.assert_called_once()
    assert "⏹️" in notify_ch.send.call_args[0][0]


# ---------------------------------------------------------------------------
# 10. Stop skipped if session already manually stopped
# ---------------------------------------------------------------------------


async def test_debounced_stop_skipped_if_no_session():
    sessions = {}
    cog = _make_cog(sessions=sessions)
    guild = _make_guild()

    with (
        patch.object(aj_mod, "DEBOUNCE_SECS", 0),
        patch("bot.autojoin.enqueue_pipeline") as mock_enqueue,
    ):
        await cog._debounced_stop(guild)
        mock_enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# 11. Stop skipped if users returned before timer fired
# ---------------------------------------------------------------------------


async def test_debounced_stop_aborted_when_users_returned(tmp_path):
    guild = _make_guild()
    # Users came back
    humans = [_make_member(), _make_member()]
    voice_ch = _make_channel(_CHANNEL_ID, members=humans, guild=guild)

    fake_session = MagicMock()
    fake_session.channel = voice_ch

    sessions = {_GUILD_ID: fake_session}
    cog = _make_cog(sessions=sessions)

    with (
        patch.object(aj_mod, "DEBOUNCE_SECS", 0),
        patch("bot.autojoin.enqueue_pipeline") as mock_enqueue,
    ):
        await cog._debounced_stop(guild)
        mock_enqueue.assert_not_called()

    # Session restored
    assert _GUILD_ID in sessions
    assert sessions[_GUILD_ID] is fake_session
