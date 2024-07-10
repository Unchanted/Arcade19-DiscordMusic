import discord
import wavelink

from discord.ext import commands

class Music(commands.Cog):
    
    @commands.command()
    async def play(self, ctx: commands.Context):
        await ctx.send(wavelink.nodes)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Node {payload.node!r} is ready!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music())
