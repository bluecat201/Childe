import discord
import random
import json
import os
from discord.ext import commands

SETTINGS_FILE = "server_settings.json"
LEVELING_FILE = "leveling.json"  # Still keep separate file for XP data

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
    settings_data = {"guilds": {}}

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

# Function to save settings
async def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_data, f, indent=4)

# Function to save XP data
async def save_leveling_data():
    with open(LEVELING_FILE, "w") as f:
        json.dump(leveling_data, f, indent=4)

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

        # Check if leveling is enabled
        if not is_leveling_enabled(guild_id):
            return

        # Check if channel is ignored
        if is_channel_ignored(guild_id, channel_id):
            return

        # Add XP and check level up
        leveled_up = await self.add_xp(message.author.id, message.guild.id, random.randint(5, 10))
        await save_leveling_data()

        if leveled_up:
            # Get level up channel ID
            level_up_channel_id = get_level_up_channel(guild_id)
            
            # Default to current channel if no level up channel set
            channel_to_use = self.bot.get_channel(int(level_up_channel_id)) if level_up_channel_id else message.channel
            
            if channel_to_use:
                user_id_str = str(message.author.id)
                mention_user = get_mention_preference(message.author.id)
                mention_text = message.author.mention if mention_user else message.author.name

                await channel_to_use.send(
                    f"Congratulation, {mention_text}! Reached level {leveling_data[guild_id][user_id_str]['level']}!"
                )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_ignore_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        guild_settings = get_guild_settings(guild_id)
        
        if "ignored_channels" not in guild_settings:
            guild_settings["ignored_channels"] = []
            
        if channel_id not in guild_settings["ignored_channels"]:
            guild_settings["ignored_channels"].append(channel_id)
            await save_settings()
            await ctx.send(f"Channel {channel.mention} was added to list of ignored channels.")
        else:
            await ctx.send("This channel is already ignored.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_ignore_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        guild_settings = get_guild_settings(guild_id)
        
        if "ignored_channels" in guild_settings and channel_id in guild_settings["ignored_channels"]:
            guild_settings["ignored_channels"].remove(channel_id)
            await save_settings()
            await ctx.send(f"Channel {channel.mention} was deleted from list of ignored channels.")
        else:
            await ctx.send("This channel isn't ignored.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_level_up_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" not in guild_settings:
            guild_settings["leveling"] = {}
            
        guild_settings["leveling"]["level_up_channel_id"] = str(channel.id)
        await save_settings()
        await ctx.send(f"Channel {channel.mention} was set for announcement of level up.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset_level_up_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" in guild_settings and "level_up_channel_id" in guild_settings["leveling"]:
            del guild_settings["leveling"]["level_up_channel_id"]
            await save_settings()
            await ctx.send("Channel for announcement of level up was reset.")
        else:
            await ctx.send("Channel for announcement of level up wasn't set up.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggle_leveling(self, ctx):
        guild_id = str(ctx.guild.id)
        guild_settings = get_guild_settings(guild_id)
        
        if "leveling" not in guild_settings:
            guild_settings["leveling"] = {}
            
        current_state = guild_settings["leveling"].get("enabled", True)
        guild_settings["leveling"]["enabled"] = not current_state
        
        await save_settings()
        
        state_message = "on" if guild_settings["leveling"]["enabled"] else "off"
        await ctx.send(f"Level system is now {state_message}.")

    @commands.command()
    async def toggle_mention(self, ctx):
        user_id = str(ctx.author.id)
        
        if "users" not in settings_data:
            settings_data["users"] = {}
            
        if user_id not in settings_data["users"]:
            settings_data["users"][user_id] = {}
            
        current_pref = settings_data["users"][user_id].get("mention_on_levelup", True)
        settings_data["users"][user_id]["mention_on_levelup"] = not current_pref
        
        await save_settings()
        
        state_message = "on" if settings_data["users"][user_id]["mention_on_levelup"] else "off"
        await ctx.send(f"Mention at level up is now {state_message}.")

    # Leaderboard and level commands remain unchanged
    @commands.command()
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in leveling_data or not leveling_data[guild_id]:
            await ctx.send("Nobody has any xp right now.")
            return

        sorted_users = sorted(leveling_data[guild_id].items(), key=lambda x: (x[1]['level'], x[1]['total_xp']), reverse=True)
        leaderboard_text = ""

        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text += f"{i}. {user.name}: Level {data['level']} ({data['total_xp']} total XP, {data['messages']} messages)\n"

        embed = discord.Embed(title="Top 10 chatters", description=leaderboard_text, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in leveling_data and user_id in leveling_data[guild_id]:
            user_data = leveling_data[guild_id][user_id]
            await ctx.send(f"{member.mention} has level {user_data['level']}, {user_data['total_xp']} total XP and sent {user_data['messages']} messages.")
        else:
            await ctx.send(f"{member.mention} doesn't have any level and XP.")

async def setup(bot):
    await bot.add_cog(Leveling(bot))

