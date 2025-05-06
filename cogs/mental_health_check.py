import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta

# Data files - keep these separate as they contain actual user data, not config
SERVER_MOOD_FILE = "server_mood_data.json"
USER_MOOD_FILE = "user_mood_data.json"
MOOD_DATES_FILE = "mood_dates.json"

# Centralized settings file
SETTINGS_FILE = "server_settings.json"

# Load server-wide mood data
if os.path.exists(SERVER_MOOD_FILE):
    with open(SERVER_MOOD_FILE, "r") as f:
        server_mood_data = json.load(f)
else:
    server_mood_data = {}

# Load user mood data
if os.path.exists(USER_MOOD_FILE):
    with open(USER_MOOD_FILE, "r") as f:
        user_mood_data = json.load(f)
else:
    user_mood_data = {}

if os.path.exists(MOOD_DATES_FILE):
    with open(MOOD_DATES_FILE, "r") as f:
        mood_dates_data = json.load(f)
else:
    mood_dates_data = {}

# Load settings
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        settings_data = json.load(f)
else:
    settings_data = {
        "guilds": {},
        "global": {
            "mental_health": {
                "channels": [],
                "ping_roles": [],
                "frequency": 24,
                "check_enabled": False
            }
        }
    }

# Helper function for mental health settings
def get_mental_health_settings():
    if "global" not in settings_data:
        settings_data["global"] = {}
    
    if "mental_health" not in settings_data["global"]:
        settings_data["global"]["mental_health"] = {
            "channels": [],
            "ping_roles": [],
            "frequency": 24,
            "check_enabled": False
        }
        
    return settings_data["global"]["mental_health"]

class MentalHealthCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Get settings from centralized file
        mental_health_settings = get_mental_health_settings()
        self.check_enabled = mental_health_settings.get("check_enabled", False)
        self.channel_ids = mental_health_settings.get("channels", [])
        self.ping_roles = mental_health_settings.get("ping_roles", [])
        self.frequency = mental_health_settings.get("frequency", 24)
        
        # Start check loop
        self.check_loop.start()

    def cog_unload(self):
        self.check_loop.cancel()

    def is_admin(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.group(name="mentalhealth", invoke_without_command=True)
    async def mentalhealth(self, ctx):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
        await ctx.send("Available subcommands: enable, disable, mystats, addchannel, removechannel, setfrequency, addping, removeping, stats")

    @mentalhealth.command(name="enable")
    async def enable(self, ctx):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
        
        self.check_enabled = True
        mental_health_settings = get_mental_health_settings()
        mental_health_settings["check_enabled"] = True
        self.save_settings()
        
        await ctx.send("Mental health check enabled.")

    @mentalhealth.command(name="disable")
    async def disable(self, ctx):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
            
        self.check_enabled = False
        mental_health_settings = get_mental_health_settings()
        mental_health_settings["check_enabled"] = False
        self.save_settings()
        
        await ctx.send("Mental health check disabled.")

    @mentalhealth.command(name="addchannel")
    async def addchannel(self, ctx, channel: discord.TextChannel):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
            
        if channel.id not in self.channel_ids:
            self.channel_ids.append(channel.id)
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["channels"] = self.channel_ids
            self.save_settings()
            
            await ctx.send(f"Mental health check messages will also be sent to {channel.mention}.")
        else:
            await ctx.send(f"Channel {channel.mention} is already in the list.")

    @mentalhealth.command(name="removechannel")
    async def removechannel(self, ctx, channel: discord.TextChannel):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
            
        if channel.id in self.channel_ids:
            self.channel_ids.remove(channel.id)
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["channels"] = self.channel_ids
            self.save_settings()
            
            await ctx.send(f"Channel {channel.mention} has been removed from the list.")
        else:
            await ctx.send(f"Channel {channel.mention} is not in the list.")

    @mentalhealth.command(name="setfrequency")
    async def setfrequency(self, ctx, hours: int):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
            
        if hours < 1:
            await ctx.send("Frequency must be at least 1 hour.")
        else:
            self.frequency = hours
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["frequency"] = hours
            self.save_settings()
            
            await ctx.send(f"Mental health check frequency set to every {hours} hours.")

    @mentalhealth.command(name="addping")
    async def addping(self, ctx, role: discord.Role):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
            
        if role.id not in self.ping_roles:
            self.ping_roles.append(role.id)
            mental_health_settings = get_mental_health_settings()
            mental_health_settings["ping_roles"] = self.ping_roles
            self.save_settings()
            
            await ctx.send(f"Role {role.mention} will now be pinged during mental health check messages.")
        else:
            await ctx.send(f"Role {role.mention} is already in the ping list.")

    @mentalhealth.command(name="removeping")
    async def removeping(self, ctx, role: discord.Role):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
            
        if role.id in self.ping_roles:
            self.ping_roles.remove(role.id)
            mental_health_settings = get_mental_health_settings() 
            mental_health_settings["ping_roles"] = self.ping_roles
            self.save_settings()
            
            await ctx.send(f"Role {role.mention} has been removed from the ping list.")
        else:
            await ctx.send(f"Role {role.mention} is not in the ping list.")

    @mentalhealth.command(name="stats")
    async def stats(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in server_mood_data:
            await ctx.send("No data available for this server.")
            return

        guild_stats = server_mood_data[guild_id]
        response = f"Mental Health Check Stats:\n"
        for mood, count in guild_stats.items():
            if isinstance(count, dict):  # Handle "others" category
                response += f"{mood}:\n"
                for custom_mood, custom_count in count.items():
                    response += f"  - {custom_mood}: {custom_count}\n"
            else:
                response += f"{mood}: {count}\n"
        
        await ctx.send(response)

    @mentalhealth.command(name="manualsend")
    async def manualsend(self, ctx):
        if not self.is_admin(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
        if not self.channel_ids:
            await ctx.send("No channels are configured for mental health check messages.")
            return

        ping_roles_mentions = " ".join([f"<@&{role_id}>" for role_id in self.ping_roles])
        for channel_id in self.channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"{ping_roles_mentions}\nThis is your mental health check-in! \n"
                    "How are you feeling today? Use the command `/mentalhealth respond [mood]` to let us know. \n"
                    "Available options: happy, sad, stressed, calm, tired, motivated, or others."
                )
        await ctx.send("Mental health check message has been sent manually.")

    @tasks.loop(hours=1)
    async def check_loop(self):
        if not self.check_enabled or not self.channel_ids:
            return

        now = datetime.utcnow()
        if (now.hour % self.frequency) == 0:
            ping_roles_mentions = " ".join([f"<@&{role_id}>" for role_id in self.ping_roles])
            for channel_id in self.channel_ids:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(
                        f"{ping_roles_mentions}\nThis is your mental health check-in! \n"
                        "How are you feeling today? Use the command `/mentalhealth respond [mood]` to let us know. \n"
                        "Available options: happy, sad, stressed, calm, tired, motivated, or others."
                    )

    @mentalhealth.command(name="respond")
    async def respond(self, ctx, mood: str):
        valid_moods = ["happy", "sad", "stressed", "calm", "tired", "motivated"]
        if mood not in valid_moods and mood != "others":
            await ctx.send(f"Invalid mood. Valid options are: {', '.join(valid_moods)} or 'others'.")
            return

        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Get current timestamp for when the mood is recorded
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
            await self.handle_others(ctx, guild_id, user_id)

        # Log the mood response with the date into the mood_dates_data
        if guild_id not in mood_dates_data:
            mood_dates_data[guild_id] = {}
        if user_id not in mood_dates_data[guild_id]:
            mood_dates_data[guild_id][user_id] = []
        
        mood_record = {
            "mood": mood,
            "date": current_date
        }
        mood_dates_data[guild_id][user_id].append(mood_record)

        # Save the data back to the file
        self.save_mood_data()

        await ctx.send(f"Thank you for responding! Your mood ({mood}) has been recorded.")

    async def handle_others(self, ctx, guild_id, user_id):
        if "others" not in server_mood_data[guild_id]:
                server_mood_data[guild_id]["others"] = {}

        if "others" not in user_mood_data[user_id]:
                user_mood_data[user_id]["others"] = {}

        await ctx.send("Please provide a brief description of your mood.")
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            description = await self.bot.wait_for("message", timeout=60.0, check=check)
            mood_description = description.content

            if mood_description not in server_mood_data[guild_id]["others"]:
                server_mood_data[guild_id]["others"][mood_description] = 1
            else:
                server_mood_data[guild_id]["others"][mood_description] += 1

            if mood_description not in user_mood_data[user_id]["others"]:
                user_mood_data[user_id]["others"][mood_description] = 1
            else:
                user_mood_data[user_id]["others"][mood_description] += 1

        except:
            await ctx.send("No response received, mood not recorded.")

    @mentalhealth.command(name="mystats")
    async def mystats(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in user_mood_data:
            await ctx.send("You have not provided any mood responses yet.")
            return

        user_stats = user_mood_data[user_id]
        response = f"Your Mental Health Stats:\n"
        for mood, count in user_stats.items():
            if isinstance(count, dict):  # Handle "others" category
                response += f"{mood}:\n"
                for custom_mood, custom_count in count.items():
                    response += f"  - {custom_mood}: {custom_count}\n"
            else:
                response += f"{mood}: {count}\n"
        await ctx.send(response)
        
    def save_settings(self):
        """Save settings to the centralized settings file"""
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_data, f, indent=4)
    
    def save_mood_data(self):
        """Save mood data to their respective files"""
        with open(SERVER_MOOD_FILE, "w") as f:
            json.dump(server_mood_data, f, indent=4)

        with open(USER_MOOD_FILE, "w") as f:
            json.dump(user_mood_data, f, indent=4)

        with open(MOOD_DATES_FILE, "w") as f:
            json.dump(mood_dates_data, f, indent=4)

async def setup(bot):
    await bot.add_cog(MentalHealthCheck(bot))
