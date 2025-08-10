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
import subprocess
from datetime import datetime
from gemini_api import ChatSession

DEFAULT_PREFIX = "!"
PREFIX_FILE = "prefixes.json"
WARNINGS_FILE = "warnings.json"
SETTINGS_FILE = "server_settings.json"

def get_version():
    try:
        version = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:%s'],
            stderr=subprocess.STDOUT
        ).decode('utf-8').strip()
        return version
    except Exception:
        return "Unknown Version"

CURRENT_VERSION = "Beta 0.4"

if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        custom_prefixes = json.load(f)
else:
    custom_prefixes = {}

async def determine_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX

    guild_id = str(message.guild.id)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    else:
        settings = {"guilds": {}}
    prefix = settings.get("guilds", {}).get(guild_id, {}).get("prefix", DEFAULT_PREFIX)
    return prefix

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

GUILD_ID = 535890114258141184 
TWITCH_CHANNEL = "bluecat201"
ANNOUNCEMENT_CHANNEL_ID = 592348081362829312
CLIENT_ID = "hkn3fxk347cduph95gem7n22u2xod9"
CLIENT_SECRET = "wf4j6ts074b94qvp2z44e7d4aha3e6"
YOUR_USER_ID = 443842350377336860
CO_OWNER_USER_ID = 1335248197467242519

# --- Custom Bot Class with setup_hook ---
class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=determine_prefix,
            intents=intents
        )

    async def setup_hook(self):
        print("Setting up the bot...")
        # Load all extensions from the cogs folder
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded extension: {filename}")
                except Exception as e:
                    print(f"Failed to load extension {filename}: {e}")

        # Sync commands globally
        try:
            synced_commands = await self.tree.sync()
            print(f"Synced {len(synced_commands)} commands globally!")
        except Exception as e:
            print(f"Error syncing global commands: {e}")

        # Additionally sync commands to each guild for immediate updates
        for guild in self.guilds:
            try:
                synced_commands = await self.tree.sync(guild=discord.Object(id=guild.id))
                print(f"Synced {len(synced_commands)} commands to guild: {guild.name}")
            except Exception as e:
                print(f"Error syncing commands to {guild.name}: {e}")

bot = CustomBot()

async def sync_commands(bot_instance):
    """Sync commands globally and to all guilds"""
    try:
        # Sync commands globally
        synced_commands = await bot_instance.tree.sync()
        print(f"Synced {len(synced_commands)} commands globally!")
        
        # Additionally sync commands to each guild for immediate updates
        for guild in bot_instance.guilds:
            try:
                synced_commands = await bot_instance.tree.sync(guild=discord.Object(id=guild.id))
                print(f"Synced {len(synced_commands)} commands to guild: {guild.name}")
            except Exception as e:
                print(f"Error syncing commands to {guild.name}: {e}")
    except Exception as e:
        print(f"Error syncing global commands: {e}")

# --- SLASH COMMANDS ---
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

# --- NORMAL COMMANDS ---
@bot.command(aliases=['Blackcat','BLACKCAT'])
async def blackcat(ctx):
    await ctx.send("Alive and lost")

@bot.command(aliases=['Bluecat','BLUECAT'])
async def bluecat(ctx):
    await ctx.send("Not femboy")

@bot.command(aliases=['Info','INFO'])
async def info(ctx):
    await ctx.send(f"The bot was created as my long-term graduation project \nRelease date of the first alpha version: 5.9.2021 \nRelease date of the first beta version: 30.9.2021\nProgrammed in python \nIf you have any comments, advice or ideas for the bot, you can write them on the support server. \nThe number of servers I'm on: {len(bot.guilds)}\nCurrent version: {CURRENT_VERSION} \nDeveloper: Bluecat201")

@bot.command(aliases=['Invite','INVITE'])
async def invite(ctx):
    await ctx.send("Here is my invite: https://discord.com/api/oauth2/authorize?client_id=883325865474269192&permissions=8&scope=bot%20applications.commands")

@bot.command(aliases=['Ping','PING'])
async def ping(ctx):
    await ctx.send('Pong! {0}ms'.format(round(bot.latency, 1)))

@bot.command(aliases=['Support','SUPPORT'])
async def support(ctx):
    await ctx.send("Here is my support server: https://discord.gg/QmB2Ang4vr")

@bot.command(aliases=['Twitch','TWITCH'])
async def twitch(ctx):
    await ctx.send("Here is developer twitch channel: https://www.twitch.tv/bluecat201")

# --- AI Chatbot ---
chat_session = ChatSession()
@bot.event
async def on_message(message):
    IGNORED_CHANNELS = [648557196837388289]
    if message.author.bot:
        return
    if message.channel.id in IGNORED_CHANNELS:
        return

    if bot.user.mentioned_in(message):
        query = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        async with message.channel.typing():
            response = await chat_session.send_message(query)
        await message.reply(response)
    await bot.process_commands(message)

@bot.command()
async def reset(ctx):
    if ctx.author.id != YOUR_USER_ID and ctx.author.id != CO_OWNER_USER_ID:
        await ctx.send("This command can only be used by the owner of the bot.")
        return
    await ctx.send("Bot is reseting...")
    await bot.close()

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
            commit = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=format:%h - %s (%an)'], 
                stderr=subprocess.STDOUT
            ).decode('utf-8').strip()
            version = f"{CURRENT_VERSION} ({get_version()})"
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

@bot.command(name="prefix")
@commands.has_permissions(administrator=True)
async def change_prefix(ctx, prefix: str):
    if not prefix:
        await ctx.send("You need to specify a prefix.")
        return
    guild_id = str(ctx.guild.id)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    else:
        settings = {"guilds": {}}
    if guild_id not in settings.get("guilds", {}):
        settings["guilds"][guild_id] = {}
    settings["guilds"][guild_id]["prefix"] = prefix
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
    await ctx.send(f"Prefix changed to: `{prefix}`")

# --- LOGGING EVENTS ---
@bot.event
async def on_ready():
    print(f'Connected to bot: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    await bot.change_presence(activity=discord.Streaming(name=f'{CURRENT_VERSION}', url='https://www.twitch.tv/bluecatlive'))
    channel_id = 1325107856801923113
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="Bot is Ready! ✅", 
            description=f"Version: {CURRENT_VERSION}",
            color=discord.Color.green()
        )
        embed.add_field(name="Git Commit", value=get_version(), inline=False)
        embed.set_footer(text=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await channel.send(embed=embed)
    else:
        print(f'Channel with ID {channel_id} not found.')

@bot.event
async def on_member_join(member):
    server = str(member.guild.name)
    print(f'{member} joined {server}')

@bot.event
async def on_guild_join(guild):
    print(f'Bot was added to: {guild}')

@bot.event
async def on_guild_remove(guild):
    print(f'Bot was removed from: {guild}')

@bot.event
async def on_member_remove(member):
    server = str(member.guild.name)
    print(f'{member} left {server}')

@bot.event
async def on_guild_role_create(role):
    server = str(role.guild.name)
    print(f'Role {role} was created on [{server}]')

@bot.event
async def on_guild_role_delete(role):
    server = str(role.guild.name)
    print(f'Role {role} was deleted on [{server}]')

@bot.event
async def on_guild_role_update(before,after):
    server = str(before.guild.name)
    print(f'Role {before} was changed to {after} on {server}')

@bot.event
async def on_message_edit(before,after):
    server = str(before.guild.name)
    username = str(before.author)
    prvni = str(before.content)
    potom = str(after.content)
    print(f'Message "{prvni}" was changed to "{potom}" by {username} ({server})')

@bot.event
async def on_message_delete(message):
    zprava = str(message.content)
    username = str(message.author)
    server = str(message.guild.name)
    channel = str(message.channel.name)
    print(f'Message "{zprava}" by {username} in {channel} on {server} was deleted')

# --- TOKEN LOAD & RUN ---
with open("config.json", "r") as file:
    config = json.load(file)
    TOKEN = config["token"]

bot.run(TOKEN)
