import discord
import json
import os
from discord.ext import commands
from discord.ext.commands import MissingPermissions

LOG_CHANNELS_FILE = "log_channels.json"

if not os.path.exists(LOG_CHANNELS_FILE):
    with open(LOG_CHANNELS_FILE, "w") as f:
        json.dump({}, f)

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild_id):
        with open(LOG_CHANNELS_FILE, "r") as f:
            log_channels = json.load(f)
        return log_channels.get(str(guild_id))

    def set_log_channel(self, guild_id, channel_id):
        with open(LOG_CHANNELS_FILE, "r") as f:
            log_channels = json.load(f)

        log_channels[str(guild_id)] = channel_id

        with open(LOG_CHANNELS_FILE, "w") as f:
            json.dump(log_channels, f)

    @commands.command(name="set-logs-channel")
    @commands.has_permissions(administrator=True)
    async def set_logs_channel(self, ctx, channel: discord.TextChannel):
        self.set_log_channel(ctx.guild.id, channel.id)
        await ctx.send(f"The logging channel has been set to {channel.mention}")

    async def send_log(self, guild_id, title, description, color=discord.Color.blue(), files=None, embeds=None):
        log_channel_id = self.get_log_channel(guild_id)
        if log_channel_id and (channel := self.bot.get_channel(log_channel_id)):
            embed = discord.Embed(title=title, description=description, color=color)
            if embeds:
                for e in embeds:
                    await channel.send(embed=e)
            await channel.send(embed=embed, files=files if files else [])

    # Logování připojení uživatele
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(
            member.guild.id,
            "👤 New user",
            f"{member.mention} joined server."
        )

    # Logování odpojení uživatele
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(
            member.guild.id,
            "👤 User left server",
            f"{member.mention} left server.",
            color=discord.Color.red()
        )

    # Logace vytvoření kanálu
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
    
    # Logace smazání kanálu
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
    
    # Logace změny oprávnění a změny kategorie kanálu
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

    # Logování vytvoření role
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.send_log(
            role.guild.id,
            "✨ New role created",
            f"A role has been created: **{role.name}**."
        )

    # Logování smazání role
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

    # Logování změny role
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

    # Logování editace zprávy
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

        log_channel_id = self.get_log_channel(guild.id)
        if not log_channel_id:
            return

        log_channel = self.bot.get_channel(log_channel_id)
        if not log_channel:
            return

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
        
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logger(bot))

