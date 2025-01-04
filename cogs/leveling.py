import discord
import random
import json
import os
from discord.ext import commands

LEVELING_FILE = "leveling.json"
IGNORED_CHANNELS_FILE = "ignored_channels.json"
LEVEL_UP_CHANNELS_FILE = "level_up_channels.json"
LEVELING_ENABLED_FILE = "leveling_enabled.json"

# Načtení nebo inicializace dat
if os.path.exists(LEVELING_FILE):
    with open(LEVELING_FILE, "r") as f:
        leveling_data = json.load(f)
else:
    leveling_data = {}

if os.path.exists(IGNORED_CHANNELS_FILE):
    with open(IGNORED_CHANNELS_FILE, "r") as f:
        ignored_channels = json.load(f)
else:
    ignored_channels = {}

if os.path.exists(LEVEL_UP_CHANNELS_FILE):
    with open(LEVEL_UP_CHANNELS_FILE, "r") as f:
        level_up_channels = json.load(f)
else:
    level_up_channels = {}

if os.path.exists(LEVELING_ENABLED_FILE):
    with open(LEVELING_ENABLED_FILE, "r") as f:
        leveling_enabled = json.load(f)
else:
    leveling_enabled = {}

# Funkce pro uložení dat
async def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_xp(self, user_id, guild_id, xp_to_add):
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)

        if guild_id_str not in leveling_data:
            leveling_data[guild_id_str] = {}

        if user_id_str not in leveling_data[guild_id_str]:
            leveling_data[guild_id_str][user_id_str] = {"xp": 0, "level": 1, "messages": 0, "total_xp": 0}

        user_data = leveling_data[guild_id_str][user_id_str]
        user_data["messages"] += 1
        user_data["total_xp"] += xp_to_add
        user_data["xp"] += xp_to_add

        xp = user_data["xp"]
        level = user_data["level"]

        xp_needed = level * 100
        if xp >= xp_needed:
            user_data["level"] += 1
            user_data["xp"] -= xp_needed
            return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        if not leveling_enabled.get(guild_id, True):
            return

        if guild_id in ignored_channels and channel_id in ignored_channels[guild_id]:
            return

        leveled_up = await self.add_xp(message.author.id, message.guild.id, random.randint(5, 10))
        await save_data(LEVELING_FILE, leveling_data)

        if leveled_up:
            level_up_channel_id = level_up_channels.get(guild_id, message.channel.id)
            level_up_channel = self.bot.get_channel(int(level_up_channel_id))
            if level_up_channel:
                await level_up_channel.send(f"Gratulujeme, {message.author.mention}! Dosáhl(a) jsi úrovně {leveling_data[guild_id][str(message.author.id)]['level']}!")

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def set_ignore_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        if guild_id not in ignored_channels:
            ignored_channels[guild_id] = []

        if channel_id not in ignored_channels[guild_id]:
            ignored_channels[guild_id].append(channel_id)
            await save_data(IGNORED_CHANNELS_FILE, ignored_channels)
            await ctx.send(f"Kanál {channel.mention} byl přidán do seznamu ignorovaných.")
        else:
            await ctx.send("Tento kanál je již ignorován.")

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def remove_ignore_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        if guild_id in ignored_channels and channel_id in ignored_channels[guild_id]:
            ignored_channels[guild_id].remove(channel_id)
            await save_data(IGNORED_CHANNELS_FILE, ignored_channels)
            await ctx.send(f"Kanál {channel.mention} byl odebrán ze seznamu ignorovaných.")
        else:
            await ctx.send("Tento kanál není ignorován.")

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def set_level_up_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        level_up_channels[guild_id] = str(channel.id)
        await save_data(LEVEL_UP_CHANNELS_FILE, level_up_channels)
        await ctx.send(f"Kanál {channel.mention} byl nastaven pro oznámení o zvýšení úrovně.")

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def reset_level_up_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in level_up_channels:
            del level_up_channels[guild_id]
            await save_data(LEVEL_UP_CHANNELS_FILE, level_up_channels)
            await ctx.send("Kanál pro oznámení o zvýšení úrovně byl resetován.")
        else:
            await ctx.send("Kanál pro oznámení nebyl nastaven.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggle_leveling(self, ctx):
        guild_id = str(ctx.guild.id)
        current_state = leveling_enabled.get(guild_id, True)
        leveling_enabled[guild_id] = not current_state
        await save_data(LEVELING_ENABLED_FILE, leveling_enabled)

        state_message = "zapnutý" if leveling_enabled[guild_id] else "vypnutý"
        await ctx.send(f"Leveling systém byl nyní {state_message}.")

    @commands.command()
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in leveling_data or not leveling_data[guild_id]:
            await ctx.send("Nikdo zatím nezískal žádné XP.")
            return

        sorted_users = sorted(leveling_data[guild_id].items(), key=lambda x: (x[1]['level'], x[1]['total_xp']), reverse=True)
        leaderboard_text = ""

        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text += f"{i}. {user.name}: Úroveň {data['level']} ({data['total_xp']} celkových XP, {data['messages']} zpráv)\n"

        embed = discord.Embed(title="Top 10 hráčů", description=leaderboard_text, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in leveling_data and user_id in leveling_data[guild_id]:
            user_data = leveling_data[guild_id][user_id]
            await ctx.send(f"{member.mention} má úroveň {user_data['level']}, {user_data['total_xp']} celkových XP a poslal(a) {user_data['messages']} zpráv.")
        else:
            await ctx.send(f"{member.mention} zatím nemá žádnou úroveň ani XP.")

async def setup(bot):
    await bot.add_cog(Leveling(bot))