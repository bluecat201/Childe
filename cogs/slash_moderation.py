import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import os

SETTINGS_FILE = "server_settings.json"
WARNINGS_FILE = "warnings.json"  # Keep for backwards compatibility during transition

class SlashModeration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings = self.load_warnings()

    def load_warnings(self):
        if os.path.exists(WARNINGS_FILE):
            with open(WARNINGS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_warnings(self):
        with open(WARNINGS_FILE, "w") as f:
            json.dump(self.warnings, f)

    #ban
    @app_commands.command(name="ban", description="Bans user from server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        if member == interaction.user:
            return await interaction.response.send_message("You can't ban yourself!", ephemeral=True)
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} was banned. Reason: {reason}")

    #kick
    @app_commands.command(name="kick", description="Kick user from server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} was kicked. Reason: {reason}")

    # Unmute
    @app_commands.command(name="unmute", description="Unmutes user")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")

        if muted_role not in member.roles:
            return await interaction.response.send_message(f"{member.mention} isn't muted!", ephemeral=True)

        await member.remove_roles(muted_role)
        await interaction.response.send_message(f"{member.mention} was unmuted.")

    #mute
    @app_commands.command(name="mute", description="Mutes user for a specified duration")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason"):
        try:
            seconds = int(duration[:-1])
            duration_unit = duration[-1]
            if duration_unit == "s":
                seconds *= 1
            elif duration_unit == "m":
                seconds *= 60
            elif duration_unit == "h":
                seconds *= 3600
            elif duration_unit == "d":
                seconds *= 86400
            else:
                return await interaction.response.send_message("You provided wrong time syntax!", ephemeral=True)

            guild = interaction.guild
            muted_role = discord.utils.get(guild.roles, name="Muted")
            if not muted_role:
                muted_role = await guild.create_role(name="Muted")
                for channel in guild.channels:
                    await channel.set_permissions(muted_role, speak=False, send_messages=False)

            await member.add_roles(muted_role)
            await interaction.response.send_message(f"{member.mention} was muted for {duration}. Reason: {reason}")
            await asyncio.sleep(seconds)
            await member.remove_roles(muted_role)
            await interaction.followup.send(f"{member.mention} was unmuted.")

        except ValueError:
            await interaction.response.send_message("You provided wrong time syntax!", ephemeral=True)

    # Set prefix - updated for centralized settings
    @app_commands.command(name="setprefix", description="Sets bot prefix for this server")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def setprefix(self, interaction: discord.Interaction, prefix: str):
        guild_id = str(interaction.guild.id)
        
        # Load settings file
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        else:
            settings = {"guilds": {}}
            
        # Create guild entry if it doesn't exist
        if guild_id not in settings["guilds"]:
            settings["guilds"][guild_id] = {}
        
        # Set prefix in the new structure
        settings["guilds"][guild_id]["prefix"] = prefix
        
        # Save back to centralized settings file
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)

        await interaction.response.send_message(f"Prefix set to: {prefix}")

    # Purge
    @app_commands.command(name="purge", description="Deletes a specified number of messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def purge(self, interaction: discord.Interaction, limit: int):
        if limit < 1 or limit > 100:
            return await interaction.response.send_message("The amount of messages to delete must be between 1 and 100!", ephemeral=True)
        
        await interaction.channel.purge(limit=limit)
        await interaction.response.send_message(f"Removed {limit} messages.")

    # Sudo
    @app_commands.command(name="sudo", description="Childe speaks for you!")
    @app_commands.checks.has_permissions(administrator=True)
    async def sudo(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)
        await interaction.delete_original_message()

    # Unban
    @app_commands.command(name="unban", description="Removes ban from user")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, member: discord.User, reason: str = "No reason"):
        try:
            await interaction.guild.unban(member, reason=reason)
            await interaction.response.send_message(f"{member} was unbanned. Reason: {reason}")
        except discord.NotFound:
            await interaction.response.send_message("This user isn't banned", ephemeral=True)

    #warn
    @app_commands.command(name="warn", description="Warns user")
    @app_commands.checks.has_permissions(administrator=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        guild_id = str(interaction.guild.id)
        member_id = str(member.id)

        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}

        if member_id not in self.warnings[guild_id]:
            self.warnings[guild_id][member_id] = []

        self.warnings[guild_id][member_id].append({"reason": reason, "admin": interaction.user.id})
        self.save_warnings()
        await interaction.response.send_message(f"{member.mention} was warned. Reason: {reason}")

    #warnings
    @app_commands.command(name="warnings", description="Displays warnings for a user")
    @app_commands.checks.has_permissions(administrator=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        member_id = str(member.id)

        if guild_id not in self.warnings or member_id not in self.warnings[guild_id]:
            return await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)

        embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.red())
        for idx, warning in enumerate(self.warnings[guild_id][member_id], 1):
            admin_id = warning["admin"]
            admin = interaction.guild.get_member(admin_id)
            admin_name = admin.name if admin else "Unknown"
            embed.add_field(name=f"Warn {idx}", value=f"Reason: {warning['reason']}\nIssuer: {admin_name}", inline=False)

        await interaction.response.send_message(embed=embed)


    @ban.error
    @kick.error
    @mute.error
    @warn.error
    @warnings.error
    @purge.error
    @setprefix.error
    @sudo.error
    @unban.error
    @unmute.error
    async def permissions_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashModeration(bot))
