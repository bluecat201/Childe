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

DEFAULT_PREFIX = "!"
PREFIX_FILE = "prefixes.json"
WARNINGS_FILE = "warnings.json"

# Načítání prefixů ze souboru
if os.path.exists(PREFIX_FILE):
    with open(PREFIX_FILE, "r") as f:
        custom_prefixes = json.load(f)
else:
    custom_prefixes = {}

async def determine_prefix(bot, message):
    if not message.guild: 
        return DEFAULT_PREFIX

    guild_id = str(message.guild.id)
    
    # Načtení prefixů
    if os.path.exists(PREFIX_FILE):
        with open(PREFIX_FILE, "r") as f:
            prefixes = json.load(f)
    else:
        prefixes = {}

    # Vrátí uložený prefix nebo výchozí, pokud neexistuje
    return prefixes.get(guild_id, DEFAULT_PREFIX)

# Nastavení základních proměnných
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=determine_prefix, intents=intents)

# Event: Bot je připraven
@bot.event
async def on_ready():
    print(f'Connected to bot: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    await sync_commands(bot)
    await load_extensions()
    await bot.change_presence(activity=discord.Streaming(name='Beta v0.2.7', url='https://www.twitch.tv/Bluecat201'))

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
@bot.tree.command(name="rps", description="Zahraj si kámen, nůžky, papír")
@app_commands.choices(option=[
    app_commands.Choice(name="Kámen", value="1"),
    app_commands.Choice(name="Nůžky", value="2"),
    app_commands.Choice(name="Papír", value="3"),
])
async def rps(interaction: discord.Interaction, option: app_commands.Choice[str]):
    pc = random.randint(1, 3)
    outcomes = {
        ("1", 1): "Kámen vs Kámen\n REMÍZA",
        ("1", 2): "Kámen vs Nůžky\n VYHRÁL JSI",
        ("1", 3): "Kámen vs Papír\n PROHRÁL JSI",
        ("2", 1): "Nůžky vs Kámen\n PROHRÁL JSI",
        ("2", 2): "Nůžky vs Nůžky\n REMÍZA",
        ("2", 3): "Nůžky vs Papír\n VYHRÁL JSI",
        ("3", 1): "Papír vs Kámen\n VYHRÁL JSI",
        ("3", 2): "Papír vs Nůžky\n PROHRÁL JSI",
        ("3", 3): "Papír vs Papír\n REMÍZA",
    }
    await interaction.response.send_message(outcomes[(option.value, pc)])

# Slash příkaz: Odkazy
@bot.tree.command(name="link", description="Moje odkazy")
@app_commands.choices(option=[
    app_commands.Choice(name="Twitch", value="Můj twitch: https://www.twitch.tv/bluecat201"),
    app_commands.Choice(name="Support", value="Zde najdete moji podporu: https://dsc.gg/bluecat | https://discord.gg/43H2HxB3Ax"),
    app_commands.Choice(name="Youtube", value="hl. kanál: https://www.youtube.com/channel/UCwY2CDHkQGmCIwgVgEJKt8w"),
    app_commands.Choice(name="Instagram", value="Můj IG: https://www.instagram.com/bluecat221/"),
    app_commands.Choice(name="Web", value="Můj web: https://bluecat201.weebly.com/"),
])
async def link(interaction: discord.Interaction, option: app_commands.Choice[str]):
    await interaction.response.send_message(option.value)

# Načítání tokenu ze souboru
with open("config.json", "r") as file:
    config = json.load(file)
    TOKEN = config["token"]

#|non-slash|  
# NORMAL COMMANDS
@bot.command(aliases=['Bluecat','BLUECAT'])
async def bluecat(ctx):
    await ctx.send("Není femboy")

@bot.command()
async def d(ctx):
    await ctx.send("<:cicisrdicko:849285560832360531>")


#info
@bot.command(aliases=['Info','INFO'])
async def info(ctx):
    await ctx.send(f"Bot vznikal jako moje dlouhodobá maturitní práce :)\nDatum vydání první alpha verze: 5.9.2021 \nDatum vydání první beta verze: 30.9.2021\nNaprogramováno v pythonu \nPokud máte jakékoliv poznámky, rady či nápady pro bota, můžete je napsat na !support server. ;)\nPočet serverů, na kterých jsem: {len(bot.guilds)}\nVerze bota: Beta 0.2.7 \nDeveloper: Bluecat201")

#invite bota
@bot.command(aliases=['Invite','INVITE'])
async def invite(ctx):
    await ctx.send("Zde je můj invite: https://discord.com/api/oauth2/authorize?client_id=883325865474269192&permissions=8&scope=bot%20applications.commands")

#ping
@bot.command(aliases=['Ping','PING'])
async def ping(ctx):
    await ctx.send('Pong! {0}ms'.format(round(bot.latency, 1)))

#support
@bot.command(aliases=['Support','SUPPORT'])
async def support(ctx):
    await ctx.send("Zde najdete moji podporu: https://dsc.gg/bluecat | https://discord.gg/43H2HxB3Ax")

#twitch
@bot.command(aliases=['Twitch','TWITCH'])
async def twitch(ctx):
    await ctx.send("Zde je twitch mého stvořitele: https://www.twitch.tv/bluecat201")

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