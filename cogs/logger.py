import discord
import json
import os
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from datetime import datetime
import aiofiles

SETTINGS_FILE = "server_settings.json"
LOGS_DIRECTORY = "logs"  # Main logs directory

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIRECTORY):
    os.makedirs(LOGS_DIRECTORY)

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild_id):
        """Get log channel ID from centralized settings"""
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                
            guild_id = str(guild_id)
            return settings.get("guilds", {}).get(guild_id, {}).get("logging", {}).get("log_channel_id")
        return None

    def set_log_channel(self, guild_id, channel_id):
        """Update log channel in centralized settings"""
        guild_id = str(guild_id)
        
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        else:
            settings = {"guilds": {}}
            
        # Create nested structure if not exists
        if guild_id not in settings.get("guilds", {}):
            settings["guilds"][guild_id] = {}
            
        if "logging" not in settings["guilds"][guild_id]:
            settings["guilds"][guild_id]["logging"] = {}
            
        # Set the log channel
        settings["guilds"][guild_id]["logging"]["log_channel_id"] = channel_id
        
        # Save settings
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    
    async def log_to_file(self, guild_id, guild_name, title, description):
        """Write log entry to file"""
        try:
            # Create guild directory if it doesn't exist
            guild_dir = os.path.join(LOGS_DIRECTORY, f"{guild_id}_{guild_name}")
            if not os.path.exists(guild_dir):
                os.makedirs(guild_dir)
            
            # Create log file with today's date
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(guild_dir, f"{today}.log")
            
            # Format log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {title}: {description}\n"
            
            # Write to file (async)
            async with aiofiles.open(log_file, 'a', encoding='utf-8') as f:
                await f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {e}")

    @commands.command(name="set-logs-channel")
    @commands.has_permissions(administrator=True)
    async def set_logs_channel(self, ctx, channel: discord.TextChannel):
        self.set_log_channel(ctx.guild.id, channel.id)
        await ctx.send(f"The logging channel has been set to {channel.mention}")

    async def send_log(self, guild_id, title, description, color=discord.Color.blue(), files=None, embeds=None):
        # Get guild object for name
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
            
        # Log to file
        await self.log_to_file(guild_id, guild.name, title, description)
        
        # Log to Discord
        log_channel_id = self.get_log_channel(guild_id)
        if log_channel_id and (channel := self.bot.get_channel(log_channel_id)):
            embed = discord.Embed(title=title, description=description, color=color)
            if embeds:
                for e in embeds:
                    await channel.send(embed=e)
            await channel.send(embed=embed, files=files if files else [])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(
            member.guild.id,
            "👤 New user",
            f"{member.mention} joined server."
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(
            member.guild.id,
            "👤 User left server",
            f"{member.mention} left server.",
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        category = channel.category.name if channel.category else "No Category"
        if isinstance(channel, discord.CategoryChannel):
            await self.send_log(
                channel.guild.id,
                "📂 Category created",
                f"A new category **{channel.name}** was created."
            )
        else:
            await self.send_log(
                channel.guild.id,
                "📢 Channel created",
                f"A new channel **{channel.name}** was created in category **{category}**."
            )
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        category = channel.category.name if channel.category else "No Category"
        if isinstance(channel, discord.CategoryChannel):
            await self.send_log(
                channel.guild.id,
                "📂 Category deleted",
                f"The category **{channel.name}** was deleted.",
                color=discord.Color.red()
            )
        else:
            await self.send_log(
                channel.guild.id,
                "❌ Channel deleted",
                f"The channel **{channel.name}** in category **{category}** was deleted.",
                color=discord.Color.red()
            )
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.id == self.get_log_channel(before.guild.id):
            return
        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        if before.overwrites != after.overwrites:
            perm_changes = []
            for target, before_perms in before.overwrites.items():
                after_perms = after.overwrites.get(target, discord.PermissionOverwrite())
                added_perms = [perm for perm, value in after_perms if value and not getattr(before_perms, perm)]
                removed_perms = [perm for perm, value in before_perms if value and not getattr(after_perms, perm)]
                if added_perms or removed_perms:
                    perm_changes.append(f"**{target}:**\n" + "\n".join([f"➕ `{perm}`" for perm in added_perms] + [f"➖ `{perm}`" for perm in removed_perms]))
            if perm_changes:
                changes.append("**Permissions updated:**\n" + "\n".join(perm_changes))
        if before.category != after.category:
            before_category = before.category.name if before.category else "No Category"
            after_category = after.category.name if after.category else "No Category"
            changes.append(f"**Category changed:** `{before_category}` → `{after_category}`")
        if before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**Slowmode:** `{before.slowmode_delay}s` → `{after.slowmode_delay}s`")
        if before.nsfw != after.nsfw:
            changes.append(f"**NSFW:** `{before.nsfw}` → `{after.nsfw}`")
        if before.topic != after.topic:
            changes.append(f"**Topic:** `{before.topic or 'None'}` → `{after.topic or 'None'}`")
        if changes:
            await self.send_log(before.guild.id, "🔧 Channel updated", f"**Channel:** {before.mention}\n" + "\n".join(changes))

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(guild.id, "⛔ User Banned", f"{user.mention} ({user}) was banned.", discord.Color.red())

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.send_log(guild.id, "✅ User Unbanned", f"{user.mention} ({user}) was unbanned.", discord.Color.green())

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                await self.send_log(
                    member.guild.id,
                    "👢 User Kicked",
                    f"{member.mention} ({member}) was kicked by {entry.user.mention}.",
                    discord.Color.orange()
                )
                return

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.send_log(
            role.guild.id,
            "✨ New role created",
            f"A role has been created: **{role.name}**."
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.send_log(
            role.guild.id,
            "❌ Role deleted",
            f"A role **{role.name}** was deleted.",
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]
        
        if added_roles:
            roles_added = ", ".join([role.mention for role in added_roles])
            await self.send_log(
                after.guild.id,
                "➕ Role added",
                f"{after.mention} was given the role(s): {roles_added}"
            )
        
        if removed_roles:
            roles_removed = ", ".join([role.mention for role in removed_roles])
            await self.send_log(
                after.guild.id,
                "➖ Role removed",
                f"{after.mention} lost the role(s): {roles_removed}"
            )

        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                await self.send_log(
                    after.guild.id,
                    "⏳ Member timed out",
                    f"{after.mention} has been timed out until {after.timed_out_until}.",
                    color=discord.Color.orange()
                )
            else:
                await self.send_log(
                    after.guild.id,
                    "✅ Timeout removed",
                    f"{after.mention} is no longer timed out.",
                    color=discord.Color.green()
                )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.position != after.position:
            return  # Ignorujeme změnu pořadí rolí

        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"**Color:** `{before.color}` → `{after.color}`")
        if before.permissions != after.permissions:
            added = [perm for perm, value in after.permissions if value and not getattr(before.permissions, perm)]
            removed = [perm for perm, value in before.permissions if value and not getattr(after.permissions, perm)]
            if added or removed:
                perm_changes = "\n".join([f"➕ `{perm}`" for perm in added] + [f"➖ `{perm}`" for perm in removed])
                changes.append(f"**Permissions changed:**\n{perm_changes}")
                if "administrator" in added:
                    changes.append("🚨 **Administrator permission has been granted!** 🚨")
        if before.mentionable != after.mentionable:
            changes.append(f"**Mentionable:** `{before.mentionable}` → `{after.mentionable}`")
        if before.hoist != after.hoist:
            changes.append(f"**Displayed separately:** `{before.hoist}` → `{after.hoist}`")

        if changes:
            await self.send_log(
                before.guild.id,
                "🔄 Role edited",
                f"A role **{before.name}** has been edited.\n" + "\n".join(changes)
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:  # Ignoruje boty
            return
        if before.content == after.content:  # Pokud obsah není změněn
            return
        if before.guild:  # Zajistíme, že zpráva není v DM
            await self.send_log(
                before.guild.id,
                "✏️ Message edited",
                f"**Channel:** {before.channel.mention}\n"
                f"**Author:** {before.author.mention}\n"
                f"**Before:** {before.content}\n"
                f"**After:** {after.content}"
            )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild and message.channel.id == self.get_log_channel(message.guild.id):
            return
        files = [await attachment.to_file() for attachment in message.attachments]
        embeds = message.embeds if message.embeds else None
        async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
            deleter = entry.user if entry.target == message.author else None
            deleter_info = f"**Deleted by:** {deleter.mention}" if deleter else "Deleted by unknown user."
            await self.send_log(
                message.guild.id,
                "🗑️ Message deleted",
                f"**Channel:** {message.channel.mention}\n"
                f"**Author:** {message.author.mention}\n"
                f"**Content:** {message.content}\n"
                f"{deleter_info}",
                discord.Color.red(),
                files=files,
                embeds=embeds
            )

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return
        guild = messages[0].guild
        if not guild:
            return

        channel_name = messages[0].channel.name
        
        # Format content for file logging
        file_content = []
        for message in messages:
            timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author = message.author.name if message.author else "Unknown"
            content = message.content if message.content else "[No Content]"
            file_content.append(f"[{timestamp}] Channel: #{channel_name} | User: {author} | Content: {content}")
        
        # Log to file system
        bulk_msg_log = f"Bulk deletion of {len(messages)} messages in #{channel_name}"
        bulk_msg_details = "\n".join(file_content)
        await self.log_to_file(guild.id, guild.name, "Bulk Message Deletion", f"{bulk_msg_log}\n{bulk_msg_details}")
        
        # Continue with Discord logging
        log_channel_id = self.get_log_channel(guild.id)
        if not log_channel_id:
            return

        log_channel = self.bot.get_channel(log_channel_id)
        if not log_channel:
            return
        
        if len(messages) > 10:
            # Create file for Discord
            file_name = f"bulk_delete_{int(messages[0].created_at.timestamp())}.txt"
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write('\n'.join(file_content))
            
            embed = discord.Embed(
                title="🗑️ Bulk Message Deletion",
                description=f"**{len(messages)} messages deleted in {messages[0].channel.mention}**",
                color=discord.Color.red()
            )
            embed.add_field(name="Details", value="See attached file for all deleted messages", inline=False)
            
            with open(file_name, 'rb') as f:
                file = discord.File(f, filename=file_name)
                await log_channel.send(embed=embed, file=file)
            
            os.remove(file_name)
        else:
            # Original behavior
            deleted_messages = []
            for message in messages:
                author = message.author.mention if message.author else "Unknown"
                content = message.content if message.content else "[No Content]"
                deleted_messages.append(f"**{author}:** {content}")
            
            embed = discord.Embed(
                title="🗑️ Bulk Message Deletion",
                description=f"**{len(messages)} messages deleted in {messages[0].channel.mention}**",
                color=discord.Color.red()
            )
            embed.add_field(name="Deleted Messages", value="\n".join(deleted_messages), inline=False)
            
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logger(bot))

