import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

SETTINGS_FILE = "server_settings.json"
LEVELING_FILE = "leveling.json"

if os.path.exists(LEVELING_FILE):
    with open(LEVELING_FILE, "r") as f:
        leveling_data = json.load(f)
else:
    leveling_data = {}

if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        settings_data = json.load(f)
else:
    settings_data = {"guilds": {}, "users": {}}

def get_guild_settings(guild_id):
    guild_id = str(guild_id)
    if guild_id not in settings_data["guilds"]:
        settings_data["guilds"][guild_id] = {}
    
    return settings_data["guilds"][guild_id]

def is_leveling_enabled(guild_id):
    guild_id = str(guild_id)
    guild_settings = get_guild_settings(guild_id)
    
    if "leveling" not in guild_settings:
        guild_settings["leveling"] = {"enabled": True}
        
    return guild_settings["leveling"].get("enabled", True)

def is_channel_ignored(guild_id, channel_id):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    guild_settings = get_guild_settings(guild_id)
    
    return channel_id in guild_settings.get("ignored_channels", [])

def get_level_up_channel(guild_id):
    guild_id = str(guild_id)
    guild_settings = get_guild_settings(guild_id)
    
    if "leveling" not in guild_settings:
        guild_settings["leveling"] = {}
        
    return guild_settings["leveling"].get("level_up_channel_id")

def get_mention_preference(user_id):
    user_id = str(user_id)
    
    if "users" not in settings_data:
        settings_data["users"] = {}
        
    if user_id not in settings_data["users"]:
        settings_data["users"][user_id] = {}
        
    return settings_data["users"][user_id].get("mention_on_levelup", True)

async def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_data, f, indent=4)

async def save_leveling_data():
    with open(LEVELING_FILE, "w") as f:
        json.dump(leveling_data, f, indent=4)

class LevelingSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_ignore_channel", description="Sets a channel to be ignored for leveling")
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
            await interaction.response.send_message(f"Channel {channel.mention} was added to the ignored list.")
        else:
            await interaction.response.send_message("This channel is already ignored.")

    @app_commands.command(name="remove_ignore_channel", description="Removes a channel from the ignored list")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        
        guild_settings = get_guild_settings(guild_id)
        
        if "ignored_channels" in guild_settings and channel_id in guild_settings["ignored_channels"]:
            guild_settings["ignored_channels"].remove(channel_id)
            await save_settings()
            await interaction.response.send_message(f"Channel {channel.mention} was removed from the ignored list.")
        else:
            await interaction.response.send_message("This channel is not in the ignored list.")

    @app_commands.command(name="set_level_up_channel", description="Sets a channel for level up announcements.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_up_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" not in guild_settings:
            guild_settings["leveling"] = {}
            
        guild_settings["leveling"]["level_up_channel_id"] = str(channel.id)
        await save_settings()
        await interaction.response.send_message(f"Channel {channel.mention} was set for level up announcements.")

    @app_commands.command(name="reset_level_up_channel", description="Resets the level up announcement channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_level_up_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" in guild_settings and "level_up_channel_id" in guild_settings["leveling"]:
            del guild_settings["leveling"]["level_up_channel_id"]
            await save_settings()
            await interaction.response.send_message("Level up announcement channel was reset.")
        else:
            await interaction.response.send_message("No level up announcement channel was set.")

    @app_commands.command(name="toggle_leveling", description="Leveling system on/off.")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_leveling(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" not in guild_settings:
            guild_settings["leveling"] = {}
            
        current_state = guild_settings["leveling"].get("enabled", True)
        guild_settings["leveling"]["enabled"] = not current_state
        await save_settings()

        state_message = "ON" if guild_settings["leveling"]["enabled"] else "OFF"
        await interaction.response.send_message(f"Leveling system: {state_message}.")

    @app_commands.command(name="leaderboard", description="Displays the top 10 users in the leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id not in leveling_data or not leveling_data[guild_id]:
            await interaction.response.send_message("No users in the leaderboard yet.")
            return

        sorted_users = sorted(leveling_data[guild_id].items(), key=lambda x: (x[1]['level'], x[1]['total_xp']), reverse=True)
        leaderboard_text = ""

        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text += f"{i}. {user.name}: Level {data['level']} ({data['total_xp']} XP, {data['messages']} messages)\n"

        embed = discord.Embed(title="Top 10 users", description=leaderboard_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="Displays your (or someone else's) level and XP.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id in leveling_data and user_id in leveling_data[guild_id]:
            user_data = leveling_data[guild_id][user_id]
            await interaction.response.send_message(f"{member.mention} has level {user_data['level']}, {user_data['total_xp']} XP and sent {user_data['messages']} messages.")
        else:
            await interaction.response.send_message(f"{member.mention} has no level data yet.")

    @app_commands.command(name="toggle_mention", description="Toggles mention on level up.")
    async def toggle_mention(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if "users" not in settings_data:
            settings_data["users"] = {}
            
        if user_id not in settings_data["users"]:
            settings_data["users"][user_id] = {}
            
        current_pref = settings_data["users"][user_id].get("mention_on_levelup", True)
        settings_data["users"][user_id]["mention_on_levelup"] = not current_pref
        await save_settings()
        
        state_message = "ON" if settings_data["users"][user_id]["mention_on_levelup"] else "OFF"
        await interaction.response.send_message(f"Mention toggle is now: {state_message}.")

async def setup(bot):
    await bot.add_cog(LevelingSlash(bot))
