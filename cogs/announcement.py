import discord
from discord import app_commands
from discord.ext import commands
import json
import os

ANNOUNCEMENT_SETTINGS_FILE = "announcement_settings.json"

class Announcement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creator_id = 443842350377336860
        if os.path.exists(ANNOUNCEMENT_SETTINGS_FILE):
            with open(ANNOUNCEMENT_SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {}

    def save_settings(self):
        with open(ANNOUNCEMENT_SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    def is_creator(ctx):
        return ctx.author.id == ctx.cog.creator_id

    @commands.command(name="setchannel")
    @commands.check(is_creator)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        self.settings["channel_id"] = channel.id
        self.save_settings()
        await ctx.send(f"Oznamovací kanál nastaven na {channel.mention}.")

    @commands.command(name="setmessage")
    @commands.check(is_creator)
    async def set_message(self, ctx, *, message: str):
        self.settings["message"] = message
        self.save_settings()
        await ctx.send("Zpráva pro oznámení byla úspěšně nastavena.")

    @commands.command(name="announce")
    @commands.check(is_creator)
    async def announce(self, ctx):
        channel_id = self.settings.get("channel_id")
        message = self.settings.get("message")

        if not channel_id or not message:
            await ctx.send("Kanál nebo zpráva nebyly nastaveny. Použijte příkazy `setchannel` a `setmessage`.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("Nepodařilo se najít nastavený kanál. Ujistěte se, že kanál stále existuje.")
            return

        await channel.send(message)
        await ctx.send("Zpráva byla úspěšně odeslána.")

    # --- SLASH VERSION ---
    @app_commands.command(
        name="announce",
        description="Sends an announcement embed to the selected channel."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        text: str
    ):
        embed = discord.Embed(
            title=title,
            description=text,
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"Announcement sent to {channel.mention}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Announcement(bot))
