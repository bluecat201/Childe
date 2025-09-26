import discord
import random
import json
import os
from discord.ext import commands
from db_helpers import db_helpers

# Helper functions for settings management
async def get_guild_settings(guild_id):
    """Get guild settings from database"""
    settings_data = await db_helpers.get_server_settings()
    guild_id = str(guild_id)
    return settings_data.get("guilds", {}).get(guild_id, {})

async def is_leveling_enabled(guild_id):
    """Check if leveling is enabled for a guild"""
    from database import db
    if not db.connection or not db.connection.is_connected():
        return True  # Default to enabled if database not available
        
    cursor = db.connection.cursor()
    try:
        cursor.execute("SELECT enabled FROM leveling_enabled WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        return result[0] if result else True  # Default to enabled
    except Exception as e:
        print(f"Error checking leveling enabled: {e}")
        return True
    finally:
        cursor.close()

async def is_channel_ignored(guild_id, channel_id):
    """Check if a channel is in the ignored list"""
    from database import db
    if not db.connection or not db.connection.is_connected():
        return False  # Default to not ignored if database not available
        
    cursor = db.connection.cursor()
    try:
        cursor.execute("SELECT 1 FROM ignored_channels WHERE guild_id = %s AND channel_id = %s", (guild_id, channel_id))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking ignored channel: {e}")
        return False
    finally:
        cursor.close()

async def get_level_up_channel(guild_id):
    """Get the level up channel ID for a guild"""
    from database import db
    if not db.connection or not db.connection.is_connected():
        return None  # Default to no level up channel if database not available
        
    cursor = db.connection.cursor()
    try:
        cursor.execute("SELECT channel_id FROM level_up_channels WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting level up channel: {e}")
        return None
    finally:
        cursor.close()

async def get_mention_preference(user_id):
    """Get user's mention preference for level up messages"""
    from database import db
    if not db.connection or not db.connection.is_connected():
        return True  # Default to mentioning if database not available
        
    cursor = db.connection.cursor()
    try:
        cursor.execute("SELECT preferences FROM mention_prefs WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            import json
            prefs = json.loads(result[0]) if result[0] else {}
            return prefs.get("mention_on_levelup", True)
        return True  # Default to True
    except Exception as e:
        print(f"Error getting mention preference: {e}")
        return True
    finally:
        cursor.close()

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

    def add_xp(self, user_id, guild_id, xp_to_add):
        return db_helpers.update_user_xp(guild_id, user_id, xp_to_add, 1)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        channel_id = message.channel.id

        # Check if leveling is enabled
        if not await is_leveling_enabled(guild_id):
            return

        # Check if channel is ignored
        if await is_channel_ignored(guild_id, channel_id):
            return

        # Add XP and check level up
        leveled_up = self.add_xp(message.author.id, message.guild.id, random.randint(5, 10))

        if leveled_up:
            # Get level up channel ID
            level_up_channel_id = await get_level_up_channel(guild_id)
            
            # Default to current channel if no level up channel set
            channel_to_use = self.bot.get_channel(int(level_up_channel_id)) if level_up_channel_id else message.channel
            
            if channel_to_use:
                mention_user = await get_mention_preference(message.author.id)
                mention_text = message.author.mention if mention_user else message.author.name

                # Get user's current level from database
                from database import db
                current_level = 1  # Default level
                if db.connection and db.connection.is_connected():
                    cursor = db.connection.cursor()
                    try:
                        cursor.execute("SELECT level FROM leveling WHERE guild_id = %s AND user_id = %s", (guild_id, message.author.id))
                        result = cursor.fetchone()
                        current_level = result[0] if result else 1
                    except Exception as e:
                        print(f"Error getting current level: {e}")
                    finally:
                        cursor.close()

                await channel_to_use.send(
                    f"Congratulation, {mention_text}! Reached level {current_level}!"
                )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_ignore_channel(self, ctx, channel: discord.TextChannel):
        guild_id = ctx.guild.id
        channel_id = channel.id
        
        if not await is_channel_ignored(guild_id, channel_id):
            from database import db
            cursor = db.connection.cursor()
            try:
                cursor.execute("INSERT IGNORE INTO ignored_channels (guild_id, channel_id) VALUES (%s, %s)", (guild_id, channel_id))
            finally:
                cursor.close()
            await ctx.send(f"Channel {channel.mention} was added to list of ignored channels.")
        else:
            await ctx.send("This channel is already ignored.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_ignore_channel(self, ctx, channel: discord.TextChannel):
        guild_id = ctx.guild.id
        channel_id = channel.id
        
        if await is_channel_ignored(guild_id, channel_id):
            from database import db
            cursor = db.connection.cursor()
            try:
                cursor.execute("DELETE FROM ignored_channels WHERE guild_id = %s AND channel_id = %s", (guild_id, channel_id))
            finally:
                cursor.close()
            await ctx.send(f"Channel {channel.mention} was deleted from list of ignored channels.")
        else:
            await ctx.send("This channel isn't ignored.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_level_up_channel(self, ctx, channel: discord.TextChannel):
        guild_id = ctx.guild.id
        
        from database import db
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO level_up_channels (guild_id, channel_id) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
            """, (guild_id, channel.id))
        finally:
            cursor.close()
        await ctx.send(f"Channel {channel.mention} was set for announcement of level up.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset_level_up_channel(self, ctx):
        guild_id = ctx.guild.id
        
        level_up_channel_id = await get_level_up_channel(guild_id)
        if level_up_channel_id:
            from database import db
            cursor = db.connection.cursor()
            try:
                cursor.execute("DELETE FROM level_up_channels WHERE guild_id = %s", (guild_id,))
            finally:
                cursor.close()
            await ctx.send("Channel for announcement of level up was reset.")
        else:
            await ctx.send("Channel for announcement of level up wasn't set up.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggle_leveling(self, ctx):
        guild_id = ctx.guild.id
        
        current_state = await is_leveling_enabled(guild_id)
        new_state = not current_state
        
        from database import db
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO leveling_enabled (guild_id, enabled) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE enabled = VALUES(enabled)
            """, (guild_id, new_state))
        finally:
            cursor.close()
        
        state_message = "on" if new_state else "off"
        await ctx.send(f"Level system is now {state_message}.")

    @commands.command()
    async def toggle_mention(self, ctx):
        user_id = ctx.author.id
        
        current_pref = await get_mention_preference(user_id)
        new_pref = not current_pref
        
        from database import db
        cursor = db.connection.cursor()
        try:
            import json
            cursor.execute("""
                INSERT INTO mention_prefs (user_id, preferences) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE preferences = VALUES(preferences)
            """, (user_id, json.dumps({"mention_on_levelup": new_pref})))
        finally:
            cursor.close()
        
        state_message = "on" if new_pref else "off"
        await ctx.send(f"Mention at level up is now {state_message}.")

    @commands.command()
    async def leaderboard(self, ctx):
        guild_id = ctx.guild.id

        leaderboard_data = await db_helpers.get_guild_leaderboard(guild_id, 10)
        
        if not leaderboard_data:
            await ctx.send("Nobody has any xp right now.")
            return

        leaderboard_text = ""
        for i, data in enumerate(leaderboard_data, 1):
            try:
                user = await self.bot.fetch_user(int(data['user_id']))
                leaderboard_text += f"{i}. {user.name}: Level {data['level']} ({data['total_xp']} total XP, {data['messages']} messages)\n"
            except:
                leaderboard_text += f"{i}. Unknown User: Level {data['level']} ({data['total_xp']} total XP, {data['messages']} messages)\n"

        embed = discord.Embed(title="Top 10 chatters", description=leaderboard_text, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id = ctx.guild.id
        user_id = member.id

        from database import db
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT level, total_xp, messages FROM leveling WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
            result = cursor.fetchone()
            
            if result:
                level, total_xp, messages = result
                await ctx.send(f"{member.mention} has level {level}, {total_xp} total XP and sent {messages} messages.")
            else:
                await ctx.send(f"{member.mention} doesn't have any level and XP.")
        finally:
            cursor.close()

async def setup(bot):
    await bot.add_cog(Leveling(bot))

