"""
__main__.py — Entry point.  Run with: python -m bot

Sets up logging, creates the bot, loads the RecordCog, syncs slash
commands, then connects to Discord.
"""

import asyncio
import logging
import sys

import discord
from discord.ext import commands

from .autojoin import AutojoinCog
from .config import AUTOJOIN_CHANNELS, DISCORD_TOKEN, LOG_LEVEL
from .cog import RecordCog

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("rpg-recorder")


class RPGRecorderBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        record_cog = RecordCog(self)
        await self.add_cog(record_cog)
        if AUTOJOIN_CHANNELS:
            await self.add_cog(AutojoinCog(self, record_cog._sessions))
            log.info("Autojoin enabled for channels: %s", AUTOJOIN_CHANNELS)
        await self.tree.sync()
        log.info("Slash commands synced to Discord")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id=%d) — Ready", self.user, self.user.id)


async def main() -> None:
    bot = RPGRecorderBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutdown requested — bye")
