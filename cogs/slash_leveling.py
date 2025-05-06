import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

# Centralized settings file
SETTINGS_FILE = "server_settings.json"
LEVELING_FILE = "leveling.json"  # Keep separate file for XP data

# Load XP data
if os.path.exists(LEVELING_FILE):
    with open(LEVELING_FILE, "r") as f:
        leveling_data = json.load(f)
else:
    leveling_data = {}

# Load settings data
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        settings_data = json.load(f)
else:
    settings_data = {"guilds": {}, "users": {}}

# Helper functions for settings management
def get_guild_settings(guild_id):
    """Get guild settings, creating default structure if needed"""
    guild_id = str(guild_id)
    if guild_id not in settings_data["guilds"]:
        settings_data["guilds"][guild_id] = {}
    
    return settings_data["guilds"][guild_id]

def is_leveling_enabled(guild_id):
    """Check if leveling is enabled for a guild"""
    guild_id = str(guild_id)
    guild_settings = get_guild_settings(guild_id)
    
    if "leveling" not in guild_settings:
        guild_settings["leveling"] = {"enabled": True}
        
    return guild_settings["leveling"].get("enabled", True)

def is_channel_ignored(guild_id, channel_id):
    """Check if a channel is in the ignored list"""
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    guild_settings = get_guild_settings(guild_id)
    
    return channel_id in guild_settings.get("ignored_channels", [])

def get_level_up_channel(guild_id):
    """Get the level up announcement channel for a guild"""
    guild_id = str(guild_id)
    guild_settings = get_guild_settings(guild_id)
    
    if "leveling" not in guild_settings:
        guild_settings["leveling"] = {}
        
    return guild_settings["leveling"].get("level_up_channel_id")

def get_mention_preference(user_id):
    """Get mention preference for a user"""
    user_id = str(user_id)
    
    if "users" not in settings_data:
        settings_data["users"] = {}
        
    if user_id not in settings_data["users"]:
        settings_data["users"][user_id] = {}
        
    return settings_data["users"][user_id].get("mention_on_levelup", True)

async def save_settings():
    """Save settings to centralized file"""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_data, f, indent=4)

async def save_leveling_data():
    """Save XP data to separate file"""
    with open(LEVELING_FILE, "w") as f:
        json.dump(leveling_data, f, indent=4)

class LevelingSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_ignore_channel", description="Přidá kanál do seznamu ignorovaných.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        
        guild_settings = get_guild_settings(guild_id)
        
        if "ignored_channels" not in guild_settings:
            guild_settings["ignored_channels"] = []
            
        if channel_id not in guild_settings["ignored_channels"]:
            guild_settings["ignored_channels"].append(channel_id)
            await save_settings()
            await interaction.response.send_message(f"Kanál {channel.mention} byl přidán do seznamu ignorovaných.")
        else:
            await interaction.response.send_message("Tento kanál je již ignorován.")

    @app_commands.command(name="remove_ignore_channel", description="Odebere kanál ze seznamu ignorovaných.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        
        guild_settings = get_guild_settings(guild_id)
        
        if "ignored_channels" in guild_settings and channel_id in guild_settings["ignored_channels"]:
            guild_settings["ignored_channels"].remove(channel_id)
            await save_settings()
            await interaction.response.send_message(f"Kanál {channel.mention} byl odebrán ze seznamu ignorovaných.")
        else:
            await interaction.response.send_message("Tento kanál není ignorován.")

    @app_commands.command(name="set_level_up_channel", description="Nastaví kanál pro oznámení o zvýšení úrovně.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_up_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" not in guild_settings:
            guild_settings["leveling"] = {}
            
        guild_settings["leveling"]["level_up_channel_id"] = str(channel.id)
        await save_settings()
        await interaction.response.send_message(f"Kanál {channel.mention} byl nastaven pro oznámení o zvýšení úrovně.")

    @app_commands.command(name="reset_level_up_channel", description="Resetuje kanál pro oznámení o zvýšení úrovně.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_level_up_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" in guild_settings and "level_up_channel_id" in guild_settings["leveling"]:
            del guild_settings["leveling"]["level_up_channel_id"]
            await save_settings()
            await interaction.response.send_message("Kanál pro oznámení o zvýšení úrovně byl resetován.")
        else:
            await interaction.response.send_message("Kanál pro oznámení nebyl nastaven.")

    @app_commands.command(name="toggle_leveling", description="Přepíná zapnutí/vypnutí levelovacího systému.")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_leveling(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" not in guild_settings:
            guild_settings["leveling"] = {}
            
        current_state = guild_settings["leveling"].get("enabled", True)
        guild_settings["leveling"]["enabled"] = not current_state
        await save_settings()

        state_message = "zapnutý" if guild_settings["leveling"]["enabled"] else "vypnutý"
        await interaction.response.send_message(f"Levelovací systém byl nyní {state_message}.")

    @app_commands.command(name="leaderboard", description="Zobrazí top 10 hráčů.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id not in leveling_data or not leveling_data[guild_id]:
            await interaction.response.send_message("Nikdo zatím nezískal žádné XP.")
            return

        sorted_users = sorted(leveling_data[guild_id].items(), key=lambda x: (x[1]['level'], x[1]['total_xp']), reverse=True)
        leaderboard_text = ""

        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text += f"{i}. {user.name}: Úroveň {data['level']} ({data['total_xp']} celkových XP, {data['messages']} zpráv)\n"

        embed = discord.Embed(title="Top 10 hráčů", description=leaderboard_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="Zobrazí úroveň a XP uživatele.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id in leveling_data and user_id in leveling_data[guild_id]:
            user_data = leveling_data[guild_id][user_id]
            await interaction.response.send_message(f"{member.mention} má úroveň {user_data['level']}, {user_data['total_xp']} celkových XP a poslal(a) {user_data['messages']} zpráv.")
        else:
            await interaction.response.send_message(f"{member.mention} zatím nemá žádnou úroveň ani XP.")

    @app_commands.command(name="toggle_mention", description="Přepíná označení při zvýšení úrovně.")
    async def toggle_mention(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if "users" not in settings_data:
            settings_data["users"] = {}
            
        if user_id not in settings_data["users"]:
            settings_data["users"][user_id] = {}
            
        current_pref = settings_data["users"][user_id].get("mention_on_levelup", True)
        settings_data["users"][user_id]["mention_on_levelup"] = not current_pref
        await save_settings()
        
        state_message = "zapnuto" if settings_data["users"][user_id]["mention_on_levelup"] else "vypnuto"
        await interaction.response.send_message(f"Označení při zvýšení úrovně bylo nyní {state_message}.")

async def setup(bot):
    await bot.add_cog(LevelingSlash(bot))
