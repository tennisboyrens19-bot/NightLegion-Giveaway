from __future__ import annotations

import discord


class GiveawayView(discord.ui.View):
    def __init__(self, cog, giveaway_id: str, *, ended: bool = False):
        super().__init__(timeout=None)
        self.cog = cog
        self.giveaway_id = giveaway_id

        enter = discord.ui.Button(
            label="Enter Giveaway" if not ended else "Giveaway Ended",
            emoji="🎉" if not ended else "🏁",
            style=discord.ButtonStyle.success if not ended else discord.ButtonStyle.secondary,
            custom_id=f"nl-gw:enter:{giveaway_id}",
            disabled=ended,
        )
        enter.callback = self.enter
        self.add_item(enter)

        stats = discord.ui.Button(label="My Stats", emoji="🏆", style=discord.ButtonStyle.secondary, custom_id=f"nl-gw:stats:{giveaway_id}")
        stats.callback = self.stats
        self.add_item(stats)

        entrants = discord.ui.Button(label="Entrants", emoji="👥", style=discord.ButtonStyle.secondary, custom_id=f"nl-gw:entrants:{giveaway_id}")
        entrants.callback = self.entrants
        self.add_item(entrants)

        info = discord.ui.Button(label="Info", emoji="ℹ️", style=discord.ButtonStyle.secondary, custom_id=f"nl-gw:info:{giveaway_id}")
        info.callback = self.info
        self.add_item(info)

    async def enter(self, interaction: discord.Interaction):
        await self.cog.handle_entry(interaction, self.giveaway_id)

    async def stats(self, interaction: discord.Interaction):
        await self.cog.send_user_stats(interaction, interaction.user.id)

    async def entrants(self, interaction: discord.Interaction):
        await self.cog.send_entrants(interaction, self.giveaway_id)

    async def info(self, interaction: discord.Interaction):
        await self.cog.send_info(interaction, self.giveaway_id)
