from __future__ import annotations

import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load the standalone Giveaway Bot .env before importing config.
load_dotenv()

from config import TEST_GUILD_ID
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("giveaway-bot")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Put it in .env or your Render environment variables.")

intents = discord.Intents.default()
intents.guilds = True
intents.members = False


class GiveawayBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.giveaways")

        if TEST_GUILD_ID:
            # Keep testing commands scoped to the Giveaway Bot's test server.
            # First copy the six current commands to the guild for instant updates.
            guild = discord.Object(id=TEST_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)

            # Remove stale GLOBAL commands previously published by THIS standalone
            # Giveaway application (for example /giveaway_start). This does not
            # affect the separate BOTW/NightLegion Discord application.
            self.tree.clear_commands(guild=None)
            await self.tree.sync()

            log.info("Synced %s Giveaway commands to test guild %s and cleared stale global Giveaway commands", len(synced), TEST_GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("Synced %s global commands", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")
        await self.change_presence(activity=discord.Game(name="NightLegion Giveaways"))


GiveawayBot().run(TOKEN)
