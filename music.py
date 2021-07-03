import asyncio
import youtube_dl
import pafy
import discord
import nacl
from discord.ext import commands
from dislash import *
import os, re

path = "/proc/self/cgroup"

def is_docker():
  if not os.path.isfile(path): return False
  with open(path) as f:
    for line in f:
      if re.match("\d+:[\w=]+:/docker(-[ce]e)?/\w+", line):
        return True
    return False

if is_docker():
    ffmpegLoc = '/usr/bin/ffmpeg'
else:
    ffmpegLoc = 'ffmpeg/bin/ffmpeg.exe' 
class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        global playingSong
        playingSong = False
        self.setup()

    def setup(self):

        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        global playingSong
        if len(self.song_queue[ctx.guild.id]) > 0:
            ctx.voice_client.stop()
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)
            playingSong = True
        else:
            playingSong = False


    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(
            {"format": "bestaudio", "quiet": True}).extract_info(f"ytsearch{amount}:{song}", download=False,
                                                                 ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        global playingSong
        url = pafy.new(song).getbestaudio().url
        ctx.guild.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(executable=ffmpegLoc, source=url)),
                              after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        playingSong = True
        ctx.guild.voice_client.source.volume = 0.5

    @slash_commands.command(
    description="Makes the bot join your voice channel"
    )
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.reply(
                "You are not connected to a voice channel, please connect to the channel you want the bot to join.")

        if ctx.guild.voice_client is not None:
            await ctx.guild.voice_client.disconnect()
        await ctx.reply('Connected.')
        await ctx.author.voice.channel.connect()

    @slash_commands.command(
    description="Make the bot leave your voice channel.")
    async def leave(self, ctx):
        if ctx.guild.voice_client is not None:
            if len(self.song_queue[ctx.guild.id]) > 0:
                self.song_queue[ctx.guild.id] = []
            await ctx.guild.voice_client.disconnect()
            await ctx.reply('Disconnected succesfully.')
        else:
            await ctx.reply("I am not connected to a voice channel.")

    @slash_commands.command(
    description="Play a song",
    options=[
        Option("song", "Enter a name or url", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
    )
    async def play(self, ctx, *, song=None):
        await ctx.reply('Song loading...')
        global playingSong
        if song is None:
            return await ctx.reply("You must include a song to play.")

        if ctx.guild.voice_client is None:
            await self.join(self, ctx)

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("The given song could not be found. Try using /search.")

            song = result[0]
        if playingSong:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(
                    f"{song} has been added to the queue at position: {queue_len + 1}.")

            else:
                return await ctx.send(
                    "Only 10 songs can be queued at once, please wait for the current song to finish.")
        await self.play_song(ctx, song)
        await ctx.send(f"Now playing: {song}")

    @slash_commands.command(
    description="Search for a song",
    options=[
        Option("song", "Enter what to search for", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
    )
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.reply("You forgot to include a song to search for.")

        await ctx.reply("Searching for song, this may take a few seconds.")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Results for '{song}':",
                              description="*You can use these URL's to play an exact song if the one you want isn't the first result.*\n",
                              colour=discord.Colour.red())

        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Displaying the first {amount} results.")
        await ctx.send(embed=embed)

    @slash_commands.command(
    description="View the queue",
    )
    async def queue(self, ctx):  # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are currently no songs in the queue.")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        await ctx.reply(embed=embed)

    @slash_commands.command(description="Skip the currently playing song")
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.reply("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.reply("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.reply("I am not currently playing any songs for you.")

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                             description="**80% of the voice channel must vote to skip for it to pass.**",
                             colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.reply(
            embed=poll)  # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705")  # yes
        await poll_msg.add_reaction(u"\U0001F6AB")  # no

        await asyncio.sleep(15)  # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)

        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                    votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79:  # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful",
                                      description="***Voting to skip the current song was succesful, skipping now.***",
                                      colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed",
                                  description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**",
                                  colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            await self.check_queue(ctx)



    @slash_commands.command(description="Force skip (only available to staff)")
    @slash_commands.has_permissions(manage_messages=True)
    async def fskip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.reply("No songs are playing.")

        if ctx.author.voice is None:
            return await ctx.reply("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("No songs are playing in your voice channel.")


        ctx.voice_client.stop()
        await self.check_queue(ctx)

        await ctx.reply("Song skipped!")
