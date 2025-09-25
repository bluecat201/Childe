import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from discord import ButtonStyle
from discord.ui import View, Button
from db_helpers import db_helpers

# Load settings data
SETTINGS_FILE = "mental_health_config.json"
settings_data = {}

if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        settings_data = json.load(f)

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

class MoodResponseView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        
    @discord.ui.button(label="Happy!", style=ButtonStyle.green, custom_id="mood_happy")
    async def happy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "happy")
    
    @discord.ui.button(label="Sad", style=ButtonStyle.gray, custom_id="mood_sad")
    async def sad_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "sad")
    
    @discord.ui.button(label="Stressed", style=ButtonStyle.red, custom_id="mood_stressed")
    async def stressed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "stressed")
    
    @discord.ui.button(label="Calm", style=ButtonStyle.blurple, custom_id="mood_calm")
    async def calm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "calm")
    
    @discord.ui.button(label="Tired", style=ButtonStyle.gray, custom_id="mood_tired")
    async def tired_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "tired")
    
    @discord.ui.button(label="Motivated", style=ButtonStyle.green, custom_id="mood_motivated")
    async def motivated_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "motivated")
    
    @discord.ui.button(label="Other...", style=ButtonStyle.blurple, custom_id="mood_others")
    async def others_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.handle_mood(interaction, "others")
    
    async def handle_mood(self, interaction, mood):
        valid_moods = ["happy", "sad", "stressed", "calm", "tired", "motivated"]
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        current_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if mood != "others":
            # Update user mood in database
            await db_helpers.update_user_mood(user_id, mood)
            
            # Update server mood in database (we'll store this separately)
            from database import db
            cursor = db.connection.cursor()
            try:
                cursor.execute("SELECT mood_data FROM server_moods WHERE guild_id = %s", (guild_id,))
                result = cursor.fetchone()
                
                if result:
                    mood_data = json.loads(result[0]) if result[0] else {m: 0 for m in valid_moods}
                else:
                    mood_data = {m: 0 for m in valid_moods}
                
                mood_data[mood] = mood_data.get(mood, 0) + 1
                
                cursor.execute("""
                    INSERT INTO server_moods (guild_id, mood_data) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE mood_data = VALUES(mood_data)
                """, (guild_id, json.dumps(mood_data)))
                
            finally:
                cursor.close()
        else:
            await interaction.followup.send("Please reply with a brief description of your mood.", ephemeral=True)
            
            try:
                def check(m):
                    return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)
                
                try:
                    dm_channel = await interaction.user.create_dm()
                    await dm_channel.send("Please describe your mood:")
                    description = await self.cog.bot.wait_for("message", timeout=60.0, check=check)
                    mood_description = description.content
                except:
                    await interaction.followup.send("I couldn't send you a DM. Please use `/mentalhealth respond others` in a channel.", ephemeral=True)
                    return
                
                # Update user mood with custom description
                await db_helpers.update_user_mood(user_id, "others", mood_description)
                
                # Update server mood data
                from database import db
                cursor = db.connection.cursor()
                try:
                    cursor.execute("SELECT mood_data FROM server_moods WHERE guild_id = %s", (guild_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        mood_data = json.loads(result[0]) if result[0] else {}
                    else:
                        mood_data = {}
                    
                    if "others" not in mood_data:
                        mood_data["others"] = {}
                    
                    mood_data["others"][mood_description] = mood_data["others"].get(mood_description, 0) + 1
                    
                    cursor.execute("""
                        INSERT INTO server_moods (guild_id, mood_data) 
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE mood_data = VALUES(mood_data)
                    """, (guild_id, json.dumps(mood_data)))
                    
                finally:
                    cursor.close()
                
                await dm_channel.send("Thank you for your response. Your mood has been recorded.")
                
            except Exception as e:
                await interaction.followup.send("No response received or an error occurred. Your mood was not recorded.", ephemeral=True)
                return

        # Save mood date record to database
        await db_helpers.add_mood_date(user_id, guild_id, mood, current_date)

        self.cog.save_mood_data()

        if mood != "others":
            await interaction.followup.send(f"Thank you for responding! Your mood ({mood}) has been recorded.", ephemeral=True)


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
        
        # Get server mood data from database
        from database import db
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT mood_data FROM server_moods WHERE guild_id = %s", (guild_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                await ctx.send("No data available for this server.")
                return
            
            guild_stats = json.loads(result[0])
            
        finally:
            cursor.close()
        
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
        
        embed = discord.Embed(
            title="Mental Health Check-in",
            description="How are you feeling today?",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Respond with", 
            value="Click a button below or use the command `/mentalhealth respond [mood]` to let us know.",
            inline=False
        )
        
        embed.set_footer(text="Take care of yourself! Your mental health matters.")
        
        view = MoodResponseView(self)
        
        for channel_id in self.channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(content=ping_roles_mentions, embed=embed, view=view)
        await ctx.send("Mental health check message has been sent manually.")

    @tasks.loop(hours=1)
    async def check_loop(self):
        if not self.check_enabled or not self.channel_ids:
            return

        now = datetime.utcnow()
        if (now.hour % self.frequency) == 0:
            ping_roles_mentions = " ".join([f"<@&{role_id}>" for role_id in self.ping_roles])
            
            embed = discord.Embed(
                title="Mental Health Check-in",
                description="How are you feeling today?",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Respond with", 
                value="Click a button below or use the command `/mentalhealth respond [mood]` to let us know.",
                inline=False
            )
            
            embed.set_footer(text="Take care of yourself! Your mental health matters.")
            
            view = MoodResponseView(self)
            
            for channel_id in self.channel_ids:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(content=ping_roles_mentions, embed=embed, view=view)

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

        if mood != "others":
            # Update user mood in database
            await db_helpers.update_user_mood(user_id, mood)
            
            # Update server mood in database
            from database import db
            cursor = db.connection.cursor()
            try:
                cursor.execute("SELECT mood_data FROM server_moods WHERE guild_id = %s", (guild_id,))
                result = cursor.fetchone()
                
                if result:
                    mood_data = json.loads(result[0]) if result[0] else {m: 0 for m in valid_moods}
                else:
                    mood_data = {m: 0 for m in valid_moods}
                
                mood_data[mood] = mood_data.get(mood, 0) + 1
                
                cursor.execute("""
                    INSERT INTO server_moods (guild_id, mood_data) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE mood_data = VALUES(mood_data)
                """, (guild_id, json.dumps(mood_data)))
                
            finally:
                cursor.close()
        else:
            await self.handle_others(ctx, guild_id, user_id)

        # Save mood date record to database
        await db_helpers.add_mood_date(user_id, guild_id, mood, current_date)

        await ctx.send(f"Thank you for responding! Your mood ({mood}) has been recorded.")

    async def handle_others(self, ctx, guild_id, user_id):
        await ctx.send("Please provide a brief description of your mood.")
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            description = await self.bot.wait_for("message", timeout=60.0, check=check)
            mood_description = description.content

            # Update user mood with custom description
            await db_helpers.update_user_mood(user_id, "others", mood_description)
            
            # Update server mood data
            from database import db
            cursor = db.connection.cursor()
            try:
                cursor.execute("SELECT mood_data FROM server_moods WHERE guild_id = %s", (guild_id,))
                result = cursor.fetchone()
                
                if result:
                    mood_data = json.loads(result[0]) if result[0] else {}
                else:
                    mood_data = {}
                
                if "others" not in mood_data:
                    mood_data["others"] = {}
                
                mood_data["others"][mood_description] = mood_data["others"].get(mood_description, 0) + 1
                
                cursor.execute("""
                    INSERT INTO server_moods (guild_id, mood_data) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE mood_data = VALUES(mood_data)
                """, (guild_id, json.dumps(mood_data)))
                
            finally:
                cursor.close()

        except:
            await ctx.send("No response received, mood not recorded.")

    @mentalhealth.command(name="mystats")
    async def mystats(self, ctx):
        user_id = str(ctx.author.id)
        user_stats = await db_helpers.get_user_mood_data(user_id)
        
        if not user_stats:
            await ctx.send("You have not provided any mood responses yet.")
            return

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

async def setup(bot):
    await bot.add_cog(MentalHealthCheck(bot))
