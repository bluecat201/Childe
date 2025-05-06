import discord
import aiohttp
from discord.ext import commands, tasks
import random
import json
import os
import asyncio
from discord.ui import Button, View
from discord import app_commands
from discord.ext.commands import MissingPermissions
import aiofiles
import requests
import subprocess  # Add this import for running git commands
from datetime import datetime
from gemini_api import ChatSession


DEFAULT_PREFIX = "!"
PREFIX_FILE = "prefixes.json"
WARNINGS_FILE = "warnings.json"

SETTINGS_FILE = "server_settings.json"

# Function to get the current version from git commit
def get_version():
    try:
        version = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:%s'],
            stderr=subprocess.STDOUT
        ).decode('utf-8').strip()
        return version
    except Exception:
        return "Unknown Version"

# Get the version at startup
CURRENT_VERSION = "0.3.4"

# Načítání prefixů ze souboru
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        custom_prefixes = json.load(f)
else:
    custom_prefixes = {}

async def determine_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX

    guild_id = str(message.guild.id)
    
    # Load settings file
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    else:
        settings = {"guilds": {}}

    # Navigate the nested structure to find the prefix
    # First get the guild dict, then get the prefix from that guild
    prefix = settings.get("guilds", {}).get(guild_id, {}).get("prefix", DEFAULT_PREFIX)
    return prefix

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=determine_prefix, intents=intents)

GUILD_ID = 535890114258141184 
TWITCH_CHANNEL = "bluecat201"  # Twitch kanál, který chcete sledovat
ANNOUNCEMENT_CHANNEL_ID = 592348081362829312  # ID kanálu, kde chcete oznámení
CLIENT_ID = "hkn3fxk347cduph95gem7n22u2xod9"
CLIENT_SECRET = "wf4j6ts074b94qvp2z44e7d4aha3e6"
YOUR_USER_ID = 443842350377336860
CO_OWNER_USER_ID = 1335248197467242519

#twitch announcement
access_token = None
is_stream_live = False

async def get_access_token():
    global access_token
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=params)
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"New access token obtained at {datetime.now()}")
    else:
        print(f"Failed to get access token: {response.status_code} {response.text}")

async def check_twitch(bot):
    global is_stream_live
    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_CHANNEL}"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("data"):
                    if not is_stream_live:
                        is_stream_live = True
                        guild = bot.get_guild(GUILD_ID)
                        if not guild:
                            print(f"Guild with ID {GUILD_ID} not found.")
                            return

                        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
                        if not channel:
                            print(f"Channel with ID {ANNOUNCEMENT_CHANNEL_ID} not found.")
                            return

                        stream_info = data["data"][0]
                        title = stream_info.get("title", "")[0:100]
                        game_name = stream_info.get("game_name", "Unknown")

                        await channel.send(
                            f"🎥 **{TWITCH_CHANNEL}** právě začal streamovat!\n"
                            f"🎮 Hraje: {game_name}\n"
                            f"📢 Titulek streamu: {title}\n"
                            f"🔗 Sledujte na: https://www.twitch.tv/{TWITCH_CHANNEL}"
                        )
                else:
                    if is_stream_live:
                        is_stream_live = False
                        print(f"{TWITCH_CHANNEL} stream has ended at {datetime.now()}.")
            else:
                print(f"Failed to fetch Twitch stream data: {response.status}")

async def start_twitch_monitor(bot):
    await get_access_token()
    while True:
        try:
            await check_twitch(bot)
        except Exception as e:
            print(f"Error while checking Twitch: {e}")
        await asyncio.sleep(300)  # Check every 5 minutes

# Event: Bot je připraven
@bot.event
async def on_ready():
    print(f'Connected to bot: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    await load_extensions()
    await sync_commands(bot)
    await bot.change_presence(activity=discord.Streaming(name=f'{CURRENT_VERSION}', url='https://www.twitch.tv/Bluecat201'))
    start_twitch_monitor(bot)
    print(f'Bot sleduje Twitch')

    channel_id = 1325107856801923113  # Replace with your channel's ID
    channel = bot.get_channel(channel_id)
    
    if channel:
        await channel.send("Bot is ready! ✅")  # Customize the message
    else:
        print(f'Channel with ID {channel_id} not found.')

# Funkce pro načtení všech extensions
async def load_extensions():
    for filename in os.listdir("./cogs"):  # Zkontroluje složku "cogs"
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")  # Načte bez .py
                print(f"Načten modul: {filename}")
            except Exception as e:
                print(f"Chyba při načítání {filename}: {e}")

async def sync_commands(bot):
    for guild in bot.guilds:  # Pokud chcete synchronizovat pro konkrétní servery
        try:
            await bot.tree.sync(guild=guild)
            print(f"Příkazy synchronizovány pro server: {guild.name}")
        except Exception as e:
            print(f"Chyba při synchronizaci příkazů pro {guild.name}: {e}")

# Slash příkaz: Kámen, nůžky, papír
@bot.tree.command(name="rps", description="Play rock, paper, scissors")
@app_commands.choices(option=[
    app_commands.Choice(name="Rock", value="1"),
    app_commands.Choice(name="Scissors", value="2"),
    app_commands.Choice(name="Paper", value="3"),
])
async def rps(interaction: discord.Interaction, option: app_commands.Choice[str]):
    pc = random.randint(1, 3)
    outcomes = {
        ("1", 1): "Rock vs Rock\n DRAW",
        ("1", 2): "Rock vs Scissors\n YOU WON",
        ("1", 3): "Rock vs Paper\n YOU LOSE",
        ("2", 1): "Scissors vs Rock\n YOU LOSE",
        ("2", 2): "Scissors vs Scissors\n DRAW",
        ("2", 3): "Scissors vs Paper\n YOU WON",
        ("3", 1): "Paper vs Rock\n YOU WON",
        ("3", 2): "Paper vs Scissors\n YOU LOSE",
        ("3", 3): "Paper vs Paper\n DRAW",
    }
    await interaction.response.send_message(outcomes[(option.value, pc)])

# Slash příkaz: Odkazy
@bot.tree.command(name="links", description="My socials")
@app_commands.choices(option=[
    app_commands.Choice(name="Twitch", value="My twitch: https://www.twitch.tv/bluecat201"),
    app_commands.Choice(name="Support", value="Here is my support server: https://discord.gg/QmB2Ang4vr"),
    app_commands.Choice(name="Youtube", value="Main Channel: https://www.youtube.com/channel/UCwY2CDHkQGmCIwgVgEJKt8w"),
    app_commands.Choice(name="Instagram", value="My IG: https://www.instagram.com/bluecat221/"),
    app_commands.Choice(name="Web", value="My website: https://bluecat201.weebly.com/"),
])
async def link(interaction: discord.Interaction, option: app_commands.Choice[str]):
    await interaction.response.send_message(option.value)

# Načítání tokenu ze souboru
with open("config.json", "r") as file:
    config = json.load(file)
    TOKEN = config["token"]

#|non-slash|  
#NORMAL COMMANDS
#blackcat
@bot.command(aliases=['Blackcat','BLACKCAT'])
async def blackcat(ctx):
    await ctx.send("Alive and lost")

#bluecat
@bot.command(aliases=['Bluecat','BLUECAT'])
async def bluecat(ctx):
    await ctx.send("Not femboy")

#info
@bot.command(aliases=['Info','INFO'])
async def info(ctx):
    await ctx.send(f"The bot was created as my long-term graduation project \nRelease date of the first alpha version: 5.9.2021 \nRelease date of the first beta version: 30.9.2021\nProgrammed in python \nIf you have any comments, advice or ideas for the bot, you can write them on the support server. \nThe number of servers I'm on: {len(bot.guilds)}\nCurrent version: {CURRENT_VERSION} \nDeveloper: Bluecat201")

#invite bota
@bot.command(aliases=['Invite','INVITE'])
async def invite(ctx):
    await ctx.send("Here is my invite: https://discord.com/api/oauth2/authorize?client_id=883325865474269192&permissions=8&scope=bot%20applications.commands")

#ping
@bot.command(aliases=['Ping','PING'])
async def ping(ctx):
    await ctx.send('Pong! {0}ms'.format(round(bot.latency, 1)))

#support
@bot.command(aliases=['Support','SUPPORT'])
async def support(ctx):
    await ctx.send("Here is my support server: https://discord.gg/QmB2Ang4vr")

#twitch
@bot.command(aliases=['Twitch','TWITCH'])
async def twitch(ctx):
    await ctx.send("Here is developer twitch channel: https://www.twitch.tv/bluecat201")

#response
chat_session = ChatSession()

@bot.event
async def on_message(message):
    IGNORED_CHANNELS = [648557196837388289]
    # Don't let the bot respond to itself or other bots
    if message.author.bot:
        return
    
    # Ignorujte zprávy z konkrétních kanálů
    if message.channel.id in IGNORED_CHANNELS:
        return

    # Check if the bot is mentioned
    if bot.user.mentioned_in(message):
        query = message.content.replace(f"<@!{bot.user.id}>", "").strip()  # Odstraní zmínku bota z obsahu zprávy
        
        # Start typing indicator while generating response
        async with message.channel.typing():
            response = await chat_session.send_message(query)
            
        await message.reply(response)

    # Handle normal bot commands as well
    await bot.process_commands(message)

# Reset command (restricted to your user)
@bot.command()
async def reset(ctx):
    if ctx.author.id != YOUR_USER_ID and ctx.author.id != CO_OWNER_USER_ID:
        await ctx.send("This command can only be used by the owner of the bot.")
        return

    await ctx.send("Bot is reseting...")
    await bot.close()

#state command
@bot.command(aliases=['State', 'STATUS', 'status'])
async def state(ctx):
    if ctx.author.id != YOUR_USER_ID and ctx.author.id != CO_OWNER_USER_ID:
        await ctx.send("This command can only be used by the owner or co-owner of the bot.")
        return
    async with ctx.typing():
        try:
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                stderr=subprocess.STDOUT
            ).decode('utf-8').strip()
            
            # Get full commit info with ID and author
            commit = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=format:%h - %s (%an)'], 
                stderr=subprocess.STDOUT
            ).decode('utf-8').strip()
            
            # Use the same version variable across the bot
            version = CURRENT_VERSION (get_version())
                                        
            embed = discord.Embed(
                title="Bot Git Status", 
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Current Version", value=f"`{version}`", inline=False)
            embed.add_field(name="Current Branch", value=f"`{branch}`", inline=False)
            embed.add_field(name="Latest Commit", value=f"`{commit}`", inline=False)
                            
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
            
        except subprocess.CalledProcessError as e:
            await ctx.send(f"Error running git commands: ```\n{e.output.decode('utf-8')}```")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

#prefix command
@bot.command(name="prefix")
@commands.has_permissions(administrator=True)
async def change_prefix(ctx, prefix: str):
    if not prefix:
        await ctx.send("You need to specify a prefix.")
        return
        
    guild_id = str(ctx.guild.id)
    
    # Load settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    else:
        settings = {"guilds": {}}
    
    # Ensure guild exists in settings
    if guild_id not in settings.get("guilds", {}):
        settings["guilds"][guild_id] = {}
    
    # Update prefix
    settings["guilds"][guild_id]["prefix"] = prefix
    
    # Save settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
    
    await ctx.send(f"Prefix changed to: `{prefix}`")

#|výstup do konzole|

#logace připojení uživatele
@bot.event
async def on_member_join(member):
    server = str(member.guild.name)
    print(f'{member} se připojil na server {server}')

#logace přidání bota na server
@bot.event
async def on_guild_join(guild):
    print(f'Bot byl přidán na server: {guild}')

#logace odebrání bota ze serveru
@bot.event
async def on_guild_remove(guild):
    print(f'Bot byl odebrán ze serveru: {guild}')

#Logace odpojení uživatele
@bot.event
async def on_member_remove(member):
    server = str(member.guild.name)
    print(f'{member} se odpojil  ze serveru {server}')

#logace vytvoření role
@bot.event
async def on_guild_role_create(role):
    server = str(role.guild.name)
    print(f'Role {role} byla vytvořena [{server}]')

#logace smazání role
@bot.event
async def on_guild_role_delete(role):
    server = str(role.guild.name)
    print(f'Role {role} byla smazána [{server}]')

#logace přidání role uživately
@bot.event
async def on_guild_role_update(before,after):
    server = str(before.guild.name)
    print(f'Role {before} byla změněna na {after} na serveru {server}')

#logace změny zprávy
@bot.event
async def on_message_edit(before,after):
    server = str(before.guild.name)
    username = str(before.author)
    prvni = str(before.content)
    potom = str(after.content)
    print(f'Zpráva "{prvni}" byla změněna na "{potom}" od {username} ({server})')

#logace smazání zprávy
@bot.event
async def on_message_delete(message):
    zprava = str(message.content)
    username = str(message.author)
    server = str(message.guild.name)
    channel = str(message.channel.name)
    print(f'Zpráva "{zprava}" od {username} v roomce {channel} na serveru {server} byla smazána')



#bot.ipc.start()
bot.run(TOKEN)
``` 
