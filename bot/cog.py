"""
cog.py — Slash-command cog: /record start | stop | status

One active RecordingSession per guild, stored in self._sessions.
All commands use defer() to handle the ffmpeg finalization latency.
"""

import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from .config import RECORDER_ROLE_NAME, SESSIONS_DIR
from .recorder import RecordingSession

log = logging.getLogger(__name__)


def _has_permission(member: discord.Member, role_name: str | None) -> bool:
    """Return True if member is allowed to manage recordings.

    When RECORDER_ROLE_NAME is not configured every member is allowed.
    """
    if not role_name:
        return True
    return any(getattr(r, "name", None) == role_name for r in getattr(member, "roles", []))


class RecordCog(commands.Cog):
    """Provides the /record slash command group."""

    record = app_commands.Group(
        name="record",
        description="RPG session voice recording",
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # guild_id → active RecordingSession
        self._sessions: dict[int, RecordingSession] = {}

    # ------------------------------------------------------------------
    # /record start
    # ------------------------------------------------------------------

    @record.command(name="start", description="Join your voice channel and start recording")
    async def record_start(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=False, thinking=True)

        member = interaction.guild.get_member(interaction.user.id)
        if not _has_permission(member, RECORDER_ROLE_NAME):
            await interaction.followup.send(
                "❌ You don't have permission to start recordings. "
                f"Required role: **{RECORDER_ROLE_NAME}**"
            )
            return

        guild_id = interaction.guild_id
        if guild_id in self._sessions:
            await interaction.followup.send(
                "⚠️ A recording is already running in this server. "
                "Use `/record stop` first."
            )
            return

        if not member or not member.voice or not member.voice.channel:
            await interaction.followup.send(
                "❌ You must be in a voice channel to start recording."
            )
            return

        channel = member.voice.channel

        try:
            session = RecordingSession(channel, SESSIONS_DIR)
            await session.start()
        except Exception as exc:
            log.exception("Failed to start recording in #%s", channel.name)
            await interaction.followup.send(f"❌ Could not start recording: {exc}")
            return

        self._sessions[guild_id] = session
        await interaction.followup.send(
            f"🔴 **Recording started**\n"
            f"Channel: **{channel.name}** | Session: `{session.session_dir.name}`\n"
            f"Use `/record stop` to end and export."
        )

    # ------------------------------------------------------------------
    # /record stop
    # ------------------------------------------------------------------

    @record.command(name="stop", description="Stop recording and export FLAC files per speaker")
    async def record_stop(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=False, thinking=True)

        member = interaction.guild.get_member(interaction.user.id)
        if not _has_permission(member, RECORDER_ROLE_NAME):
            await interaction.followup.send(
                "❌ You don't have permission to stop recordings. "
                f"Required role: **{RECORDER_ROLE_NAME}**"
            )
            return

        guild_id = interaction.guild_id
        session = self._sessions.pop(guild_id, None)
        if session is None:
            await interaction.followup.send("⚠️ No recording is currently running.")
            return

        duration = session.duration_str()

        await interaction.followup.send(
            f"⏳ Recording stopped after **{duration}** — finalizing audio files…"
        )

        try:
            flac_paths = await session.stop()
        except Exception as exc:
            log.exception("Error during session finalization")
            await interaction.followup.send(f"❌ Finalization error: {exc}")
            return

        if flac_paths:
            files_list = "\n".join(f"  • `{p.name}`" for p in flac_paths)
            await interaction.followup.send(
                f"✅ **Session complete** — `{session.session_dir.name}`\n"
                f"Duration: **{duration}** | Speakers: **{len(flac_paths)}**\n"
                f"{files_list}"
            )
        else:
            await interaction.followup.send(
                f"⚠️ Session ended but no audio was captured "
                f"(duration: {duration})."
            )

    # ------------------------------------------------------------------
    # /record status
    # ------------------------------------------------------------------

    @record.command(name="status", description="Show whether a recording is running and health stats")
    async def record_status(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        session = self._sessions.get(guild_id)

        if session is None:
            await interaction.response.send_message(
                "⬛ No recording in progress.", ephemeral=True
            )
            return

        health = session.sink.health()
        lines = [
            f"🔴 **Recording active** — `{session.session_dir.name}`",
            f"Duration: **{session.duration_str()}** | Channel: **{session.channel.name}**",
            "",
            "**Speakers:**",
        ]

        if health:
            for name, stats in health.items():
                silent_tag = (
                    f"  ⚠️ silent {stats['silent_secs']:.0f}s"
                    if stats["silent_secs"] > 30
                    else ""
                )
                lines.append(
                    f"  • **{name}**: {stats['kbpm']:.1f} KB/min"
                    f"  |  {stats['chunks']} chunk(s){silent_tag}"
                )
        else:
            lines.append("  _(no speakers detected yet)_")

        await interaction.response.send_message("\n".join(lines), ephemeral=True)
