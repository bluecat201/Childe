import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

# Načtení nebo inicializace dat
LEVELING_FILE = "leveling.json"
IGNORED_CHANNELS_FILE = "ignored_channels.json"
LEVEL_UP_CHANNELS_FILE = "level_up_channels.json"
LEVELING_ENABLED_FILE = "leveling_enabled.json"
MENTION_PREFS_FILE = "mention_prefs.json"

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

if os.path.exists(MENTION_PREFS_FILE):
    with open(MENTION_PREFS_FILE, "r") as f:
        mention_prefs = json.load(f)
else:
    mention_prefs = {}

async def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

class LevelingSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_ignore_channel", description="Přidá kanál do seznamu ignorovaných.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        if guild_id not in ignored_channels:
            ignored_channels[guild_id] = []

        if channel_id not in ignored_channels[guild_id]:
            ignored_channels[guild_id].append(channel_id)
            await save_data(IGNORED_CHANNELS_FILE, ignored_channels)
            await interaction.response.send_message(f"Kanál {channel.mention} byl přidán do seznamu ignorovaných.")
        else:
            await interaction.response.send_message("Tento kanál je již ignorován.")

    @app_commands.command(name="remove_ignore_channel", description="Odebere kanál ze seznamu ignorovaných.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        if guild_id in ignored_channels and channel_id in ignored_channels[guild_id]:
            ignored_channels[guild_id].remove(channel_id)
            await save_data(IGNORED_CHANNELS_FILE, ignored_channels)
            await interaction.response.send_message(f"Kanál {channel.mention} byl odebrán ze seznamu ignorovaných.")
        else:
            await interaction.response.send_message("Tento kanál není ignorován.")

    @app_commands.command(name="set_level_up_channel", description="Nastaví kanál pro oznámení o zvýšení úrovně.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_up_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        level_up_channels[guild_id] = str(channel.id)
        await save_data(LEVEL_UP_CHANNELS_FILE, level_up_channels)
        await interaction.response.send_message(f"Kanál {channel.mention} byl nastaven pro oznámení o zvýšení úrovně.")

    @app_commands.command(name="reset_level_up_channel", description="Resetuje kanál pro oznámení o zvýšení úrovně.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_level_up_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id in level_up_channels:
            del level_up_channels[guild_id]
            await save_data(LEVEL_UP_CHANNELS_FILE, level_up_channels)
            await interaction.response.send_message("Kanál pro oznámení o zvýšení úrovně byl resetován.")
        else:
            await interaction.response.send_message("Kanál pro oznámení nebyl nastaven.")

    @app_commands.command(name="toggle_leveling", description="Přepíná zapnutí/vypnutí levelovacího systému.")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_leveling(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        current_state = leveling_enabled.get(guild_id, True)
        leveling_enabled[guild_id] = not current_state
        await save_data(LEVELING_ENABLED_FILE, leveling_enabled)

        state_message = "zapnutý" if leveling_enabled[guild_id] else "vypnutý"
        await interaction.response.send_message(f"Levelovací systém byl nyní {state_message}.")

    @app_commands.command(name="leaderboard", description="Zobrazí top 10 hráčů.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id not in leveling_data or not leveling_data[guild_id]:
            await interaction.response.send_message("Nikdo zatím nezískal žádné XP.")
            return

        sorted_users = sorted(leveling_data[guild_id].items(), key=lambda x: (x[1]['level'], x[1]['xp']), reverse=True)
        leaderboard_text = ""

        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text += f"{i}. {user.name}: Úroveň {data['level']} ({data['xp']} XP)\n"

        embed = discord.Embed(title="Top 10 hráčů", description=leaderboard_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="Zobrazí úroveň a XP uživatele.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id in leveling_data and user_id in leveling_data[guild_id]:
            user_data = leveling_data[guild_id][user_id]
            await interaction.response.send_message(f"{member.mention} má úroveň {user_data['level']} a {user_data['xp']} XP.")
        else:
            await interaction.response.send_message(f"{member.mention} zatím nemá žádnou úroveň ani XP.")

    @app_commands.command(name="toggle_mention", description="Přepíná označení při zvýšení úrovně.")
    async def toggle_mention(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        current_pref = mention_prefs.get(user_id, True)
        mention_prefs[user_id] = not current_pref
        await save_data(MENTION_PREFS_FILE, mention_prefs)

        state_message = "zapnuto" if mention_prefs[user_id] else "vypnuto"
        await interaction.response.send_message(f"Označení při zvýšení úrovně bylo nyní {state_message}.")

async def setup(bot):
    await bot.add_cog(LevelingSlash(bot))
