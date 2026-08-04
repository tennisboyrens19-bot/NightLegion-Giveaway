from giveaway.cog import Giveaways


async def setup(bot):
    await bot.add_cog(Giveaways(bot))
