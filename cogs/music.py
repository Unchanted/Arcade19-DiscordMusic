from typing import cast

import discord
import wavelink

from discord.ext import commands

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs) -> None:
        self.message: discord.Message | None = None
        self.home: discord.TextChannel | discord.VoiceChannel | discord.StageChannel | None = None
        super().__init__(*args, **kwargs)

class Context(commands.Context):
    voice_client: Player | None


# class View(discord.ui.View):


class Music(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Node {payload.node!r} is ready!")
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player = payload.player

        if not player: # edge case
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed(title="Now Playing", color=discord.Color.random())
        embed.set_author(name=track.author, icon_url=track.artist.artwork)

        if track.artwork:
            embed.set_image(url=track.artwork)

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)
        
        if track.uri:
            embed.description = f"**[{track.title}]({track.uri})** by `{track.author}`"
        else:
            embed.description = f"**{track.title}** by `{track.author}`"
        
        if original and original.recommended: # weird bug. it should have been track.recommended, but this works instead.
            embed.set_footer(text=f"\n\n>This track was recommended based on [{original.title}]({original.uri}) by {original.author}")

        if getattr(player, "message", None) is None:
            player.message = await player.home.send(embed=embed)
        else:
            await player.message.edit(embed=embed)
    
    @commands.command()
    async def play(self, ctx: Context, *, query):
        """Play a song with the given query."""
        if not ctx.guild:
            return

        player: Player | None = ctx.voice_client

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=Player)  # type: ignore
            except AttributeError:
                await ctx.send("Please join a voice channel first before using this command.")
                return
            except discord.ClientException:
                await ctx.send("I was unable to join this voice channel. Please try again.")
                return

        player.autoplay = wavelink.AutoPlayMode.enabled

        if player.home is None:
            player.home = ctx.channel
        elif player.home != ctx.channel:
            await ctx.send(f"You can only play songs in {player.home.mention}, as the player has already started there.")
            return

        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            await ctx.send(f"{ctx.author.mention} - Could not find any tracks with that query. Please try again.")
            return

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            await ctx.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await ctx.send(f"Added **`{track}`** to the queue.")

        if not player.playing:

            await player.play(player.queue.get(), volume=30)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command()
    async def skip(self, ctx: Context) -> None:
        """Skip the current song."""
        player = ctx.voice_client
        if not player:
            return

        await player.skip(force=True)
        await ctx.message.add_reaction("\u2705")

    @commands.command(name="toggle", aliases=["pause", "resume"])
    async def pause_resume(self, ctx: Context) -> None:
        """Pause or Resume the Player depending on its current state."""
        player = ctx.voice_client
        if not player:
            return

        await player.pause(not player.paused)
        await ctx.message.add_reaction("\u2705")

    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx: Context) -> None:
        """Disconnect the Player."""
        player = ctx.voice_client
        if not player:
            return

        await player.disconnect()
        await ctx.message.add_reaction("\u2705")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
