"""
autojoin.py — RPGREC-008: Automatic join/stop based on voice channel occupancy.

Configuration (.env):
    AUTOJOIN_CHANNELS   comma-separated voice channel IDs to monitor
    AUTOJOIN_MIN_USERS  minimum non-bot users before recording starts (default: 2)

Behaviour:
    - Monitors on_voice_state_update events for configured channels.
    - When user count reaches AUTOJOIN_MIN_USERS, schedules a join after
      DEBOUNCE_SECS seconds (cancels if count drops again before timer fires).
    - When user count drops to 0, schedules a stop after DEBOUNCE_SECS seconds.
    - Sends a Discord message to the guild's system channel (or first text
      channel) on auto-join: "🔴 Automatische Aufnahme gestartet (N Teilnehmer)"
    - /record stop always works even for auto-started sessions (shared _sessions).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from .config import AUTOJOIN_CHANNELS, AUTOJOIN_MIN_USERS, SESSIONS_DIR
from .pipeline import enqueue_pipeline
from .recorder import RecordingSession

log = logging.getLogger(__name__)

# Seconds to wait before acting on a join/stop trigger.
DEBOUNCE_SECS = 60


def _human_members(channel: discord.VoiceChannel) -> list[discord.Member]:
    """Return non-bot members currently in the voice channel."""
    return [m for m in channel.members if not m.bot]


def _find_notify_channel(guild: discord.Guild) -> Optional[discord.abc.Messageable]:
    """Return a text channel to post auto-join notifications in."""
    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        return guild.system_channel
    for ch in guild.text_channels:
        if ch.permissions_for(guild.me).send_messages:
            return ch
    return None


class AutojoinCog(commands.Cog):
    """Listens for voice state changes and auto-starts/stops recordings."""

    def __init__(self, bot: commands.Bot, sessions: dict[int, RecordingSession]) -> None:
        self.bot = bot
        # Shared session registry with RecordCog (same dict object)
        self._sessions = sessions
        # guild_id → pending asyncio.Task (debounce timer)
        self._pending: dict[int, asyncio.Task] = {}

    async def cog_load(self) -> None:
        """Register the voice state listener after the cog is loaded."""
        self.bot.add_listener(self.on_voice_state_update, "on_voice_state_update")

    async def cog_unload(self) -> None:
        """Remove the listener when the cog is unloaded."""
        self.bot.remove_listener(self.on_voice_state_update, "on_voice_state_update")

    # ------------------------------------------------------------------
    # Event listener
    # ------------------------------------------------------------------

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if not AUTOJOIN_CHANNELS:
            return  # autojoin disabled

        # Collect affected channels (both sides of the state change)
        channels_to_check: set[discord.VoiceChannel] = set()
        for state in (before, after):
            if state.channel and state.channel.id in AUTOJOIN_CHANNELS:
                channels_to_check.add(state.channel)

        for channel in channels_to_check:
            await self._evaluate_channel(channel)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    async def _evaluate_channel(self, channel: discord.VoiceChannel) -> None:
        guild_id = channel.guild.id
        human_count = len(_human_members(channel))
        already_recording = guild_id in self._sessions

        if not already_recording and human_count >= AUTOJOIN_MIN_USERS:
            await self._schedule_join(channel)
        elif already_recording and human_count == 0:
            await self._schedule_stop(channel.guild)
        else:
            # Conditions not met — cancel any pending timer
            self._cancel_pending(guild_id)

    async def _schedule_join(self, channel: discord.VoiceChannel) -> None:
        guild_id = channel.guild.id
        if guild_id in self._pending:
            return  # timer already running

        log.info(
            "Autojoin debounce started for #%s (%ds)",
            channel.name,
            DEBOUNCE_SECS,
        )
        task = asyncio.create_task(
            self._debounced_join(channel),
            name=f"autojoin-{guild_id}",
        )
        self._pending[guild_id] = task

    async def _schedule_stop(self, guild: discord.Guild) -> None:
        guild_id = guild.id
        if guild_id in self._pending:
            return  # stop timer already running

        log.info(
            "Autostop debounce started for guild %d (%ds)",
            guild_id,
            DEBOUNCE_SECS,
        )
        task = asyncio.create_task(
            self._debounced_stop(guild),
            name=f"autostop-{guild_id}",
        )
        self._pending[guild_id] = task

    def _cancel_pending(self, guild_id: int) -> None:
        task = self._pending.pop(guild_id, None)
        if task and not task.done():
            task.cancel()
            log.debug("Cancelled pending autojoin/stop timer for guild %d", guild_id)

    # ------------------------------------------------------------------
    # Debounced actions
    # ------------------------------------------------------------------

    async def _debounced_join(self, channel: discord.VoiceChannel) -> None:
        guild_id = channel.guild.id
        try:
            await asyncio.sleep(DEBOUNCE_SECS)
        except asyncio.CancelledError:
            log.debug("Autojoin timer cancelled for #%s", channel.name)
            return
        finally:
            self._pending.pop(guild_id, None)

        # Re-check: another manual session may have started, or users left
        if guild_id in self._sessions:
            log.info("Autojoin skipped — session already active for guild %d", guild_id)
            return
        human_count = len(_human_members(channel))
        if human_count < AUTOJOIN_MIN_USERS:
            log.info(
                "Autojoin skipped — only %d user(s) in #%s (need %d)",
                human_count, channel.name, AUTOJOIN_MIN_USERS,
            )
            return

        notify_ch = _find_notify_channel(channel.guild)
        try:
            session = RecordingSession(channel, SESSIONS_DIR, notify_channel=notify_ch)
            await session.start()
        except Exception as exc:
            log.exception("Autojoin: failed to start recording in #%s: %s", channel.name, exc)
            if notify_ch:
                await notify_ch.send(f"❌ Autojoin: Aufnahme konnte nicht gestartet werden: {exc}")
            return

        self._sessions[guild_id] = session
        log.info("Autojoin: recording started in #%s", channel.name)

        if notify_ch:
            await notify_ch.send(
                f"🔴 Automatische Aufnahme gestartet ({human_count} Teilnehmer)"
            )

    async def _debounced_stop(self, guild: discord.Guild) -> None:
        guild_id = guild.id
        try:
            await asyncio.sleep(DEBOUNCE_SECS)
        except asyncio.CancelledError:
            log.debug("Autostop timer cancelled for guild %d", guild_id)
            return
        finally:
            self._pending.pop(guild_id, None)

        session = self._sessions.pop(guild_id, None)
        if session is None:
            return  # already stopped manually

        # Re-check: if users rejoined, don't stop
        human_count = len(_human_members(session.channel))
        if human_count > 0:
            # Put session back, users returned
            self._sessions[guild_id] = session
            log.info(
                "Autostop cancelled — %d user(s) back in #%s",
                human_count, session.channel.name,
            )
            return

        duration = session.duration_str()
        log.info("Autostop: stopping recording (duration %s)", duration)

        notify_ch = session.notify_channel or _find_notify_channel(guild)

        try:
            flac_paths = await session.stop()
        except Exception as exc:
            log.exception("Autostop: finalization error: %s", exc)
            if notify_ch:
                await notify_ch.send(f"❌ Autostop: Fehler beim Finalisieren: {exc}")
            return

        if flac_paths and notify_ch:
            await notify_ch.send(
                f"⏹️ Automatische Aufnahme beendet — `{session.session_dir.name}`\n"
                f"Dauer: **{duration}** | Sprecher: **{len(flac_paths)}**"
            )
            enqueue_pipeline(session.session_dir, flac_paths, notify_ch)
        elif notify_ch:
            await notify_ch.send(
                f"⚠️ Automatische Aufnahme beendet — kein Audio aufgezeichnet (Dauer: {duration})"
            )
