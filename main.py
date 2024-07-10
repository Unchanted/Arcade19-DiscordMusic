import os

import discord
import wavelink

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class Bot(commands.Bot):
    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri="http://localhost:2333", password="youshallnotpass")]
        await wavelink.Pool.connect(nodes=nodes, client=self)

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cogs.{filename[:-3]} .")
        
        await self.load_extension("jishaku")
    
    async def close(self):
        await wavelink.Pool.close()
        await super().close()

bot = Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")

@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f"Pong! ({round(bot.latency*1000, 2)}ms)")

@bot.command()
@commands.is_owner()
async def load(ctx: commands.Context, cog_name):
    await bot.load_extension(f"cogs.{cog_name}")
    await ctx.send(f"Loaded {cog_name}")

@bot.command()
@commands.is_owner()
async def unload(ctx: commands.Context, cog_name):
    await bot.unload_extension(f"cogs.{cog_name}")
    await ctx.send(f"Unloaded {cog_name}")

@bot.command()
@commands.is_owner()
async def reload(ctx: commands.Context, cog_name):
    await bot.reload_extension(f"cogs.{cog_name}")
    await ctx.send(f"Reloaded {cog_name}")

bot.run(os.getenv("TOKEN"))
