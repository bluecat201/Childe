import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
from db_helpers import db_helpers

# Now using database instead of JSON files

# Helper functions now use database
db_helper = DatabaseHelpers()

def is_leveling_enabled(guild_id):
    return db_helper.get_leveling_settings(guild_id).get('enabled', True)

def is_channel_ignored(guild_id, channel_id):
    ignored_channels = db_helper.get_ignored_channels(guild_id)
    return str(channel_id) in ignored_channels

def get_level_up_channel(guild_id):
    return db_helper.get_level_up_channel(guild_id)

def get_mention_preference(user_id):
    return db_helper.get_user_preference(user_id, 'mention_on_levelup', True)

class LevelingSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_helpers = DatabaseHelpers()

    @app_commands.command(name="set_ignore_channel", description="Sets a channel to be ignored for leveling")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        channel_id = channel.id
        
        if self.db_helpers.add_ignored_channel(guild_id, channel_id):
            await interaction.response.send_message(f"Channel {channel.mention} was added to the ignored list.")
        else:
            await interaction.response.send_message("This channel is already ignored.")

    @app_commands.command(name="remove_ignore_channel", description="Removes a channel from the ignored list")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        channel_id = channel.id
        
        if self.db_helpers.remove_ignored_channel(guild_id, channel_id):
            await interaction.response.send_message(f"Channel {channel.mention} was removed from the ignored list.")
        else:
            await interaction.response.send_message("This channel is not in the ignored list.")

    @app_commands.command(name="set_level_up_channel", description="Sets a channel for level up announcements.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_up_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        
        self.db_helpers.set_level_up_channel(guild_id, channel.id)
        await interaction.response.send_message(f"Channel {channel.mention} was set for level up announcements.")

    @app_commands.command(name="reset_level_up_channel", description="Resets the level up announcement channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_level_up_channel(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if self.db_helpers.get_level_up_channel(guild_id):
            self.db_helpers.set_level_up_channel(guild_id, None)
            await interaction.response.send_message("Level up announcement channel was reset.")
        else:
            await interaction.response.send_message("No level up announcement channel was set.")

    @app_commands.command(name="toggle_leveling", description="Leveling system on/off.")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_leveling(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        current_state = self.db_helpers.get_leveling_settings(guild_id).get('enabled', True)
        new_state = not current_state
        self.db_helpers.update_leveling_settings(guild_id, enabled=new_state)

        state_message = "ON" if new_state else "OFF"
        await interaction.response.send_message(f"Leveling system: {state_message}.")

    @app_commands.command(name="leaderboard", description="Displays the top 10 users in the leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        leaderboard_data = self.db_helpers.get_leaderboard(guild_id, limit=10)
        
        if not leaderboard_data:
            await interaction.response.send_message("No users in the leaderboard yet.")
            return

        leaderboard_text = ""
        for i, (user_id, level, total_xp, messages) in enumerate(leaderboard_data, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                leaderboard_text += f"{i}. {user.name}: Level {level} ({total_xp} XP, {messages} messages)\n"
            except:
                leaderboard_text += f"{i}. Unknown User: Level {level} ({total_xp} XP, {messages} messages)\n"

        embed = discord.Embed(title="Top 10 users", description=leaderboard_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="Displays your (or someone else's) level and XP.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        guild_id = interaction.guild.id
        user_id = member.id

        user_data = self.db_helpers.get_user_level_data(user_id, guild_id)
        
        if user_data:
            level, total_xp, messages = user_data
            await interaction.response.send_message(f"{member.mention} has level {level}, {total_xp} XP and sent {messages} messages.")
        else:
            await interaction.response.send_message(f"{member.mention} has no level data yet.")

    @app_commands.command(name="toggle_mention", description="Toggles mention on level up.")
    async def toggle_mention(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        current_pref = self.db_helpers.get_user_preference(user_id, 'mention_on_levelup', True)
        new_pref = not current_pref
        self.db_helpers.set_user_preference(user_id, 'mention_on_levelup', new_pref)
        
        state_message = "ON" if new_pref else "OFF"
        await interaction.response.send_message(f"Mention toggle is now: {state_message}.")

async def setup(bot):
    await bot.add_cog(LevelingSlash(bot))
