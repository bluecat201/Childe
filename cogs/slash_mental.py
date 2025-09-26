import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from db_helpers import DatabaseHelpers

# Now using database for all mental health data

class Slash_Mental(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_helpers = DatabaseHelpers()
        
        # Get settings from database
        mental_health_config = self.db_helpers.get_mental_health_config()
        self.check_enabled = mental_health_config.get("check_enabled", False)
        self.channel_ids = mental_health_config.get("channels", [])
        self.ping_roles = mental_health_config.get("ping_roles", [])
        self.frequency = mental_health_config.get("frequency", 24)

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="enable", description="Enable mental health check")
    async def enable(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        self.check_enabled = True
        mental_health_settings = get_mental_health_settings()
        mental_health_settings["check_enabled"] = True
        self.save_settings()
        await interaction.response.send_message("Mental health check enabled.")

    @app_commands.command(name="disable", description="Disable mental health check")
    async def disable(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        self.check_enabled = False
        mental_health_settings = get_mental_health_settings()
        mental_health_settings["check_enabled"] = False
        self.save_settings()
        await interaction.response.send_message("Mental health check disabled.")

    @app_commands.command(name="addchannel", description="Add channel to send mental health check messages")
    async def addchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if channel.id not in self.channel_ids:
            self.channel_ids.append(channel.id)
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["channels"] = self.channel_ids
            self.save_settings()
            await interaction.response.send_message(f"Mental health check messages will also be sent to {channel.mention}.")
        else:
            await interaction.response.send_message(f"Channel {channel.mention} is already in the list.")

    @app_commands.command(name="removechannel", description="Remove channel from mental health check list")
    async def removechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if channel.id in self.channel_ids:
            self.channel_ids.remove(channel.id)
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["channels"] = self.channel_ids
            self.save_settings()
            await interaction.response.send_message(f"Channel {channel.mention} has been removed from the list.")
        else:
            await interaction.response.send_message(f"Channel {channel.mention} is not in the list.")

    @app_commands.command(name="setfrequency", description="Set frequency of mental health check")
    async def setfrequency(self, interaction: discord.Interaction, hours: int):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if hours < 1:
            await interaction.response.send_message("Frequency must be at least 1 hour.", ephemeral=True)
        else:
            self.frequency = hours
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["frequency"] = hours
            self.save_settings()
            await interaction.response.send_message(f"Mental health check frequency set to every {hours} hours.")

    @app_commands.command(name="stats", description="Get the stats for the server's mental health responses")
    async def stats(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in server_mood_data:
            await interaction.response.send_message("No data available for this server.", ephemeral=True)
            return

        guild_stats = server_mood_data[guild_id]
        response = f"Mental Health Check Stats:\n"
        for mood, count in guild_stats.items():
            response += f"{mood}: {count}\n"
        
        await interaction.response.send_message(response)

    @app_commands.command(name="respond", description="Respond to the mental health check-in")
    async def respond(self, interaction: discord.Interaction, mood: str):
        valid_moods = ["happy", "sad", "stressed", "calm", "tired", "motivated"]
        if mood not in valid_moods and mood != "others":
            await interaction.response.send_message(f"Invalid mood. Valid options are: {', '.join(valid_moods)} or 'others'.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        # Get current timestamp
        current_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Update user mood data
        if user_id not in user_mood_data:
            user_mood_data[user_id] = {m: 0 for m in valid_moods}
        if mood != "others":
            user_mood_data[user_id][mood] += 1

        # Update server mood data
        if guild_id not in server_mood_data:
            server_mood_data[guild_id] = {m: 0 for m in valid_moods}
        if mood != "others":
            server_mood_data[guild_id][mood] += 1
        else:
            await self.handle_others(interaction, guild_id, user_id)

        # Log the mood response
        if guild_id not in mood_dates_data:
            mood_dates_data[guild_id] = {}
        if user_id not in mood_dates_data[guild_id]:
            mood_dates_data[guild_id][user_id] = []
        
        mood_record = {
            "mood": mood,
            "date": current_date
        }
        mood_dates_data[guild_id][user_id].append(mood_record)

        # Save data back to files
        self.save_mood_data()

        # Send response only to the user who used the command (ephemeral message)
        await interaction.response.send_message(f"Thank you for responding! Your mood ({mood}) has been recorded.", ephemeral=True)

    async def handle_others(self, interaction, guild_id, user_id):
        if "others" not in server_mood_data[guild_id]:
            server_mood_data[guild_id]["others"] = {}

        if "others" not in user_mood_data[user_id]:
            user_mood_data[user_id]["others"] = {}

        await interaction.response.send_message("Please provide a brief description of your mood.", ephemeral=True)
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        try:
            description = await self.bot.wait_for("message", timeout=60.0, check=check)
            mood_description = description.content

            if mood_description not in server_mood_data[guild_id]["others"]:
                server_mood_data[guild_id]["others"][mood_description] = 1
            else:
                server_mood_data[guild_id]["others"][mood_description] += 1

            if mood_description not in user_mood_data[user_id]["others"]:
                user_mood_data[user_id]["others"] = 1
            else:
                user_mood_data[user_id]["others"] += 1

        except:
            await interaction.response.send_message("No response received, mood not recorded.", ephemeral=True)

    def save_settings(self):
        """Save settings to centralized settings file"""
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_data, f, indent=4)
    
    def save_mood_data(self):
        """Save mood data to separate files"""
        with open(SERVER_MOOD_FILE, "w") as f:
            json.dump(server_mood_data, f, indent=4)

        with open(USER_MOOD_FILE, "w") as f:
            json.dump(user_mood_data, f, indent=4)

        with open(MOOD_DATES_FILE, "w") as f:
            json.dump(mood_dates_data, f, indent=4)

async def setup(bot):
    await bot.add_cog(Slash_Mental(bot))
