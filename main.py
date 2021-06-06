# imports
import asyncio
import shelve
import aiofiles
import discord
from discord import *
import discord.utils
from discord.ext import commands, tasks
import json
import random
from itertools import cycle
import sys

# main bot setup
verText = 'Version 1.5.5 (minor tweaks to suggestions, including numbering and deleting the command)'
sConfig = shelve.open('config', writeback = True)
intents = discord.Intents.default()
intents.members = True
intents.messages = True

status = cycle(
    ['Try )help', 'Prefix - )'])


@tasks.loop(seconds=5)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))


bot = commands.Bot(command_prefix="&", help_command=None, intents=intents)
bot.ticket_configs = {}
bot.warnings = {}  # guild_id : {member_id: [count, [(admin_id, reason)]]}


@bot.event
async def on_ready():
    for guild in bot.guilds:
        async with aiofiles.open(f"{guild.id} warnings.txt", mode="a") as temp:
            pass

        bot.warnings[guild.id] = {}

    for guild in bot.guilds:
        async with aiofiles.open(f"{guild.id} warnings.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    bot.warnings[guild.id][member_id][0] += 1
                    bot.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    bot.warnings[guild.id][member_id] = [1, [(admin_id, reason)]]

    for file in ["ticket_configs.txt"]:
        async with aiofiles.open(file, mode="a") as temp:
            pass

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.ticket_configs[int(data[0])] = [int(data[1]), int(data[2]), int(data[3])]

    print("Your bot is ready to be used.")


class BotData:
    def __init__(self):
            self.welcome_channel = None
            self.goodbye_channel = None
            self.suggestion_channel = None
                    


botdata = BotData()
try:
    bot.reaction_roles = sConfig['reaction']
except KeyError:
    sConfig['reaction'] = []
try:
    suggestionNumber = sConfig['snum']
except KeyError:
    sConfig['snum'] = 0

# test commands
@bot.command()
async def test(ctx):
    channel = ctx.channel
    await channel.send("Your test worked! " + str(ctx.author))


@bot.command()
async def Test(ctx):
    channel = ctx.channel
    await channel.send("Your test worked! " + str(ctx.author))


@bot.command()
async def user_info(ctx, id):
    member = ctx.guild.get_member(int(id))
    await ctx.send(member.name)
# ver command
@bot.command()
async def ver(ctx):
    await ctx.send(verText)


# help commands

async def get_help_embed():
    em = discord.Embed(title="Help!", description="", color=discord.Color.green())
    em.description += f"**{bot.command_prefix}test** : Tests to make sure the bot is working properly.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}help** : The help command gives you a list of commands you can do with ths bot. you can also @ mention the bot in a message to get a list of commands.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}moderator_help** : provides a list of moderator commands. Only staff members have access to this command.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}quick_help** : gets a quick help message.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}shop** : lists the buyable items you can get.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}bal** : lists your balance.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}withdraw (amount)** : lets you take however much money you want out of your bank account.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}deposit (amount)** : lets you put however much money you want into your back account.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}buy (item)** : lets you buy the item you want from the shop/\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}gamble (amount)** : gambles the amount of money you want to gamble.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}bag** : lists the items you have bought from the store.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}sell (item)** : sells an item back to the store for money, you will not get all the money you used to buy the item back.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}suggest (suggestion)** : suggests something in the suggestion channel.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}send (user) (amount)** : sends specified amount of money to specified user.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}coinflip (amount) (face) ** : bets on flipping a coin\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}roll (amount) (face) ** : bets on rolling a dice, run without an amount to not bet\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}leaderboard (amount of players you want listed)** : lists the specified amount of players based on who has the most money.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}ver** : responds with the bot version and latest feature.\n"
    em.description += f"\n"
    em.description += f"**{bot.command_prefix}8ball** : Responds like an 8ball. You can also type **{bot.command_prefix}8b**\n"
    em.set_footer(text="Here is a list of commands the bot can do!", icon_url=bot.user.avatar_url)
    return em


@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        em = await get_help_embed()
        await message.channel.send(embed=em)

    await bot.process_commands(message)


@bot.command()
async def help(ctx):
    em = await get_help_embed()
    await ctx.send(embed=em)


@bot.command()
async def quick_help(ctx):
    info = await info_embed()
    await ctx.send(embed=info)


async def info_embed():
    info = discord.Embed(title="Quick Help!", description="", color=discord.Color.green())
    info.description += f"Do **{bot.command_prefix}minecraft_help** : to get quick help with the minecraft server.\n"
    info.description += f"\n"
    info.description += f"Do **{bot.command_prefix}discord_help** : to get quick help with the discord\n"
    info.description += f"\n"
    info.description += f"Do **{bot.command_prefix}faq** : to get a FAQ list.\n"
    info.set_footer(
        text="Thanks for using Homeschool Club quick help services. If you need more help please open a ticket.",
        icon_url=bot.user.avatar_url)
    return info


@bot.command()
async def minecraft_help(ctx):
    mc = await minecraft_embed()
    await ctx.send(embed=mc)


async def minecraft_embed():
    mc = discord.Embed(title="Minecraft server help!", description="", color=discord.Color.green())
    mc.description += f"To get a rank on the minecraft server do **/shop** and you can right click on the rank you want to buy, if you have enough money to buy it. Keep in mind that this is in game money not real money.\n"
    mc.description += f"\n"
    mc.description += f"To set a home do **/sethome (home name)** and it will set your home. To go to a home that you already made do **/home (home name)** and you will teleport there.\n"
    mc.description += f"\n"
    mc.description += f"To get back to spawn at any time do **/spawn**\n"
    mc.description += f"\n"
    mc.description += f"To get to the lobby/spawn of any game do **/warp (warp name)** the warps to get to a spawn/lobby are **/warp FactionSpawn**, **/warp PvPLobby**, **/warp SandBoxSpawn** and **/warp SMPspawn**\n"
    mc.set_footer(text="I hope this helped, if it didnt please open a ticket in the **help-tickets** channel",
                  icon_url=bot.user.avatar_url)
    return mc


@bot.command()
async def discord_help(ctx):
    disc_help = await discord_help_embed()
    await ctx.send(embed=disc_help)


async def discord_help_embed():
    disc_help = discord.Embed(title="Discord server help!", description="", color=discord.Color.green())
    disc_help.description += f"To get a rank on the discord server, do **{bot.command_prefix}shop** and buy your rank, keep in mind you need to have enough money to buy it.\n"
    disc_help.description += f"\n"
    disc_help.description += f"To suggest something do **{bot.command_prefix}suggest (suggestion)** and you suggestion will be sent.\n"
    disc_help.description += f"\n"
    disc_help.description += f"To earn money, you will have to do **{bot.command_prefix}beg** and to earn money if a fun way, if you already have money, you can do **{bot.command_prefix}gamble (amount)**\n"
    disc_help.set_footer(text="I hope this helped, if it didn't please open a ticket in the **help-tickets** channel",
                         icon_url=bot.user.avatar_url)
    return disc_help


@bot.command()
async def faq(ctx):
    FAQ = await faq_embed()
    await ctx.send(embed=FAQ)


async def faq_embed():
    FAQ = discord.Embed(title="this is the FAQ section, you can read frequently asked questions here.", description="",
                        color=discord.Color.green())
    FAQ.description += f"How do i get a vip/mvp rank? : To get a VIP or MVP rank you must go on the minecraft server and do **/shop** Once you do that command you will find the ranks and their prices, remember that they are in game currency and not real life money.\n"
    FAQ.description += f"\n"
    FAQ.description += f"How do i open a ticket? : to open a ticket you can go to #help-tickets and react to the message there to open a ticket.\n"
    FAQ.description += f"\n"
    FAQ.description += f"What do we do here? : This is a server for anyone who is homeschooled, feel free to invite your friends. To get an invite for your friends just open a ticket and you will get an invite that can invite one(1) person.\n"
    FAQ.description += f"\n"
    FAQ.description += f"How do i get the edgy role? : to get the edgy role just @ mention a staff member or moderator, and they can give you the role.\n"
    FAQ.description += f"\n"
    FAQ.description += f"How do i get the YouTuber rank? : To get the YouTuber rank you must have 50 subscribers or more, as said in the rules.\n"
    FAQ.set_footer(text="I hope this helped, if it didn't please open a ticket in the **help-tickets** channel",
                   icon_url=bot.user.avatar_url)
    return FAQ


@commands.has_role("-------Staff Team-------")
@bot.command()
async def moderator_help(ctx):
    moderator = await moderator_help_embed()
    await ctx.send(embed=moderator)


async def moderator_help_embed():
    moderator = discord.Embed(title="Quick Help!", description="", color=discord.Color.green())
    moderator.description += f"**{bot.command_prefix}ticket_config** : Displays configuration of the tickets.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}configure_ticket** : sets up the ticket reaction message by configuring the ticket.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}set_welcome_channel** : sets the welcome channel of the server.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}set_goodbye_channel** : sets the goodbye channel of the server.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}warn (member) (reason)** : warns a member for an infraction of the rules.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}warnings (member)** : provides a list of warnings from that member, with who gave the warning, and what the warning was for.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}mute (@member)** : mutes the mentioned member\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}unmute (member ID) or (username + gamertag with no space between them)** : unmutes a muted member.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}purge (amount)** : deletes the amount of messages in the command. remember to put 1 number more than the amount of messages you want to delete, because the bot needs to delete the purge message too.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}kick (@member)** : requires trialstaff or higher to preform this command. This command kicks a member from the server.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}ban (@member)** : bans the member mentioned.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}unban (member ID) or (username and gamertag)** : unbans the member with the ID you sent in the command.\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}set_reaction (role) (message id) (emoji)**: set a reaction role\n"
    moderator.description += f"\n"
    moderator.description += f"**{bot.command_prefix}reset_snum (number)**: set the number of suggestions, next suggestion will be this plus 1\n"
    moderator.set_footer(text="Please note that normal members do not have permission to use these commands.",
                         icon_url=bot.user.avatar_url)
    return moderator


# ticket system


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    

    for role, msgid, emoji in sConfig['reaction']:
        if msgid == payload.message_id and emoji == payload.emoji.name:
            await payload.member.add_roles(guild.get_role(role))

    if payload.member.id != bot.user.id and str(payload.emoji) == u"\U0001F3AB":
        msg_id, channel_id, category_id = bot.ticket_configs[payload.guild_id]

        if payload.message_id == msg_id:
            guild = bot.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id)

            ticket_num = 1 if len(category.channels) == 0 else int(category.channels[-1].name.split("-")[1]) + 1
            ticket_channel = await category.create_text_channel(f"ticket-{payload.member.display_name}",
                                                                topic=f"A ticket for {payload.member.display_name}.",
                                                                permission_synced=True)

            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            await ticket_channel.send(
                f"{payload.member.mention} Thank you for creating a ticket! Use **&close** to close your ticket. The staff team (<@&705864664302747751>) will be with you shortly.")

            try:
                await bot.wait_for("message", check=lambda
                    m: m.channel == ticket_channel and m.author == payload.member and m.content == "&close",
                                   timeout=1000)

            except asyncio.TimeoutError:
                await ticket_channel.delete()

            else:
                await ticket_channel.delete()


@commands.has_role("-------Staff Team-------")
@bot.command()
async def close(ctx):
    await ctx.channel.delete()


@commands.has_role("ADMIN")
@bot.command()
async def configure_ticket(ctx, msg: discord.Message = None, category: discord.CategoryChannel = None):
    if msg is None or category is None:
        await ctx.channel.send("Failed to configure the ticket as an argument was not given or was invalid.")
        return

    bot.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id]  # this resets the configuration

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()

    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)

    await msg.add_reaction(u"\U0001F3AB")
    await ctx.channel.send("Successfully configured the ticket system.")


@commands.has_role("-------Staff Team-------")
@bot.command()
async def ticket_config(ctx):
    try:
        msg_id, channel_id, category_id = bot.ticket_configs[ctx.guild.id]

    except KeyError:
        await ctx.channel.send("You have not configured the ticket system yet.")

    else:
        embed = discord.Embed(title="Ticket system configurations.", color=discord.Color.green())
        embed.description = f"**Reaction message ID** : {msg_id}\n"
        embed.description += f"**Ticket category ID** : {category_id}\n\n"

        await ctx.channel.send(embed=embed)


# welcome and leave messages

@bot.event
async def on_member_join(member):
    if botdata.welcome_channel == None:        
        for channel in ctx.guild.channels:
            if channel.name == sConfig['welcome']:
                botdata.welcome_channel = channel
    await botdata.welcome_channel.send(
        f"Welcome! {member.mention} Please be sure to read the rules in the rules channel, and check out the rules in our website: https://homeschool-club.weebly.com/rules.html")




@bot.event
async def on_member_remove(member):
    if botdata.goodbye_channel == None:
        for channel in ctx.guild.channels:
            if channel.name == sConfig['welcome']:
                botdata.welcome_channel = channel
    await botdata.goodbye_channel.send(f"Goodbye {member.mention}")



@commands.has_role("-------Staff Team-------")
@bot.command()
async def set_welcome_channel(ctx, channel_name=None):
    if channel_name != None:
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.welcome_channel = channel
                sConfig['welcome'] = channel_name
                sConfig.sync()
                await ctx.channel.send(f"Welcome channel has been set to: {channel.name}")
                await channel.send("This is the new welcome channel!")


    else:
        await ctx.channel.send("You didnt include the name of a welcome channel.")


@commands.has_role("-------Staff Team-------")
@bot.command()
async def set_goodbye_channel(ctx, channel_name=None):
    if channel_name != None:
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.goodbye_channel = channel
                sConfig['goodbye'] = channel_name
                sConfig.sync()
                await ctx.channel.send(f"Goodbye channel has been set to: {channel.name}")
                await channel.send("This is the new goodbye channel!")

    else:
        await ctx.channel.send("You didnt include the name of a goodbye channel.")


# reaction roles


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    for role, msgid, emoji in sConfig['reaction']:
        if msgid == payload.message_id and emoji == payload.emoji.name:
            await bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(guild.get_role(role))


@commands.has_role("ADMIN")
@bot.command()
async def set_reaction(ctx, role: discord.Role = None, msg: discord.Message = None, emoji=None):
    if role != None and msg != None and emoji != None:
        await msg.add_reaction(emoji)
        sConfig.setdefault('reaction', []).append((role.id, msg.id, emoji))
        sConfig.sync()
    else:
        await ctx.send("Invalid arguments.")


# bot warning and moderation system.


@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}


@commands.has_role("-------Staff Team-------")
@bot.command()
async def warn(ctx, member: discord.Member = None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found, or you forgot to provide one.")

    if reason is None:
        return await ctx.send("Please provide a reason for warning this member.")

    try:
        first_warning = False
        bot.warnings[ctx.guild.id][member.id][0] += 1
        bot.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))



    except KeyError:
        first_warning = True
        bot.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = bot.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id} warnings.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")


@commands.has_role("Staff")
@bot.command()
async def warnings(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("The provided member could not be found, or you forgot to provide one.")

    embed = discord.Embed(title=f"displaying warnings for {member.name}", description="", color=discord.Color.red())
    try:
        i = 1
        for admin_id, reason in bot.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**warnings {1}** given by {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError:  # this person has no warnings
        await ctx.send("This user has no warnings.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount=2):
    await ctx.channel.purge(limit=amount)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided."):
    await ctx.send(member.mention + " has been kicked.")
    await member.kick(reason=reason)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided."):
    await ctx.send(member.mention + " has been banned.")
    await member.ban(reason=reason)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_disc, = member.split('#')

    for banned_entry in banned_users:
        user = banned_entry.user
        if (user.name, user.discriminator,) == (member_name, member_disc):
            await ctx.guild.unban(user)
            await ctx.send(member_name + " has been unbanned.")
            return

        await ctx.send(member + " was not found.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member):
    muted_role = ctx.guild.get_role(708075939019489360)
    member_role = ctx.guild.get_role(695742663256834141)

    await member.remove_roles(member_role)
    await member.add_roles(muted_role)

    await ctx.send(member.mention + " has been muted.")


@commands.has_role("-------Staff Team-------")
@bot.command()
async def unmute(ctx, member: discord.Member):
    muted_role = ctx.guild.get_role(708075939019489360)
    member_role = ctx.guild.get_role(695742663256834141)

    await member.add_roles(member_role)
    await member.remove_roles(muted_role)

    await ctx.send(member.mention + " has been unmuted.")


# suggestion command

@commands.has_role("-------Staff Team-------")
@bot.command()
async def set_suggestion_channel(ctx, channel_name=None):
    if channel_name != None:
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.suggestion_channel = channel
                sConfig['suggestion'] = channel_name
                await ctx.channel.send(f"Suggestion channel was set to: {channel.name}")
                await channel.send("This is the new suggestion channel!")


@bot.command()
async def suggest(ctx, *, suggestion):
    sConfig['snum'] += 1
    suggest = discord.Embed(
        title="Suggestion #"+str(sConfig['snum']),
        description=f"{suggestion}",
        color=0,
        timestamp=ctx.message.created_at
    )
    suggest.set_footer(
        text='Please react with a thumbs up or a thumbs down if you like this idea. Requested by {} | ID-{}'.format(
            ctx.message.author, ctx.message.author.id))
    if botdata.suggestion_channel == None:        
        for channel in ctx.guild.channels:
            if channel.name == sConfig['suggestion']:
                botdata.suggestion_channel = channel
    msg = await botdata.suggestion_channel.send(embed=suggest)
    await ctx.message.delete()
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    

@commands.has_role("-------Staff Team-------")
@bot.command()
async def reset_snum(ctx, num):
    try:
        sConfig['snum'] = int(num)
    except ValueError:
        await ctx.send('Invalid number.')
        return
    await ctx.send('Set succesfully.')

# economy system


mainshop = [{"name": "VIP", "price": 50000, "description": "VIP rank"},
            {"name": "MVP", "price": 125000, "description": "MVP rank"},
            {"name": "ad", "price": 1000, "description": "Buy an ad for the advertisements channel"}]


@bot.command(aliases=['bal'])
async def balance(ctx):
    await open_account(ctx.author)
    user = ctx.author

    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    em = discord.Embed(title=f'{ctx.author.name} Balance', color=discord.Color.red())
    em.add_field(name="Wallet Balance", value=wallet_amt)
    em.add_field(name='Bank Balance', value=bank_amt)
    await ctx.send(embed=em)


# @bot.command()
# async def beg(ctx):
#   await open_account(ctx.author)
#   user = ctx.author
#
#   users = await get_bank_data()

#   earnings = random.randrange(21)

#   await ctx.send(f'{ctx.author.mention} Got {earnings} coins!!')

#   users[str(user.id)]["wallet"] += earnings

#   with open("mainbank.json", 'w') as f:
#       json.dump(users, f)


@bot.event
async def on_message(msg):
    await bot.process_commands(msg)
    user = msg.author
    if not user.bot:
        if msg.channel.name != 'spam' and msg.channel.name != 'bot-spam':
            await update_bank(user, +10)


@bot.command(aliases=['wd'])
async def withdraw(ctx, amount=None):
    await open_account(ctx.author)
    if amount == None:
        await ctx.send("Please enter the amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[1]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return

    await update_bank(ctx.author, amount)
    await update_bank(ctx.author, -1 * amount, 'bank')
    await ctx.send(f'{ctx.author.mention} You withdrew {amount} coins')


@bot.command(aliases=['dp'])
async def deposit(ctx, amount=None):
    await open_account(ctx.author)
    if amount == None:
        await ctx.send("Please enter the amount")
        return
    if amount == 'all':
        amount = bal[0]
    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return

    await update_bank(ctx.author, -1 * amount)
    await update_bank(ctx.author, amount, 'bank')
    await ctx.send(f'{ctx.author.mention} You deposited {amount} coins')


@bot.command(aliases=['sm'])
async def send(ctx, member: discord.Member, amount=None):
    await open_account(ctx.author)
    await open_account(member)
    if amount == None:
        await ctx.send("Please enter the amount")
        return

    bal = await update_bank(ctx.author)
    if amount == 'all':
        amount = bal[0]

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return

    await update_bank(ctx.author, -1 * amount, 'bank')
    await update_bank(member, amount, 'bank')
    await ctx.send(f'{ctx.author.mention} You gave {member} {amount} coins')


# @bot.command(aliases=['rb'])
# async def rob(ctx, member: discord.Member):
#    await open_account(ctx.author)
#    await open_account(member)
#    bal = await update_bank(member)

#    if bal[0] < 100:
#        await ctx.send('It is useless to rob him :(')
#        return

#    earning = random.randrange(0, bal[0])

#    await update_bank(ctx.author, earning)
#    await update_bank(member, -1 * earning)
#    await ctx.send(f'{ctx.author.mention} You robbed {member} and got {earning} coins')


@bot.command(aliases=['cf'])
async def coinflip(ctx, amount=None, coin=None):
    await open_account(ctx.author)
    if amount == None:
        await ctx.send("Please enter the amount")
        return
    if coin == None:
        await ctx.send("Please enter heads or tails")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return
    if coin != 'heads' and coin != 'h' and coin != 'tails' and coin != 't':
        await ctx.send('You must enter a valid coinflip option!')
        return

    coinFlip = random.choice(['heads', 'tails'])
    randomness = random.choice(['fail', 'win', 'win', 'win', 'win', 'win', 'win', 'win'])
    if randomness == 'fail':
        if coin == 'heads' or coin == 'h':
            coinFlip = 'tails'
        else:
            coinFlip = 'heads'
    await ctx.send('The coin was ' + coinFlip + '.')
    if coinFlip == 'heads':
        if coin == 'h' or coin == 'heads':
            await ctx.send('You won ' + str(amount) + ' coins.')
            await update_bank(ctx.author, amount)
        else:
            await ctx.send('You lost ' + str(amount) + ' coins.')
            await update_bank(ctx.author, -amount)
    else:
        if coin == 't' or coin == 'tails':
            await ctx.send('You won ' + str(amount) + ' coins.')
            await update_bank(ctx.author, amount)
        else:
            await ctx.send('You lost ' + str(amount) + ' coins.')
            await update_bank(ctx.author, -amount)


@bot.command()
async def gamble(ctx, amount=None):
    await open_account(ctx.author)
    if amount == None:
        await ctx.send("Please enter the amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return
    final = []
    # for i in range(3):
    #    a = random.choice(['X', 'O', 'Q', '4', ':coin:'])

    #    final.append(a)
    for i in range(9):
        a = random.choice([':gem:', ':coin:', ':green_circle:', ':orange_circle:', ':blue_circle:'])
        final.append(a)

    await ctx.send(final[0] + final[1] + final[2])
    await ctx.send(final[3] + final[4] + final[5])
    await ctx.send(final[6] + final[7] + final[8])

    percent = 0
    for i in final:
        for i2 in final:
            if i == i2:
                percent += 0.04
    await update_bank(ctx.author, -amount)
    amount = int(percent * amount)
    await update_bank(ctx.author, amount)
    await ctx.send(f'You got ' + str(amount) + f' back.')

    # if final[0] == final[1] or final[1] == final[2] or final[0] == final[2]:
    #    await update_bank(ctx.author, 2 * amount)
    #    await ctx.send(f'You won :) {ctx.author.mention}')
    # else:
    #    await update_bank(ctx.author, -1 * amount)
    #    await ctx.send(f'You lose :( {ctx.author.mention}')


@bot.command()
async def roll(ctx, amount: str = None, bet: int = None):
    roll = random.randint(1, 6)
    won = 'lost '
    try:
        amount = int(amount)
    except Exception:
        await ctx.send(':game_die: You rolled a ' + str(roll))
        return

    await open_account(ctx.author)

    bal = await update_bank(ctx.author)

    if amount > bal[0]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return
    if bet > 6:
        await ctx.send('You can only bet numbers on the dice.')
        return

    if roll == bet:
        won = 'won '
        amount = amount * 5
        await update_bank(ctx.author, +amount)
    else:
        await update_bank(ctx.author, -amount)

    await ctx.send(':game_die: You rolled a ' + str(roll) + ' and ' + won + str(amount) + ' coins.')
    print('rolled')


@bot.command()
async def shop(ctx):
    em = discord.Embed(title="Shop")

    for item in mainshop:
        name = item["name"]
        price = item["price"]
        desc = item["description"]
        em.add_field(name=name, value=f"${price} | {desc}")

    await ctx.send(embed=em)


@bot.command(pass_context=True)
async def buy(ctx, item, amount=1):
    await open_account(ctx.author)

    res = await buy_this(ctx.author, item, amount)
    vip = True
    if item == 'mvp':
        member = ctx.message.author
        roles = ctx.guild.roles
        role = discord.utils.get(roles, name="VIP")
        if not role in member.roles:
            await ctx.send("You don't have VIP yet!")
            vip = False
            return
    if not res[0]:
        if res[1] == 1:
            await ctx.send("That Object isn't there!")
            return
        if res[1] == 2:
            await ctx.send(f"You don't have enough money in your wallet to buy {amount} {item}")
            return
    if res[0]:
        if item.lower() == 'vip':
            member = ctx.message.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="VIP")
            await member.add_roles(role)
        elif item.lower() == 'mvp' and vip == True:
            member = ctx.message.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="MVP")
            await member.add_roles(role)
        elif item.lower() == 'ad':
            member = ctx.message.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="ad")
            await member.add_roles(role)
    await ctx.send(f"You just bought {amount} {item}")


@bot.command()
async def bag(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    try:
        bag = users[str(user.id)]["bag"]
    except:
        bag = []

    em = discord.Embed(title="Bag")
    for item in bag:
        name = item["item"]
        amount = item["amount"]

        em.add_field(name=name, value=amount)

    await ctx.send(embed=em)


async def buy_this(user, item_name, amount):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            price = item["price"]
            break

    if name_ == None:
        return [False, 1]

    cost = price * amount

    users = await get_bank_data()

    bal = await update_bank(user)

    if bal[0] < cost:
        return [False, 2]

    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt + amount
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index += 1
        if t == None:
            obj = {"item": item_name, "amount": amount}
            users[str(user.id)]["bag"].append(obj)
    except:
        obj = {"item": item_name, "amount": amount}
        users[str(user.id)]["bag"] = [obj]

    with open("mainbank.json", "w") as f:
        json.dump(users, f)

    await update_bank(user, cost * -1, "wallet")

    return [True, "Worked"]


@bot.command()
async def sell(ctx, item, amount=1):
    await open_account(ctx.author)

    res = await sell_this(ctx.author, item, amount)

    if not res[0]:
        if res[1] == 1:
            await ctx.send("That Object isn't there!")
            return
        if res[1] == 2:
            await ctx.send(f"You don't have {amount} {item} in your bag.")
            return
        if res[1] == 3:
            await ctx.send(f"You don't have {item} in your bag.")
            return
    if res[0]:
        if item.lower() == 'vip':
            member = ctx.message.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="VIP")
            await member.remove_roles(role)
        elif item.lower() == 'mvp':
            member = ctx.message.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="MVP")
            await member.remove_roles(role)
        elif item.lower() == 'ad':
            member = ctx.message.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="ad")
            await member.remove_roles(role)
    await ctx.send(f"You just sold {amount} {item}.")


async def sell_this(user, item_name, amount, price=None):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            if price == None:
                price = 0.7 * item["price"]
            break

    if name_ == None:
        return [False, 1]

    cost = price * amount

    users = await get_bank_data()

    bal = await update_bank(user)

    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt - amount
                if new_amt < 0:
                    return [False, 2]
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index += 1
        if t == None:
            return [False, 3]
    except:
        return [False, 3]

    with open("mainbank.json", "w") as f:
        json.dump(users, f)

    await update_bank(user, cost, "wallet")

    return [True, "Worked"]


@bot.command(aliases=["lb"])
async def leaderboard(ctx, x=10):
    users = await get_bank_data()
    leader_board = {}
    total = []
    for user in users:
        name = int(user)
        total_amount = users[user]["wallet"] + users[user]["bank"]
        leader_board[total_amount] = name
        total.append(total_amount)

    total = sorted(total, reverse=True)

    em = discord.Embed(title=f"Top {x} Richest People",
                       description="This is decided on the basis of raw money in the bank and wallet",
                       color=discord.Color(0xfa43ee))
    index = 1
    for amt in total:
        id_ = leader_board[amt]
        member = bot.get_user(id_)
        name = member.name
        em.add_field(name=f"{index}. {name}", value=f"{amt}", inline=False)
        if index == x:
            break
        else:
            index += 1

    await ctx.send(embed=em)


async def open_account(user):
    users = await get_bank_data()

    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0
        users[str(user.id)]["bank"] = 0

    with open('mainbank.json', 'w') as f:
        json.dump(users, f)

    return True


async def get_bank_data():
    with open('mainbank.json', 'r') as f:
        users = json.load(f)

    return users


async def update_bank(user, change=0, mode='wallet'):


    users = await get_bank_data()

    users[str(user.id)][mode] += change

    with open('mainbank.json', 'w') as f:
        json.dump(users, f)
    bal = users[str(user.id)]['wallet'], users[str(user.id)]['bank']
    return bal


# fun commands
@bot.command(aliases=["8b"],name="8ball")
async def _8ball(ctx):
    answer = random.choice(['No', 'Probably not', 'It\'s possible', 'Maybe', 'Concentrate and ask again',  'Possibly', 'Probably', 'Very likely', 'Almost certainly', 'Definitely', 'No way'])
    await ctx.send('🎱 | %s, **%s**' % (answer, ctx.message.author.display_name))

# bot token
def get_token():
    with open(f"token.txt", mode="a") as temp:
        pass

    with open(f"token.txt", mode="r") as file:
        lines = file.readlines()
        i = 0
        for line in lines:
            if line == '' and i == 0:
                print('Please put your bot token in \'token.txt\'. ')
                sys.exit()
            elif i == 0:
                return line


bot.run(str(get_token()))