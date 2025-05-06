import discord
from discord.ext import commands
import aiohttp
from discord import app_commands


class SlashRoleplay(commands.Cog):
    """Příkazy pro roleplay interakce s ostatními uživateli."""

    def __init__(self, bot):
        self.bot = bot

    async def fetch_neko_action(self, description, endpoint):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://nekos.best/api/v2/{endpoint}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    image_url = data["results"][0]["url"]
                    embed = discord.Embed(description=description, color=0xadd8e6)
                    embed.set_image(url=image_url)
                    return embed
                else:
                    return None

    # Vytváří univerzální příkazy pro interakce
    #bite
    @app_commands.command(name="bite", description="You bite the tagged user.")
    async def bite(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} bites {member.mention}"
        embed = await self.fetch_neko_action(description, "bite")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #blush
    @app_commands.command(name="blush", description="Začervenáš se.")
    async def blush(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} se červená"
        embed = await self.fetch_neko_action(description, "blush")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #bored
    @app_commands.command(name="bored", description="Nudíš se.")
    async def bored(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} se nudí"
        embed = await self.fetch_neko_action(description, "bored")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #cry
    @app_commands.command(name="cry", description="Brečíš.")
    async def cry(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} brečí"
        embed = await self.fetch_neko_action(description, "cry")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #cuddle
    @app_commands.command(name="cuddle", description="Mazlíš se s označeným uživatelem.")
    async def cuddle(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} se mazlí s {member.mention}"
        embed = await self.fetch_neko_action(description, "cuddle")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #dance
    @app_commands.command(name="dance", description="Tancuješ.")
    async def dance(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} tancuje"
        embed = await self.fetch_neko_action(description, "dance")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #facepalm
    @app_commands.command(name="facepalm", description="Dáváš si facepalm.")
    async def facepalm(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} si dává facepalm"
        embed = await self.fetch_neko_action(description, "facepalm")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #feed
    @app_commands.command(name="feed", description="Krmíš označeného uživatele.")
    async def feed(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} krmí {member.mention}"
        embed = await self.fetch_neko_action(description, "feed")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #happy
    @app_commands.command(name="happy", description="Jseš šťastný.")
    async def happy(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} je šťastný"
        embed = await self.fetch_neko_action(description, "happy")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #highfive
    @app_commands.command(name="highfive", description="Dáváš si placáka s označeným uživatelem.")
    async def highfive(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} si dává placáka s {member.mention}"
        embed = await self.fetch_neko_action(description, "highfive")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #hug
    @app_commands.command(name="hug", description="Objímá označeného uživatele.")
    async def hug(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} objímá {member.mention}"
        embed = await self.fetch_neko_action(description, "hug")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #kiss
    @app_commands.command(name="kiss", description="Líbá označeného uživatele.")
    async def kiss(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} líbá {member.mention}"
        embed = await self.fetch_neko_action(description, "kiss")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #laugh
    @app_commands.command(name="laugh", description="Směješ se.")
    async def laugh(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} se směje"
        embed = await self.fetch_neko_action(description, "laugh")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #pat
    @app_commands.command(name="pat", description="Hladíš označeného uživatele.")
    async def pat(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} hladí {member.mention}"
        embed = await self.fetch_neko_action(description, "pat")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #poke
    @app_commands.command(name="poke", description="Strkáš označeného uživatele.")
    async def poke(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} strká {member.mention}"
        embed = await self.fetch_neko_action(description, "poke")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #pout
    @app_commands.command(name="pout", description="Mračíš se.")
    async def pout(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} se mračí"
        embed = await self.fetch_neko_action(description, "pout")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #shrug
    @app_commands.command(name="shrug", description="Krčíš rameny.")
    async def shrug(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} krčí rameny"
        embed = await self.fetch_neko_action(description, "shrug")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #slap
    @app_commands.command(name="slap", description="Daváš facku označenému uživately.")
    async def slap(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} dává facku {member.mention}"
        embed = await self.fetch_neko_action(description, "slap")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #sleep
    @app_commands.command(name="sleep", description="spíš.")
    async def sleep(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} spi"
        embed = await self.fetch_neko_action(description, "sleep")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)
    
    #smile
    @app_commands.command(name="smile", description="Usmíváš se.")
    async def smile(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} se usmívá"
        embed = await self.fetch_neko_action(description, "smile")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)
    
    #smug
    @app_commands.command(name="smug", description="Jseš samolibý.")
    async def smug(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} je samolibý"
        embed = await self.fetch_neko_action(description, "smug")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #stare
    @app_commands.command(name="stare", description="Civíš na označeného uživatele.")
    async def stare(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} civí na {member.mention}"
        embed = await self.fetch_neko_action(description, "stare")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #think
    @app_commands.command(name="think", description="Přemýšlíš.")
    async def think(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} přemýšlí"
        embed = await self.fetch_neko_action(description, "think")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #thumbsup
    @app_commands.command(name="thumbsup", description="Dáváš palec nahoru.")
    async def thumbsup(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} dává palec nahoru"
        embed = await self.fetch_neko_action(description, "thumbsup")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #tickle
    @app_commands.command(name="tickle", description="Lechtáš označeného uživatele.")
    async def tickle(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} lechtá {member.mention}"
        embed = await self.fetch_neko_action(description, "tickle")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #wave
    @app_commands.command(name="wave", description="Máváš.")
    async def wave(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} mává"
        embed = await self.fetch_neko_action(description, "wave")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    #wink
    @app_commands.command(name="wink", description="Mrkáš.")
    async def wink(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} mrká"
        embed = await self.fetch_neko_action(description, "wink")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nepodařilo se získat data z API.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        # Synchronizace slash příkazů při spuštění bota
        await self.bot.tree.sync()
        print("Roleplay slash příkazy byly synchronizovány.")


async def setup(bot: commands.Bot):
    await bot.add_cog(SlashRoleplay(bot))
