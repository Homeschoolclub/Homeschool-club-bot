# imports
import asyncio, shelve, aiofiles, discord, discord.utils, json, random, sys, datetime, string

from discord.ext import commands, tasks
from itertools import cycle
from time import timezone
from discord import *
from music import Player
#from reactionmenu import ButtonsMenu, ComponentsButton
from mcstatus import MinecraftServer
from dislash import *


# main bot setup
# set variables that might need editing
verText = '''Version 2.0.0 (SLASH COMMANDS! Full changelog: Post announcement embed commands (just like suggestions)
Pin qotds
Ping mc server 
Fun fact command [delayed till next update sadly]
Clear queue on leave
Change help menus to use actually good gui
Poll command
Re enabled rob command but with a chance of losing
Slash commands
Fix starboard
add easter egg
add 'add qotd' command
redo every command with the new slash commands gui)'''
qotdH = 18 # Runs qotd in utc
qotdM = 25
robCooldown = 5
guildID =  831638462951456789 # if this isn't set qotd will not work
tonesList = {'s': 'sarcastic', 'j': 'joking', 'hj': 'half-joking', 'srs': 'serious', 'p': 'platonic', 'r': 'romantic',
             'l': 'lyrics', 'ly': 'lyrics', 't': 'teasing', 'nm': 'not mad or upset', 'nc': 'negative connotation',
             'neg': 'negative connotation', 'pc': 'positive connotation', 'pos': 'positive connotation',
             'lh': 'lighthearted', 'nbh': 'nobody here', 'm': 'metaphorically', 'li': 'literally',
             'rh': 'rhetorical question', 'gen': 'genuine question', 'hyp': 'hyperbole', 'c': 'copypasta',
             'th': 'threat', 'cb': 'clickbait', 'f': 'fake', 'g': 'genuine'}  # todo: add more tones
tonesList_enabled = True  # change to false to disable tone detecting
actions = {'punch': ['punched', 'https://tenor.com/view/punchy-one-punch-man-anime-punch-fight-gif-16189288'],
           'hi': ['said hi to', 'https://tenor.com/view/puppy-dog-wave-hello-hi-gif-13974826',
                  'https://tenor.com/view/hello-wave-cute-anime-cartoon-gif-7537923',
                  'https://tenor.com/view/hello-there-private-from-penguins-of-madagascar-hi-wave-hey-there-gif-16043627',
                  'https://tenor.com/view/cute-animals-mochi-mochi-peach-cat-goma-cat-wave-gif-17543358',
                  'https://tenor.com/view/baby-yoda-baby-yoda-wave-baby-yoda-waving-hi-hello-gif-15975082',
                  'https://tenor.com/view/hi-friends-baby-goat-saying-hello-saying-hi-hi-neighbor-gif-14737423',
                  'https://tenor.com/view/mr-bean-funny-hello-hi-wave-gif-3528683',
                  'https://tenor.com/view/yo-anime-hi-promised-neverland-gif-13430927'],
           'run': ['ran away from', 'https://giphy.com/gifs/justin-g-run-away-fast-3o7ZetIsjtbkgNE1I4'],
           'hug': ['hugged', 'https://giphy.com/gifs/loading-virtual-hug-ZBQhoZC0nqknSviPqT'],
           'yeet': ['yeeted', 'https://giphy.com/gifs/memecandy-J1ABRhlfvQNwIOiAas'],
           'highfive': ['high-fived', 'https://giphy.com/gifs/highfive-hifi-3oKIPnpZgBCniqStS8'],
           'yeet': ['yeeted', 'https://tenor.com/view/yeet-lion-king-simba-rafiki-throw-gif-16194362']}
# initialize files
sConfig = shelve.open('config', writeback=True)
try:
    print('Successfully loaded welcome channel as #' + sConfig['welcome'])
except KeyError:
    print('Failed to load welcome channel.')
try:
    print('Successfully loaded suggestion channel as #' + sConfig['suggestion'])
except KeyError:
    print('Failed to load suggestion channel.')
try:
    print('Successfully loaded starboard as #' + sConfig['star'])
except KeyError:
    print('Failed to load starboard.')
try:
    print('Successfully loaded logs channel as #' + sConfig['logs'])
except KeyError:
    print('Failed to load logs channel.')
try:
    print('Successfully loaded accepted/denied suggestions channel as #' + sConfig['suggestion2'])
except KeyError:
    print('Failed to load accepted/denied suggestions channel.')
try:
    print('Successfully loaded qotd channel as #' + sConfig['qotd'])
except KeyError:
    print('Failed to load qotd channel.')
# load permissions
intents = discord.Intents.default()
intents.members = True
intents.messages = True
# load status
status = cycle(
    ['Try )help', 'Prefix - )'])
filteredMessage = None
usersOnRobCooldown = {}

@tasks.loop(seconds=5)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))


# initialize
bot = commands.Bot(command_prefix="&", help_command=None, intents=intents)
#ButtonsMenu.initialize(bot)
slash = SlashClient(bot, show_warnings = True)
guilds = [831638462951456789, 851233957571067914]
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

    await qotd(self=bot)
    print("Your bot is ready to be used.")





class BotData:
    def __init__(self):
        self.welcome_channel = None
        self.goodbye_channel = None
        self.suggestion_channel = None
        self.starboard_channel = None
        self.suggestion_channel_two = None
        self.logs_channel = None
        self.qotd_channel = None


botdata = BotData()
# load reaction roles, done later because they reference bot variables
# also load suggestion number
try:
    bot.reaction_roles = sConfig['reaction']
except KeyError:
    sConfig['reaction'] = []
try:
    suggestionNumber = sConfig['snum']
except KeyError:
    sConfig['snum'] = 0
try:
    sentQotds = sConfig['qnum']
except KeyError:
    sConfig['qnum'] = 0
    sentQotds = 0

# test commands

@slash.command(  
    description="Tests the bot"
)
async def test(inter):
    await inter.reply("Your test worked! " + str(inter.author))




@slash.command(
    description="Gets a user's info",
    options=[
        Option("user", "Enter the user", Type.USER)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def user_info(inter, user = None):
    user = user or inter.author
    await inter.reply(user.name)


# ver command
@slash.command(   
    description="Replies with the version"
)
async def ver(ctx):
    await ctx.reply(verText)


# help commands


@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        await message.channel.send(f'Run {bot.command_prefix}help for help.')
    await bot.process_commands(message)

# the docs you're looking for are https://github.com/Defxult/reactionmenu/blob/335c5f838e793cc2ea46bb02d5c2a44da2c99bb8/README.md unless you updated, in which case idk somewhere near there
# Removed because slash commands dont need help
# A shame because the help gui looked super cool
# but
# it had to be done
# - j5155, 6/25/2021
""" @slash.command( 
       
    description="Sends a help GUI"
)
async def help(ctx):
    helpChannel = ctx.channel
    ctx.reply('Help loading...')
    basicHelp = discord.Embed(title="Basic Help!", description="", color=discord.Color.green())
    basicHelp.description += f"**{bot.command_prefix}test** : Tests to make sure the bot is working properly.\n"
    basicHelp.description += f"\n"
    basicHelp.description += f"**{bot.command_prefix}help** : The help command gives you a list of commands you can do with ths bot. you can also @ mention the bot in a message to get a list of commands.\n"
    basicHelp.description += f"\n"
    basicHelp.description += f"**{bot.command_prefix}moderator_help** : provides a list of moderator commands. Only staff members have access to this command.\n"
    basicHelp.description += f"\n"
    basicHelp.description += f"**{bot.command_prefix}quick_help** : gets a quick help message.\n"
    basicHelp.description += f"\n"
    basicHelp.description += f"**{bot.command_prefix}ver** : responds with the bot version and latest feature.\n"
    basicHelp.description += f"\n"
    basicHelp.description += f"**{bot.command_prefix}suggest (suggestion)** : suggests something in the suggestion channel.\n"
    basicHelp.set_footer(text="Here is a list of commands the bot can do!", icon_url=bot.user.avatar_url)


    ecoHelp = discord.Embed(title="Economy Help!", description="", color=discord.Color.green())
    ecoHelp.description += f"**{bot.command_prefix}shop** : lists the buyable items you can get.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}bal** : lists your balance.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}withdraw (amount)** : lets you take however much money you want out of your bank account.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}deposit (amount)** : lets you put however much money you want into your back account.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}buy (item)** : lets you buy the item you want from the shop/\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}gamble (amount)** : gambles the amount of money you want to gamble.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}bag** : lists the items you have bought from the store.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}sell (item)** : sells an item back to the store for money, you will not get all the money you used to buy the item back.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}send (user) (amount)** : sends specified amount of money to specified user.\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}coinflip (amount) (face) ** : bets on flipping a coin\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}roll (amount) (face) ** : bets on rolling a dice, run without an amount to not bet\n"
    ecoHelp.description += f"\n"
    ecoHelp.description += f"**{bot.command_prefix}leaderboard (amount of players you want listed)** : lists the specified amount of players based on who has the most money.\n"
    ecoHelp.set_footer(text="Here is a list of commands the bot can do!", icon_url=bot.user.avatar_url)

    funHelp = discord.Embed(title="Fun Help!", description="", color=discord.Color.green())
    funHelp.description += f"**{bot.command_prefix}8ball** : Responds like an 8ball. You can also type **{bot.command_prefix}8b**\n"
    funHelp.description += f"\n"
    funHelp.description += f"**{bot.command_prefix}action (action) (user)** : Responds with a gif of your action. You can also type **{bot.command_prefix}a**\n"
    funHelp.description += f"\n"
    funHelp.description += f"**{bot.command_prefix}poll (description)** : Responds with a poll of your action.\n"
    funHelp.set_footer(text="Here is a list of commands the bot can do!", icon_url=bot.user.avatar_url)

    musicHelp = discord.Embed(title="Music Help!", description="", color=discord.Color.green())
    musicHelp.description += f"**{bot.command_prefix}join** : Makes the bot join the music channel\n"
    musicHelp.description += f"\n"
    musicHelp.description += f"**{bot.command_prefix}leave** : Makes the bot leave the channel\n"
    musicHelp.description += f"\n"
    musicHelp.description += f"**{bot.command_prefix}play (song name, or link)** : Plays the song you requested\n"
    musicHelp.description += f"\n"
    musicHelp.description += f"**{bot.command_prefix}skip** : Adds a vote skip to the chat to vote on the song being skipped\n"
    musicHelp.description += f"\n"
    musicHelp.description += f"**{bot.command_prefix}queue** : Lists the songs in a queue\n"
    musicHelp.description += f"\n"
    musicHelp.description += f"**{bot.command_prefix}search (song name)** : Will provide you with links to the song you want to play (the first link is what the bot would have played)\n"
    musicHelp.set_footer(text="Here is a list of commands the bot can do!", icon_url=bot.user.avatar_url)
    
    mcHelp = discord.Embed(title="Minecraft Help!", description="", color=discord.Color.green())
    mcHelp.description += f"**{bot.command_prefix}ping (ip)** : Replies with info about a Java server, by default pings the official HSC one\n"
    mcHelp.set_footer(text="Here is a list of commands the bot can do!", icon_url=bot.user.avatar_url)

    helpMenu = ButtonsMenu(ctx, back_button='◀️', next_button='▶️', menu_type=ButtonsMenu.TypeEmbed) 
    helpMenu.add_page(basicHelp)
    helpMenu.add_page(ecoHelp)
    helpMenu.add_page(funHelp)
    helpMenu.add_page(musicHelp)
    helpMenu.add_page(mcHelp)
    # prev and next
    npb = ComponentsButton(label='Previous', style = 1, custom_id=ComponentsButton.ID_PREVIOUS_PAGE)
    prpb = ComponentsButton(label='Next', style = 1, custom_id=ComponentsButton.ID_NEXT_PAGE)
    # first and last pages
    fpb = ComponentsButton(label='First', style = 3, custom_id=ComponentsButton.ID_GO_TO_FIRST_PAGE)
    lpb = ComponentsButton(label='Last', style = 3, custom_id=ComponentsButton.ID_GO_TO_LAST_PAGE)
    # go to page
    gtpb = ComponentsButton(label='Choose', style = 2, custom_id=ComponentsButton.ID_GO_TO_PAGE)
    # end session
    #esb = ComponentsButton(label='End', style = 4, custom_id=ComponentsButton.ID_END_SESSION)
    helpMenu.add_button(npb)
    helpMenu.add_button(prpb)
    helpMenu.add_button(fpb)
    helpMenu.add_button(lpb)
    helpMenu.add_button(gtpb)
    #helpMenu.add_button(esb)


    await helpMenu.start(send_to=helpChannel) """ 


@slash.command(
       
    description="Gets quick help"
)
async def quick_help(ctx):
    info = await info_embed()
    await ctx.reply(embed=info)


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


@slash.command(
       
    description="Gets minecraft help"
)
async def minecraft_help(ctx):
    mc = await minecraft_embed()
    await ctx.reply(embed=mc)


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


@slash.command(
       
    description="Gets discord help"
)
async def discord_help(ctx):
    disc_help = await discord_help_embed()
    await ctx.reply(embed=disc_help)


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


@slash.command(
       
    description="Gets a FAQ"
)
async def faq(ctx):
    FAQ = await faq_embed()
    await ctx.reply(embed=FAQ)


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


# Removed because slash commands dont need help
# A shame because the help gui looked super cool
# but
# it had to be done
# - j5155, 6/25/2021
''' @slash.command(
       
    description="Gets moderator help",
)
@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
async def moderator_help(ctx):
    await ctx.reply('Help menu loading...')
    moderator1 = discord.Embed(title="Basic Help!", description="", color=discord.Color.green())
    moderator1.description += f"**{bot.command_prefix}warn (member) (reason)** : warns a member for an infraction of the rules.\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}warnings (member)** : provides a list of warnings from that member, with who gave the warning, and what the warning was for.\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}mute (@member)** : mutes the mentioned member\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}unmute (member ID) or (username + gamertag with no space between them)** : unmutes a muted member.\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}purge (amount)** : deletes the amount of messages in the command. remember to put 1 number more than the amount of messages you want to delete, because the bot needs to delete the purge message too.\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}kick (@member)** : requires trialstaff or higher to preform this command. This command kicks a member from the server.\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}ban (@member)** : bans the member mentioned.\n"
    moderator1.description += f"\n"
    moderator1.description += f"**{bot.command_prefix}unban (member ID) or (username and gamertag)** : unbans the member with the ID you sent in the command.\n"
    moderator1.set_footer(text="Please note that normal members do not have permission to use these commands.",
                         icon_url=bot.user.avatar_url)
    moderator2 = discord.Embed(title='Suggestion Help!', description='', color=discord.Color.green())
    moderator2.description += f"**{bot.command_prefix}accept (reason)**: run this command while replying to a suggestion to move it to the decided suggestions channel\n"
    moderator2.description += f"\n"
    moderator2.description += f"**{bot.command_prefix}deny (reason)**: run this command while replying to a suggestion to move it to the decided suggestions channel\n"
    moderator2.description += f"\n"
    moderator2.description += f"**{bot.command_prefix}implement (reason)**: run this command while replying to a suggestion to move it to the decided suggestions channel\n"
    moderator2.set_footer(text="Please note that normal members do not have permission to use these commands.",
                         icon_url=bot.user.avatar_url)
    moderator3 = discord.Embed(title='Configuration Help!', description = '', color=discord.Color.green())
    moderator3.description += f"**{bot.command_prefix}ticket_config** : Displays configuration of the tickets.\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}configure_ticket** : sets up the ticket reaction message by configuring the ticket.\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}set_welcome_channel** : sets the welcome channel of the server.\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}set_goodbye_channel** : sets the goodbye channel of the server.\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}set_reaction (role) (message id) (emoji)**: set a reaction role\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}reset_snum (number)**: set the number of suggestions, next suggestion will be this plus 1\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}reset_qnum (number)**: set the number of posted qotds, next qotd will be this plus 1\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}set_decided_suggestion_channel (channel)**: set the channel for decided suggestions\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}set_logs_channel (channel)**: set the channel for modlogs\n"
    moderator3.description += f"\n"
    moderator3.description += f"**{bot.command_prefix}set_qotd_channel** : sets the qotd channel of the server.\n"

    moderator3.set_footer(text="Please note that normal members do not have permission to use these commands.",
                         icon_url=bot.user.avatar_url)
    moderator4 = discord.Embed(title='Music Help!', description = '', color=discord.Color.green())
    moderator4.description += f"**{bot.command_prefix}fskip** : Skips the current song that is playing.\n"
    moderator4.set_footer(text="Please note that normal members do not have permission to use these commands.",
                         icon_url=bot.user.avatar_url)


    modHelpMenu = ButtonsMenu(ctx, back_button='◀️', next_button='▶️', menu_type=ButtonsMenu.TypeEmbed) 
    modHelpMenu.add_page(moderator1)
    modHelpMenu.add_page(moderator2)
    modHelpMenu.add_page(moderator3)
    modHelpMenu.add_page(moderator4)
    # first and last pages
     # prev and next
    npb = ComponentsButton(label='Previous', style = 1, custom_id=ComponentsButton.ID_PREVIOUS_PAGE)
    prpb = ComponentsButton(label='Next', style = 1, custom_id=ComponentsButton.ID_NEXT_PAGE)
    # first and last pages
    fpb = ComponentsButton(label='First', style = 3, custom_id=ComponentsButton.ID_GO_TO_FIRST_PAGE)
    lpb = ComponentsButton(label='Last', style = 3, custom_id=ComponentsButton.ID_GO_TO_LAST_PAGE)
    # go to page
    gtpb = ComponentsButton(label='Choose', style = 2, custom_id=ComponentsButton.ID_GO_TO_PAGE)
    # end session
    #esb = ComponentsButton(label='End', style = 4, custom_id=ComponentsButton.ID_END_SESSION)
    modHelpMenu.add_button(npb)
    modHelpMenu.add_button(prpb)
    modHelpMenu.add_button(fpb)
    modHelpMenu.add_button(lpb)
    modHelpMenu.add_button(gtpb)


    await modHelpMenu.start() '''




# starboard

@slash.command(
       
    description="Sets the starboard channel",
    options=[
        Option("channel", "Enter the channel", Type.CHANNEL)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
async def set_starboard(ctx, channel=None):
    
    if channel != None:
        channel_name = channel.name
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.starboard_channel = channel
                sConfig['star'] = channel_name
                sConfig.sync()
                await ctx.reply(f"Starboad has been set to: {channel.name}")
                # await channel.send("This is the new welcome channel!")
                return
    await ctx.reply(
        "Invalid channel. Make sure you're sending a channel name (welcome), and not a channel link (#welcome).")


# ticket system


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)

    if payload.member.id != bot.user.id and str(
            payload.emoji) == '⭐':  # thanks https://stackoverflow.com/questions/65156352
        rguild = bot.get_guild(payload.guild_id)
        rchannel = bot.get_channel(payload.channel_id)
        rmessage = await rchannel.fetch_message(payload.message_id)
        reaction = discord.utils.get(rmessage.reactions, emoji=payload.emoji.name)
        if payload.member.id == rmessage.author.id:
            await reaction.remove(payload.member)
        elif reaction and reaction.count == 3:
            if botdata.starboard_channel == None:
                for channel in rguild.channels:
                    if channel.name == sConfig['star']:
                        botdata.starboard_channel = channel
            embed = discord.Embed(color=15105570)
            embed.set_author(name=rmessage.author.name, icon_url=rmessage.author.avatar_url)
            embed.add_field(name="Message Content", value=rmessage.content)
            embed.add_field(name='Link', value='[Jump!](%s)' % rmessage.jump_url)

            if len(reaction.message.attachments) > 0:
                embed.set_image(url=reaction.message.attachments[0].url)

            embed.set_footer(text=f" ⭐ {reaction.count} | # {reaction.message.channel.name}")
            embed.timestamp = datetime.datetime.utcnow()
            await botdata.starboard_channel.send(embed=embed)

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

def in_ticket():
    def predicate(inter):
        return inter.channel.category.name == 'Player Support'
    return check(predicate)

@in_ticket()
@slash.command(
       
    description="Closes a ticket",
)
async def close(ctx):
    if ctx.channel.category.name == 'Player Support':
        await ctx.reply('Channel closed.')
        await ctx.channel.delete()
    else:
        ctx.reply('This command only works in tickets.')


@slash_commands.has_role("Administrator")
@slash.command(
       
    description="Configure ticket",
    options=[
        Option("message_id", "Enter the id of the message", Type.STRING, required=True),
        Option("category", "Enter the category", Type.STRING, required=True)

        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def configure_ticket(ctx, msg: discord.Message = None, category: discord.CategoryChannel = None):
    if msg is None or category is None:
        await ctx.reply("Failed to configure the ticket as an argument was not given or was invalid.")
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
    await ctx.reply("Successfully configured the ticket system.")


@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="View ticket configuration",
)
async def ticket_config(ctx):
    try:
        msg_id, channel_id, category_id = bot.ticket_configs[ctx.guild.id]

    except KeyError:
        await ctx.reply("You have not configured the ticket system yet.")

    else:
        embed = discord.Embed(title="Ticket system configurations.", color=discord.Color.green())
        embed.description = f"**Reaction message ID** : {msg_id}\n"
        embed.description += f"**Ticket category ID** : {category_id}\n\n"

        await ctx.reply(embed=embed)


# welcome and leave messages




@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="Sets the welcome channel",
    options=[
        Option("channel", "Enter the channel", Type.CHANNEL, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def set_welcome_channel(ctx, channel=None):
    if channel != None:
        channel_name = channel.name
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.welcome_channel = channel
                sConfig['welcome'] = channel_name
                sConfig.sync()
                await ctx.reply(f"Welcome channel has been set to: {channel.name}")
                # await channel.send("This is the new welcome channel!")
                return

    await ctx.reply(
        "Invalid channel. Make sure you're sending a channel name (welcome), and not a channel link (#welcome).")


# Removed command because it does the same as welcome - j5155, 6/6/2021
# @commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
# @bot.command()
# async def set_goodbye_channel(ctx, channel_name=None):
#     if channel_name != None:
#         for channel in ctx.guild.channels:
#             if channel.name == channel_name:
#                 botdata.goodbye_channel = channel
#                 sConfig['goodbye'] = channel_name
#                 sConfig.sync()
#                 await ctx.channel.send(f"Goodbye channel has been set to: {channel.name}")
#                 await channel.send("This is the new goodbye channel!")
#
#     else:
#         await ctx.channel.send("You didnt include the name of a goodbye channel.")


# reaction roles


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    for role, msgid, emoji in sConfig['reaction']:
        if msgid == payload.message_id and emoji == payload.emoji.name:
            await bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(guild.get_role(role))


@slash_commands.has_role("ADMIN")
@slash.command(
       
    description="Sets a reaction role",
    options=[
        Option("role", "Enter the role", Type.STRING, required=True),
        Option("msg", "Enter a message", Type.STRING, required=True),
        Option("emoji", "Enter the emoji", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def set_reaction(ctx, role: discord.Role = None, msg: discord.Message = None, emoji=None):
    if role != None and msg != None and emoji != None:
        await msg.add_reaction(emoji)
        sConfig.setdefault('reaction', []).append((role.id, msg.id, emoji))
        sConfig.sync()
        ctx.reply("Reaction role set.")
    else:
        await ctx.reply("Invalid arguments.")


# bot warning and moderation system.


@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}


@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="Warns a user",
    options=[
        Option("member", "Enter a member", Type.USER, required=True),
        Option("reason", "Enter a reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
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

    await ctx.reply(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")


@slash_commands.has_role("Staff")
@slash.command(
       
    description="View a member's warnings",
    options=[
        Option("member", "Enter a member", Type.USER)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def warnings(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"displaying warnings for {member.name}", description="", color=discord.Color.red())
    try:
        i = 1
        for admin_id, reason in bot.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**warnings {1}** given by {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.reply(embed=embed)

    except KeyError:  # this person has no warnings
        await ctx.reply("This user has no warnings.")


@slash.command(
       
    description="Purges messages",
    options=[
        Option("amount", "Enter the amount", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.has_permissions(manage_messages=True)
async def purge(ctx, amount=2):
    await ctx.channel.purge(limit=int(amount))
    delMessage = await ctx.reply('Performed successfully')
    await asyncio.sleep(2)
    await delMessage.delete()


@slash.command(
       
    description="Kicks a user",
    options=[
        Option("user", "Enter the user", Type.USER),
        Option("reason", "Enter a reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided."):
    await ctx.reply(member.mention + " has been kicked.")
    await member.kick(reason=reason)



@slash.command(
       
    description="Bans a user",
    options=[
        Option("user", "Enter the user", Type.USER),
        Option("reason", "Enter a reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided."):
    await ctx.reply(member.mention + " has been banned.")
    await member.ban(reason=reason)


@slash.command(
       
    description="Unbans a user",
    options=[
        Option("user", "Enter the user", Type.STRING),
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_disc, = member.split('#')

    for banned_entry in banned_users:
        user = banned_entry.user
        if (user.name, user.discriminator,) == (member_name, member_disc):
            await ctx.guild.unban(user)
            await ctx.reply(member_name + " has been unbanned.")
            return

        await ctx.reply(member + " was not found.")



@slash.command(
       
    description="Mutes a user",
    options=[
        Option("user", "Enter the user", Type.USER, required=True),
        Option("reason", "Enter a reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member):
    muted_role = ctx.guild.get_role(708075939019489360)
    member_role = ctx.guild.get_role(695742663256834141)

    await member.remove_roles(member_role)
    await member.add_roles(muted_role)

    await ctx.reply(member.mention + " has been muted.")


@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="Unmutes a user",
    options=[
        Option("user", "Enter the user", Type.USER, required=True),
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def unmute(ctx, member: discord.Member):
    muted_role = ctx.guild.get_role(708075939019489360)
    member_role = ctx.guild.get_role(695742663256834141)

    await member.add_roles(member_role)
    await member.remove_roles(muted_role)

    await ctx.reply(member.mention + " has been unmuted.")


# suggestion command

@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="Sets the suggestion channel",
    options=[
        Option("schannel", "Enter the channel", Type.CHANNEL)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def set_suggestion_channel(ctx, schannel=None):
    if schannel != None:
        channel_name = schannel.name
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.suggestion_channel = channel
                sConfig['suggestion'] = channel_name
                await ctx.reply(f"Suggestion channel was set to: {channel.name}")
                # await channel.send("This is the new suggestion channel!")


@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='set_decided_suggestion_channel',   
    description="Sets the decided suggestion channel",
    options=[
        Option("set_channel", "Enter the channel", Type.CHANNEL, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def set_decided_channel(ctx, set_channel=None):
    if set_channel != None:
        channel_name = set_channel.name
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.suggestion_channel_two = channel
                sConfig['suggestion2'] = channel_name
                await ctx.reply(f"Decided suggestion channel was set to: {channel.name}")
                # await channel.send("This is the new suggestion channel!")


@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='accept',   
    description="Use this while replying to a suggestion to accept it.",
    options=[
        Option("number", "Number of affected suggestion", Type.STRING, required=True),        
        Option("reason", "Enter the reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def accept(ctx, number, reason='No reason provided.'):
    impMessage = await findSuggestion(number, ctx.channel)
    if impMessage is not None and impMessage.author.bot is True and impMessage.embeds is not None:
        relEmbed = impMessage.embeds[0]
        if 'has' in str(relEmbed.title):
            hasLoc = relEmbed.title.find('has')
            movedMessage = discord.Embed(
                title = relEmbed.title[:hasLoc] + 'has been accepted.',
                description=relEmbed.description,
                timestamp = ctx.created_at
            )
            oldFooterLoc = relEmbed.footer.text.rfind(' ', 0, relEmbed.footer.text.rfind('by') - 2)
            movedMessage.set_footer(
                text = relEmbed.footer.text[:oldFooterLoc] + f' Accepted by {ctx.author} | ID-{ctx.author.id}'
            )
        else:
            movedMessage = discord.Embed(
                title=relEmbed.title + ' has been accepted.',
                description=relEmbed.description,
                timestamp=ctx.created_at
            )
            movedMessage.set_footer(
                text=relEmbed.footer.text[69:] + ' Accepted by {} | ID-{}'.format(ctx.author,
                                                                                ctx.author.id))
        movedMessage.add_field(inline=True,
                               name='Reason:',
                               value=reason
                               )
        if botdata.suggestion_channel_two == None:
            for channel in ctx.guild.channels:
                if channel.name == sConfig['suggestion2']:
                    botdata.suggestion_channel_two = channel
        await botdata.suggestion_channel_two.send(embed=movedMessage)
        await impMessage.delete()
        delMessage = await ctx.reply('Performed successfully')
        await asyncio.sleep(2)
        await delMessage.delete()

    else:
        await ctx.reply('No message provided. Reply to a message to accept it.')


@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='implement',   
    description="Use this while replying to a suggestion to implement it.",
    options=[
        Option("number", "Number of the affected suggestion?", Type.STRING, required=True),
        Option("reason", "Enter the reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def implement(ctx, number, reason='No reason provided.'):
    impMessage = await findSuggestion(number, ctx.channel)
    if impMessage is not None and impMessage.author.bot is True and impMessage.embeds is not None:
        relEmbed = impMessage.embeds[0]
        if 'has' in str(relEmbed.title):
            hasLoc = relEmbed.title.find('has')
            movedMessage = discord.Embed(
                title = relEmbed.title[:hasLoc] + 'has been implemented.',
                description=relEmbed.description,
                timestamp = ctx.created_at
            )
            oldFooterLoc = relEmbed.footer.text.rfind(' ', 0, relEmbed.footer.text.rfind('by') - 2)
            movedMessage.set_footer(
                text = relEmbed.footer.text[:oldFooterLoc] + f' Implemented by {ctx.author} | ID-{ctx.author.id}'
            )
        else:
            movedMessage = discord.Embed(
                title=relEmbed.title + ' has been implemented.',
                description=relEmbed.description,
                timestamp=ctx.created_at
            )
            movedMessage.set_footer(
                text=relEmbed.footer.text[69:] + ' Implemented by {} | ID-{}'.format(ctx.author,
                                                                                ctx.author.id))
        movedMessage.add_field(inline=True,
                               name='Reason:',
                               value=reason
                               )
        if botdata.suggestion_channel_two == None:
            for channel in ctx.guild.channels:
                if channel.name == sConfig['suggestion2']:
                    botdata.suggestion_channel_two = channel
        await botdata.suggestion_channel_two.send(embed=movedMessage)
        await impMessage.delete()
        delMessage = await ctx.reply('Performed successfully')
        await asyncio.sleep(2)
        await delMessage.delete()

    else:
        await ctx.reply('No message provided. Reply to a message to implement it.')
@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="Use this to deny a suggestion",
    options=[
        Option("number", "Number of affected suggestion", Type.STRING, required=True),
        Option("reason", "Enter the reason", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def deny(ctx, number, reason='No reason provided.'):
    impMessage = await findSuggestion(number, ctx.channel)
    if impMessage is not None and impMessage.author.bot is True and impMessage.embeds is not None:
        relEmbed = impMessage.embeds[0]
        if 'has' in str(relEmbed.title):
            hasLoc = relEmbed.title.find('has')
            movedMessage = discord.Embed(
                title = relEmbed.title[:hasLoc] + 'has been denied.',
                description=relEmbed.description,
                timestamp = ctx.created_at
            )
            oldFooterLoc = relEmbed.footer.text.rfind(' ', 0, relEmbed.footer.text.rfind('by') - 2)
            movedMessage.set_footer(
                text = relEmbed.footer.text[:oldFooterLoc] + f' Denied by {ctx.author} | ID-{ctx.author.id}'
            )
        else:
            movedMessage = discord.Embed(
                title=relEmbed.title + ' has been denied.',
                description=relEmbed.description,
                timestamp=ctx.created_at
            )
            movedMessage.set_footer(
                text=relEmbed.footer.text[69:] + ' Denied by {} | ID-{}'.format(ctx.author,
                                                                                ctx.author.id))
        movedMessage.add_field(inline=True,
                               name='Reason:',
                               value=reason
                               )
        if botdata.suggestion_channel_two == None:
            for channel in ctx.guild.channels:
                if channel.name == sConfig['suggestion2']:
                    botdata.suggestion_channel_two = channel
        await botdata.suggestion_channel_two.send(embed=movedMessage)
        await impMessage.delete()
        delMessage = await ctx.reply('Performed successfully')
        await asyncio.sleep(2)
        await delMessage.delete()

    else:
        await ctx.reply('No message provided. Reply to a message to deny it.')

async def findSuggestion(number, channel):
    async for message in channel.history(limit=300):
        if message.author == bot.user and message.embeds != []:
            print(message.embeds)
            mEmbed = message.embeds[0]
            if number in mEmbed.title:
                return message

@slash.command(
    name='suggest',   
    description="Make a suggestion",
    options=[
        Option("description", "Enter the suggestion", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def suggest(ctx, *, description):
    sConfig['snum'] += 1
    suggest = discord.Embed(
        title="Suggestion #" + str(sConfig['snum']),
        description=f"{description}",
        color=0,
        timestamp=ctx.created_at
    )
    suggest.set_footer(
        text='Please react with a thumbs up or a thumbs down if you like this idea. Requested by {} | ID-{}'.format(
            ctx.author, ctx.author.id))
    if botdata.suggestion_channel == None:
        for channel in ctx.guild.channels:
            if channel.name == sConfig['suggestion']:
                botdata.suggestion_channel = channel
    msg = await botdata.suggestion_channel.send(embed=suggest)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    delMessage = await ctx.reply('Suggestion sent!')
    await asyncio.sleep(2)
    await delMessage.delete()



@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
       
    description="Use this to set the number of set suggestions.",
    options=[
        Option("number", "Enter a number", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def reset_snum(ctx, num):
    try:
        sConfig['snum'] = int(num)
    except ValueError:
        await ctx.reply('Invalid number.')
        return
    await ctx.reply(f'Set to {num} succesfully.')


# economy system


mainshop = [{"name": "VIP", "price": 50000, "description": "VIP rank"},
            {"name": "MVP", "price": 125000, "description": "MVP rank"},
            {"name": "ad", "price": 1000, "description": "Buy an ad for the advertisements channel"}]


@slash.command(   
    description="Use this to view your balance.",
)
async def balance(ctx):
    await open_account(ctx.author)
    user = ctx.author

    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    em = discord.Embed(title=f'{ctx.author.name} Balance', color=discord.Color.red())
    em.add_field(name="Wallet Balance", value=wallet_amt)
    em.add_field(name='Bank Balance', value=bank_amt)
    await ctx.reply(embed=em)


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
            if not await open_account(user):
                await update_bank(user, +10)
        if str(msg.content).find(" /") != -1 and tonesList_enabled:
            tones = str(msg.content).split('/')
            del tones[0]
            identifiedTones = []
            for part in tones:
                if part == '/':
                    continue  # skip this part of the message
                try:
                    identifiedTone = tonesList[part.strip()]  # find meaning
                    identifiedTones.append(identifiedTone)  # and save it
                except KeyError:
                    continue  # if there is none, ignore
            if len(identifiedTones) != 0:  # if we found any
                await msg.channel.send('Detected tones: %s' % (", ".join(identifiedTones)))
        if msg.channel.category.name != 'edgy' and msg.channel.category.name != 'staff channels':  # if this isn't edgy or staff
            words = msg.content.split()
            detectedWords = []
            with open(f"filter.txt", mode="a") as temp:  # create the filter file if it isn't there already
                pass

            with open(f"filter.txt", mode="r") as file:  # read the filter file
                flines = file.readlines()  # make a list of all the lines
                with open(f"whitelist.txt", mode="r") as wfile:
                    wlines = wfile.readlines()
                    if '' in flines:
                        flines.remove('')
                    if '' in wlines:
                        wlines.remove('')
                    for index, item in enumerate(flines):
                        if item.endswith('\n'):
                            flines[index] = item[:-1]
                    for index, item in enumerate(wlines):
                        if item.endswith('\n'):
                            wlines[index] = item[:-1]
                    for i in words:
                        if i not in wlines:
                            sRemove = stripSymbols(i)
                            if sRemove in flines:
                                detectedWords.append(sRemove)

            if detectedWords != []:  # did they swear?
                print(detectedWords)
                try:
                    dm = await msg.author.create_dm()
                    await dm.send(
                        "Please don't swear. Your message '%s' contained swearing (specifically '%s') and has been automatically removed." % (
                        msg.content, ', '.join(detectedWords)))
                except discord.errors.Forbidden:
                    await log(msg.guild, 'DM failed',
                              f'Messaging {msg.author} about their swearing has failed, ask them to open dms?')
                global filteredMessage
                filteredMessage = msg
                await log(msg.guild, f'Swear from {msg.author} in #{msg.channel.name} automatically removed', f'Original message: ||{msg.content}||')
                await msg.delete()


def stripSymbols(s):  # this is probably the wrong place but it's fine
    for char in string.punctuation:
        s = s.replace(char, '')

    return s.lower()


async def log(guild, title, text):
    guild = bot.get_guild(guildID)
    logEmbed = discord.Embed(
        title=title,
        description=text,
    )
    logEmbed.set_footer(
        text='Action automatically logged by Homeschool Club Bot')
    if botdata.logs_channel == None:
        for channel in guild.channels:
            if channel.name == sConfig['logs']:
                botdata.logs_channel = channel
                
    if botdata.logs_channel == None:
        print("Logs channel not set or did not load correctly.")
        return
    await botdata.logs_channel.send(embed=logEmbed)


# ik moderation should go somewhere else but i dont wanna bother so these stay here for now
# if you're updating the bot and can find a better spot feel free to move em
@slash_commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='set_logs_channel',   
    description="Set the logs channel",
    options=[
        Option("set_channel", "Enter the channel", Type.CHANNEL, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def set_logs_channel(ctx, set_channel=None):
    if set_channel != None:
        channel_name = set_channel.name
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.logs_channel = channel
                sConfig['logs'] = channel_name
                sConfig.sync()
                await ctx.reply(f"Logs channel was set to: {channel.name}")


@slash.command(
    name='withdraw',   
    description="Withdraw from bank",
    options=[
        Option("amount", "Enter the amount to withdraw", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def withdraw(ctx, amount=None):
    await open_account(ctx.author)
    bal = await update_bank(ctx.author)
    if amount == None:
        await ctx.send("Please enter the amount")
        return
    if amount == 'all':
        amount = bal[0]

    amount = int(amount)

    if amount > bal[1]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return

    await update_bank(ctx.author, amount)
    await update_bank(ctx.author, -1 * amount, 'bank')
    await ctx.reply(f'{ctx.author.mention} You withdrew {amount} coins')


@slash.command(
    name='deposit',   
    description="Deposit to bank",
    options=[
        Option("amount", "Enter the amount to deposit", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def deposit(ctx, amount=None):
    await open_account(ctx.author)
    bal = await update_bank(ctx.author)
    if amount == None:
        await ctx.send("Please enter the amount")
        return
    if amount == 'all':
        amount = bal[0]

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.send('Amount must be positive!')
        return

    await update_bank(ctx.author, -1 * amount)
    await update_bank(ctx.author, amount, 'bank')
    await ctx.reply(f'{ctx.author.mention} You deposited {amount} coins')


@slash.command(
       
    description="Send money to a user.",
    options=[
        Option("member", "Enter a user", Type.USER, required=True),
        Option("amount", "Enter an amount", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def send(ctx, member: discord.Member, amount=None):
    await open_account(ctx.author)
    await open_account(member)
    if amount == None:
        await ctx.reply("Please enter the amount")
        return

    bal = await update_bank(ctx.author)
    if amount == 'all':
        amount = bal[0]

    amount = int(amount)

    if amount > bal[0]:
        await ctx.reply('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.reply('Amount must be positive!')
        return

    await update_bank(ctx.author, -1 * amount, 'bank')
    await update_bank(member, amount, 'bank')
    await ctx.reply(f'{ctx.author.mention} You gave {member} {amount} coins')


@slash.command(
       
    description="Rob a user. Note: Has a chance of backfiring. (5 minute cooldown)",
    options=[
        Option("member", "Enter a user", Type.USER, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
@slash_commands.cooldown(1,robCooldown*60, type=BucketType.member)
async def rob(ctx, member: discord.Member):
    if member.status == discord.Status.offline:
        return await ctx.reply('That user is offline, and cannot be robbed.')
    await open_account(ctx.author)
    await open_account(member)
    bal = await update_bank(member)
    rBal = await update_bank(ctx.author)


    if bal[0] < 100:
       await ctx.reply('It is useless to rob him :(')
       return
    earning = random.randrange(-1 * rBal[0], bal[0])

    await update_bank(ctx.author, earning)
    await update_bank(member, -1 * earning)
    if earning > 1:
        await ctx.reply(f'{ctx.author.mention} robbed {member} and got {earning} coins.')
    else:
        await ctx.reply(f'{ctx.author.mention} was caught robbing {member}! They lost {earning * -1} coins.')
    


@slash.command(
       
    description="Bet on flipping a coin.",
    options=[
        Option("amount", "Amount to bet", Type.STRING, required=True),
        Option("coin", "Heads or tails", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
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
        await ctx.reply('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.reply('Amount must be positive!')
        return
    if coin != 'heads' and coin != 'h' and coin != 'tails' and coin != 't':
        await ctx.reply('You must enter a valid coinflip option!')
        return

    coinFlip = random.choice(['heads', 'tails'])
    Win = random.choice([False, True, True, True, True, True, True])
    if not Win:
        if coin == 'heads' or coin == 'h':
            coinFlip = 'tails'
        else:
            coinFlip = 'heads'
    await ctx.reply('The coin was ' + coinFlip + '.')
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


@slash.command(
       
    description="Gamble an amount of money.",
    options=[
        Option("amount", "Enter an amount to gamble.", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def gamble(ctx, amount=None):
    await open_account(ctx.author)
    if amount == None:
        await ctx.reply("Please enter the amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[0]:
        await ctx.reply('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.reply('Amount must be positive!')
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


@slash.command(
       
    description="Roll a die, and if you put an amount, bet on it",
    options=[
        Option("amount", "Enter how much you want to bet.", Type.STRING),
        Option("face", "Enter what face to bet on", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def roll(ctx, amount: str = None, bet: int = None):
    roll = random.randint(1, 6)
    won = 'lost '
    try:
        amount = int(amount)
    except Exception:
        await ctx.reply(':game_die: You rolled a ' + str(roll))
        return

    await open_account(ctx.author)

    bal = await update_bank(ctx.author)

    if amount > bal[0]:
        await ctx.reply('You do not have sufficient balance')
        return
    if amount < 0:
        await ctx.reply('Amount must be positive!')
        return
    if bet > 6:
        await ctx.reply('You can only bet numbers on the dice.')
        return

    if roll == bet:
        won = 'won '
        amount = amount * 5
        await update_bank(ctx.author, +amount)
    else:
        await update_bank(ctx.author, -amount)

    await ctx.reply(':game_die: You rolled a ' + str(roll) + ' and ' + won + str(amount) + ' coins.')
    print('rolled')


@slash.command(
       
    description="View shop",
)
async def shop(ctx):
    em = discord.Embed(title="Shop")

    for item in mainshop:
        name = item["name"]
        price = item["price"]
        desc = item["description"]
        em.add_field(name=name, value=f"${price} | {desc}")

    await ctx.reply(embed=em)


@slash.command(
       
    description="Buy item from shop",
    options=[
        Option("item", "Enter a item", Type.STRING, required=True),
        Option("amount", "How many items (defaults to 1)", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def buy(ctx, item, amount=1):
    await open_account(ctx.author)

    res = await buy_this(ctx.author, item, amount)
    vip = True
    if item == 'mvp':
        member = ctx.author
        roles = ctx.guild.roles
        role = discord.utils.get(roles, name="VIP")
        if not role in member.roles:
            await ctx.reply("You don't have VIP yet!")
            vip = False
            return
    if not res[0]:
        if res[1] == 1:
            await ctx.reply("That Object isn't there!")
            return
        if res[1] == 2:
            await ctx.reply(f"You don't have enough money in your wallet to buy {amount} {item}")
            return
    if res[0]:
        if item.lower() == 'vip':
            member = ctx.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="VIP")
            await member.add_roles(role)
        elif item.lower() == 'mvp' and vip == True:
            member = ctx.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="MVP")
            await member.add_roles(role)
        elif item.lower() == 'ad':
            member = ctx.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="ad")
            await member.add_roles(role)
    await ctx.send(f"You just bought {amount} {item}")


@slash.command(
    name='bag',   
    description="View bag.",
)
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

    await ctx.reply(embed=em)


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


@slash.command(
       
    description="Sell some of your items (run /bag to view them)",
    options=[
        Option("item", "Enter a item", Type.STRING, required=True),
        Option("amount", "How many items (defaults to 1)", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def sell(ctx, item, amount=1):
    await open_account(ctx.author)

    res = await sell_this(ctx.author, item, amount)

    if not res[0]:
        if res[1] == 1:
            await ctx.reply("That Object isn't there!")
            return
        if res[1] == 2:
            await ctx.reply(f"You don't have {amount} {item} in your bag.")
            return
        if res[1] == 3:
            await ctx.reply(f"You don't have {item} in your bag.")
            return
    if res[0]:
        if item.lower() == 'vip':
            member = ctx.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="VIP")
            await member.remove_roles(role)
        elif item.lower() == 'mvp':
            member = ctx.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="MVP")
            await member.remove_roles(role)
        elif item.lower() == 'ad':
            member = ctx.author
            roles = ctx.guild.roles
            role = discord.utils.get(roles, name="ad")
            await member.remove_roles(role)
    await ctx.reply(f"You just sold {amount} {item}.")


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


@slash.command(
       
    description="View leaderboard",
    options=[
        Option("amount", "Enter how many users to view (defaults to 10)", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
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
        if member == None:
            continue
        name = member.name
        em.add_field(name=f"{index}. {name}", value=f"{amt}", inline=False)
        if index == x:
            break
        else:
            index += 1

    await ctx.reply(embed=em)


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
    try:
        users[str(user.id)][mode] += change
    except KeyError:
        await open_account(user)
        users[str(user.id)][mode] += change
    with open('mainbank.json', 'w') as f:
        json.dump(users, f)
    bal = users[str(user.id)]['wallet'], users[str(user.id)]['bank']
    return bal


# fun commands
@slash.command(
    name = '8ball',   
    description="Ask a magic 8ball (100% legit) any question",
    options=[
        Option("question", "Enter any question", Type.STRING),
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def _8ball(ctx, *, question=None):
    responsesDict = {"hey hsb, did you get anything for christmas?": "a watch. it said it was from the present",
                     "do you like pay to win games?": "yeah, but I only use a bit-coin",
                     "are you a meaningless piece of 0's and 1's floating in the wide expanse of your code?": "01011001 01100101 01110011...",
                     "04 27 2021": "aww, you remembered my birthday!",
                     "01011001 01100101 01110011": "01001000 01100101 01101100 01101100 01101111 00100001"}
    try:
        answer = responsesDict[question]
    except KeyError:
        answer = random.choice(
            ['No', 'Probably not', 'It\'s possible', 'Maybe', 'Concentrate and ask again', 'Possibly', 'Probably',
             'Very likely', 'Almost certainly', 'Definitely', 'No way'])
    await ctx.reply(f'**{ctx.author.display_name}** asks: **{question}** \n🎱 | {answer}, **{ctx.author.display_name}**')

@slash.command(
       
    description="Get a random pun",

)
async def pun(ctx):
    answer = random.choice(['What did the grape say when it got crushed? Nothing, it just let out a little wine.',
                            'Time flies like an arrow. Fruit flies like a banana.',
                            'To the guy who invented zero, thanks for nothing.',
                            'I had a crazy dream last night! I was swimming in an ocean of orange soda. Turns out it was just a Fanta sea.',
                            'Geology rocks but Geography is where it’s at!', 'Can February March? No, but April May.',
                            'I don’t trust stairs because they’re always up to something.',
                            'A man sued an airline company after it lost his luggage. Sadly, he lost his case.',
                            'My grandpa has the heart of the lion and a lifetime ban from the zoo.',
                            'I lost my mood ring and I don’t know how to feel about it!',
                            'So what if I don’t know what apocalypse means? It’s not the end of the world!',
                            'Becoming a vegetarian is one big missed steak.',
                            'I was wondering why the ball was getting bigger. Then it hit me.',
                            'Never trust an atom, they make up everything!',
                            'Waking up this morning was an eye-opening experience.',
                            'Long fairy tales have a tendency to dragon.', 'I made a pun about the wind but it blows.',
                            'I can’t believe I got fired from the calendar factory. All I did was take a day off!',
                            'She had a photographic memory, but never developed it.',
                            'I wasn’t originally going to get a brain transplant, but then I changed my mind.',
                            'There was a kidnapping at school yesterday. Don’t worry, though – he woke up!',
                            'What do you call an alligator in a vest? An investigator.',
                            'German sausage jokes are just the wurst.', 'How does Moses make coffee? Hebrews it.',
                            'What do you call the ghost of a chicken? A poultry-geist.',
                            'I bought a boat because it was for sail.',
                            'My ex-wife still misses me. But her aim is starting to improve!',
                            'I just found out that I’m color blind. The news came completely out of the green!',
                            'Why didn’t the cat go to the vet? He was feline fine!',
                            'Who is the penguin’s favorite Aunt? Aunt-Arctica!',
                            'Apple is designing a new automatic car. But they’re having trouble installing Windows!',
                            'Did you hear about the guy who got hit in the head with a can of soda? He was lucky it was a soft drink!',
                            'Did you hear about that cheese factory that exploded in France? There was nothing left but de Brie!',
                            'I’m no cheetah, you’re lion!',
                            'My dad unfortunately passed away when we couldn’t remember his blood type. His last words to us were, “Be positive!”',
                            'What’s America’s favorite soda? Mini soda.',
                            'Why should you never trust a train? They have loco motives.',
                            'What did the buffalo say to his son? Bison.',
                            'Why does Peter Pan fly all the time? He Neverlands.',
                            'My dog can do magic tricks. It’s a labracadabrador.',
                            'I used to have a fear of hurdles, but I got over it.',
                            'Once you’ve seen one shopping center you’ve seen a mall.',
                            'What are windmills’ favorite genre of music? They’re big metal fans.',
                            'I love whiteboards. They’re re-markable.',
                            'I tried to make a belt out of watches. It was a waist of time.',
                            'Yesterday a clown held the door open for me. It was such a nice jester.',
                            'Why can’t Harry Potter tell the difference between his potion pot and his best friend? They’re both cauld ron.',
                            'What does C.S. Lewis keep in his wardrobe? Narnia business.',
                            'I was worried about being in a long-distance relationship. But so far so good.',
                            'RIP boiling water. You will be mist.',
                            'I’m reading a book about anti-gravity. It’s impossible to put down.',
                            'I decided to get rid of my spine. It was holding me back.',
                            'Long fairy tales have a tendency to dragon.',
                            'Who designed King Arthur’s round table? Sir Cumference.',
                            'I couldn’t remember how to throw a boomerang. Eventually it came back to me.',
                            'I tried to draw a circle, but it was pointless.',
                            'A cartoonist was found dead. Details are sketchy.',
                            'My wife told me to stop speaking in numbers. But I didn’t 1 2.',
                            'Need an ark? I Noah guy.', 'I used to hate facial hair, but it grew on me.'])
    await ctx.send(answer)

@slash.command(
       
    description="Get a random fun fact",
)
async def funfact(ctx):
    answer = random.choice(['Sadly there aren\'t any fun facts yet, check back later! \n ||*cough* <@513693374671224852> YOU NEED TO FINISH THEM MAN AAAA||'])
    await ctx.send(answer)

@slash.command(
       
    description="Run an action on someone",
    options=[
        Option("action", "Enter an action (type list for a list)", Type.STRING, required=True),
        Option("acted_user", "What user to run it on", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def action(ctx, action='invalid', acted_user=None):
    try:
        currentActions = actions[action]
    except KeyError:
        await ctx.send('Invalid action. \n Valid actions: ' + ', '.join(list(actions)))
        return
    await ctx.send('%s %s %s! \n %s' % (ctx.author.display_name, currentActions[0], acted_user,
                                        currentActions[random.randint(1, len(currentActions) - 1)]))

@slash.command(
       
    description="Make a poll",
    options=[
        Option("question", "Enter a question", Type.STRING, required=True),
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def poll(ctx, question):

    poll = discord.Embed(
        title=f"{ctx.author} asks",
        description=f"{question}",
        color=discord.Colour.blurple(),
    )
    msg = await ctx.reply(embed=poll)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

@commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='send',   
    description="Send an embed",
    options=[
        Option("title", "Enter the title of the embed", Type.STRING, required=True),
        Option("channel", 'Enter the channel to post in', Type.CHANNEL),
        Option("description", "Enter the description of the embed", Type.STRING),
        Option("footer", "Enter the footer of the embed", Type.STRING)
        
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def send(ctx, title, channel=None, description='', footer = ''):
    if channel == None:
        channel = ctx.channel
    suggest = discord.Embed(
        title=title,
        description=description,
        color=discord.Colour.blurple(),
        timestamp=ctx.created_at
    )
    suggest.set_footer(text=footer)
    msg = await channel.send(embed=suggest)
    delMessage = await ctx.reply('Embed sent!')
    await asyncio.sleep(2)
    await delMessage.delete()

@commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='edit',   
    description="Edit an embed",
    options=[
        Option('message_id', "Enter the ID of the message to edit", Type.STRING, required=True),
        Option("message_channel", 'Enter the channel the edited message is in', Type.CHANNEL, required=True),
        Option("title", "Enter the title of the embed", Type.STRING, required=True),
        Option("description", "Enter the description of the embed", Type.STRING),
        Option("footer", "Enter the footer of the embed", Type.STRING)
        
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def edit(ctx, message_id, message_channel, title, description='', footer = ''):
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Colour.blurple(),
        timestamp=ctx.created_at
    )
    embed.set_footer(text=footer)
    msg = await message_channel.fetch_message(message_id)
    await msg.edit(embed=embed)
    delMessage = await ctx.reply('Embed edited successfully.')
    await asyncio.sleep(2)
    await delMessage.delete()

@slash.command(
    name='easteregg',
    description='easterEggs are fun...'
)
async def easteregg(ctx):
    try:
        await ctx.author.edit(nick='magicalHouse')
        msg = await ctx.reply('magical houses will consume all \n dont spoil it for the others though')
    except Exception:
        msg = await ctx.reply('i would love to destroy you with a magical house but sadly you are TOO famous')
    await asyncio.sleep(3)
    await msg.delete()
# logs

@bot.event
async def on_message_delete(message):
    if message != filteredMessage:
        if message.content != None:
            await log(message.guild, f'{message.author.name}\'s message in #{message.channel.name} has been deleted.', message.content)


@bot.event
async def on_message_edit(before, after):
    if before.content != after.content and after.content != None:
        await log(before.guild, before.author.name + f' has edited their message in #{after.channel.name}.',
                  f'**Before:** \n {before.content} \n **After:** \n {after.content}')


@bot.event
async def on_guild_channel_create(channel):
    await log(channel.guild, f'#{channel.name} has been created.',
              f'{channel.mention} is in category {channel.category.name}. \n ')


@bot.event
async def on_guild_channel_delete(channel):
    await log(channel.guild, '#' + channel.name + ' has been deleted.',
              f'#{channel.name} was in category {channel.category.name}.')


@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        if after.nick != None:
            await log(before.guild, f'{after.name}\'s nickname has changed.',
                      f'Old nickname: \n {before.nick} \n New nickname: \n {after.nick}')
        else:
            await log(before.guild, f'{after.name}\'s nickname has been reset.',
                      f'Old nickname: \n {before.nick} \n New nickname: \n {after.name}')


@bot.event
async def on_guild_role_create(role):
    await log(role.guild, f'@{role.name} has been created.', f'{role.mention} has id {role.id}. \n ')


@bot.event
async def on_guild_role_delete(role):
    await log(role.guild, '@' + role.name + ' has been deleted.', f'{role.mention} had id {role.id}.')


@bot.event
async def on_member_ban(guild, user):
    await log(guild, f'{user.name} has been banned.', f'{user.mention} has id {user.id}. \n ')


@bot.event
async def on_member_unban(guild, user):
    await log(guild, f'{user.name} has been unbanned.', f'{user.mention} has id {user.id}. \n ')


@bot.event
async def on_member_join(user):
    await log(user.guild, f'{user.name} has joined.',
              f'{user.mention} created their account at {user.created_at}.')
    if botdata.welcome_channel == None:
        for channel in user.guild.channels:
            if channel.name == sConfig['welcome']:
                botdata.welcome_channel = channel
    if botdata.welcome_channel == None:
        print('Welcome channel not set or did not load correctly.')
    await botdata.welcome_channel.send(
        f"Welcome! {user.mention} Please be sure to read the rules in the rules channel, and check out the rules in our website: https://homeschool-club.weebly.com/rules.html")



@bot.event
async def on_member_remove(user):
    await log(user.guild, f'{user.name} has left.', f'{user.mention} created their account at {user.created_at}.')
    if botdata.welcome_channel == None:
        for channel in user.guild.channels:
            if channel.name == sConfig['welcome']:
                botdata.welcome_channel = channel
    if botdata.welcome_channel == None:
        print('Welcome channel not set or did not load correctly.')
    await botdata.welcome_channel.send(f"Goodbye {user.mention}")

@slash.event
async def on_slash_command_error(inter, error):
    await on_command_error(inter, error)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send("Command failed with error: ```\n" + str(error) + "\n```Make sure you've given the correct arguments, you have permission to run the command, and you're running it in the right channels, and if everything looks right, contact the devs.")
    await log(ctx.guild, 'Command failed', f'Error: \n ```{error}``` \n User: \n {ctx.author.mention} \n Channel: \n {ctx.channel.mention}')

# qotd system
def seconds_until(hours, minutes):
    given_time = datetime.time(hours, minutes, tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    future_exec = datetime.datetime.combine(now, given_time)
    if (future_exec - now).days < 0:  # If we are past the execution, it will take place tomorrow
        future_exec = datetime.datetime.combine(now + datetime.timedelta(days=1), given_time) # days always >= 0

    return (future_exec - now).total_seconds()
    

async def qotd(self):
    guild = bot.get_guild(guildID)
    while True:  # Or change to self.is_running or some variable to control the task
        await asyncio.sleep(seconds_until(qotdH,qotdM))  # Will stay here until the time is the set one
        with open(f"questions.txt", mode="a") as temp:  # create the filter file if it isn't there already
            pass

        with open(f"questions.txt", mode="r") as file:  # read the filter file
            flines = file.readlines()  # make a list of all the lines
            if botdata.qotd_channel == None:
                for channel in guild.channels:
                    if channel.name == sConfig['qotd']:
                        botdata.qotd_channel = channel
            sConfig['qnum'] += 1
            sentQotds = sConfig['qnum']
            try:
                yesterdaysQotd = sentQotd
                await yesterdaysQotd.unpin()
            except:
                await log(guild, 'Failed to unpin old qotd', f'QOTD #{sentQotds-1} could not be unpinned, please unpin it manually.')
            try:
                todaysQotd = flines[sConfig['qnum']]
                qotdEmbed = discord.Embed(title="Question Of The Day", description=todaysQotd, color=0x00ff00)
                qotdEmbed.set_footer(text=f'QOTD {sentQotds}/{len(flines)}')
                sentQotd = await botdata.qotd_channel.send(embed = qotdEmbed)
                try:
                    await sentQotd.pin()
                except:
                    await log(guild, 'Failed to pin QOTD', f'QOTD number {sentQotds} could not be pinned')
            except IndexError:
                await log(guild, 'QOTD failed to send', f'QOTD number {sentQotds} has failed to send, make sure it exists?')
        for member in guild.members:
            if member.nick == 'magicalHouse':
                await member.edit(nick=None)
        await asyncio.sleep(120)  # Practical solution to ensure that the print isn't spammed as long as it is 11:58

@commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
 
    description="Sets the qotd channel",
    options=[
        Option("channel_name", "Enter the channel", Type.CHANNEL)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def set_qotd_channel(ctx, channel_name=None):
    if channel_name != None:
        channel_name = channel_name.name
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.qotd_channel = channel
                sConfig['qotd'] = channel_name
                sConfig.sync()
                await ctx.reply(f"QOTD channel has been set to: {channel.name}")
                return
    await ctx.reply(
        "Invalid channel. Make sure you're sending a channel name (qotd), and not a channel link (#qotd).")
@commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
 
    description="Sets number of sent qotds",
    options=[
        Option("amount", "Enter the amount", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def reset_qnum(ctx, amount):
    try:
        sConfig['qnum'] = int(amount)
    except ValueError:
        await ctx.reply('Invalid number.')
        return
    await ctx.reply('Set succesfully.')

@commands.has_role("━━ « ( ⍟ Staff Team ⍟ ) » ━━")
@slash.command(
    name='add_qotd',
    description="Add a qotd",
    options=[
        Option("question", "Enter the qotd to add", Type.STRING, required=True)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def add_qotd(ctx, question):
    with open(f"questions.txt", mode="a") as file:
        file.write('\n' + question)
        file.close()
    f = open("questions.txt", mode='r')
    lines = f.readlines()
    f.close()
    await ctx.reply(f'``{lines[len(lines)-1]}`` was added to the QOTD list succesfully.')

    
# server ping
@slash.command(
 
    description="Pings a server",
    options=[
        Option("ip", "Enter the IP (defaults to HSC official)", Type.STRING)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def ping(ctx, ip='homeschoolclub.revivemc.net'):
    pingedServer = MinecraftServer.lookup(ip)
    
    try:
        status = pingedServer.status()
            
        #query = pingedServer.query()
        #await ctx.channel.send(f"{ip} has these {status.players} players online: {', '.join(query.players.names)} \n It also has MOTD ```\n{query.motd}\n```")
        
        await ctx.reply(f'Note: Due to an issue with Dinnerbone\'s library, displaying the MOTD of most servers is not currently working. \n {ip} has {status.players.online} players online and responded in {status.latency}ms. It runs {status.version.name}. \n MOTD: ```\n{str(status.description)}\n```')
    except:
        await ctx.reply('Server did not respond to request.')

# music system



async def setup():
    await bot.wait_until_ready()
    bot.add_cog(Player(bot))
    #for name, cmd in slash.commands.items():
        #await slash.register_global_slash_command(name)
bot.loop.create_task(setup())



# bot token
def get_token():
    with open(f"token.txt", mode="a") as temp:
        pass

    with open(f"token.txt", mode="r") as file:
        lines = file.readlines()
        return lines[0]


bot.run(str(get_token()))