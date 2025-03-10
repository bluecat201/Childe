import discord
from discord.ext import commands
import json
import os

ANNOUNCEMENT_SETTINGS_FILE = "announcement_settings.json"

class Announcement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creator_id = 443842350377336860  # Tvoje Discord ID
        
        if os.path.exists(ANNOUNCEMENT_SETTINGS_FILE):
            with open(ANNOUNCEMENT_SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {}

    def save_settings(self):
        with open(ANNOUNCEMENT_SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    def has_manage_messages(ctx):
        return ctx.author.guild_permissions.manage_messages

    def is_creator(ctx):
        return ctx.author.id == 443842350377336860

    @commands.command(name="setchannel")
    @commands.check(has_manage_messages)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        self.settings[str(ctx.guild.id)] = {"channel_id": channel.id}
        self.save_settings()
        await ctx.send(f"Notification channel for this server set to {channel.mention}.")

    @commands.command(name="setmessage")
    @commands.check(has_manage_messages)
    async def set_message(self, ctx, *, message: str):
        if str(ctx.guild.id) not in self.settings:
            self.settings[str(ctx.guild.id)] = {}
        self.settings[str(ctx.guild.id)]["message"] = message
        self.save_settings()
        await ctx.send("The notification message has been set successfully.")

    @commands.command(name="disable")
    @commands.check(has_manage_messages)
    async def disable_announce(self, ctx):
        if str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)]["disabled"] = True
            self.save_settings()
            await ctx.send("Notification has been turned off for this server.")
        else:
            await ctx.send("Notification has never been set.")

    @commands.command(name="enable")
    @commands.check(has_manage_messages)
    async def enable_announce(self, ctx):
        if str(ctx.guild.id) in self.settings and "disabled" in self.settings[str(ctx.guild.id)]:
            del self.settings[str(ctx.guild.id)]["disabled"]
            self.save_settings()
            await ctx.send("Notifications have been turned back on.")
        else:
            await ctx.send("Notifications have already been enabled or have never been disabled.")

    @commands.command(name="announce")
    @commands.check(is_creator)
    async def announce(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.settings and self.settings[guild_id].get("disabled"):
            await ctx.send("Notifications are disabled for this server.")
            return

        channel_id = self.settings.get(guild_id, {}).get("channel_id")
        message = self.settings.get(guild_id, {}).get("message", "This is only testing announcement, don't panic")

        if not channel_id:
            # Hledání prvního veřejného kanálu, do kterého bot může psát
            for channel in ctx.guild.text_channels:
                if channel.permissions_for(ctx.guild.me).send_messages:
                    channel_id = channel.id
                    break

        if not channel_id:
            await ctx.send("An appropriate notification channel could not be found.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("Could not find the set channel. Make sure the channel still exists.")
            return

        await channel.send(message)
        await ctx.send("The message was sent successfully.")

async def setup(bot):
    await bot.add_cog(Announcement(bot))
