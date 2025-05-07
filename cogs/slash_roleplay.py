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
    @app_commands.command(name="blush", description="You blush.")
    async def blush(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} blushes"
        embed = await self.fetch_neko_action(description, "blush")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #bored
    @app_commands.command(name="bored", description="You are bored.")
    async def bored(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} is bored"
        embed = await self.fetch_neko_action(description, "bored")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #cry
    @app_commands.command(name="cry", description="You cry.")
    async def cry(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} cries"
        embed = await self.fetch_neko_action(description, "cry")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #cuddle
    @app_commands.command(name="cuddle", description="You cuddle the tagged user.")
    async def cuddle(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} cuddles {member.mention}"
        embed = await self.fetch_neko_action(description, "cuddle")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #dance
    @app_commands.command(name="dance", description="You dance.")
    async def dance(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} dances"
        embed = await self.fetch_neko_action(description, "dance")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #facepalm
    @app_commands.command(name="facepalm", description="You facepalms.")
    async def facepalm(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} facepalms"
        embed = await self.fetch_neko_action(description, "facepalm")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #feed
    @app_commands.command(name="feed", description="You feed the tagged user.")
    async def feed(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} feeds {member.mention}"
        embed = await self.fetch_neko_action(description, "feed")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #happy
    @app_commands.command(name="happy", description="You are happy.")
    async def happy(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} is happy"
        embed = await self.fetch_neko_action(description, "happy")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #highfive
    @app_commands.command(name="highfive", description="You highfive the tagged user.")
    async def highfive(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} highfives {member.mention}"
        embed = await self.fetch_neko_action(description, "highfive")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #hug
    @app_commands.command(name="hug", description="You hug the tagged user.")
    async def hug(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} hugs {member.mention}"
        embed = await self.fetch_neko_action(description, "hug")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #kiss
    @app_commands.command(name="kiss", description="You kiss the tagged user.")
    async def kiss(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} kisses {member.mention}"
        embed = await self.fetch_neko_action(description, "kiss")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #laugh
    @app_commands.command(name="laugh", description="You laugh.")
    async def laugh(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} laughs"
        embed = await self.fetch_neko_action(description, "laugh")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #pat
    @app_commands.command(name="pat", description="You pat the tagged user.")
    async def pat(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} pats {member.mention}"
        embed = await self.fetch_neko_action(description, "pat")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #poke
    @app_commands.command(name="poke", description="You poke the tagged user.")
    async def poke(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} pokes {member.mention}"
        embed = await self.fetch_neko_action(description, "poke")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #pout
    @app_commands.command(name="pout", description="You pout.")
    async def pout(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} pouts"
        embed = await self.fetch_neko_action(description, "pout")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #shrug
    @app_commands.command(name="shrug", description="You shrug.")
    async def shrug(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} shrugs"
        embed = await self.fetch_neko_action(description, "shrug")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #slap
    @app_commands.command(name="slap", description="You slap the tagged user.")
    async def slap(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} slaps {member.mention}"
        embed = await self.fetch_neko_action(description, "slap")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #sleep
    @app_commands.command(name="sleep", description="You sleep.")
    async def sleep(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} sleeps"
        embed = await self.fetch_neko_action(description, "sleep")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)
    
    #smile
    @app_commands.command(name="smile", description="You smile.")
    async def smile(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} smiles"
        embed = await self.fetch_neko_action(description, "smile")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)
    
    #smug
    @app_commands.command(name="smug", description="You are smug.")
    async def smug(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} is smug"
        embed = await self.fetch_neko_action(description, "smug")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #stare
    @app_commands.command(name="stare", description="You stare at the tagged user.")
    async def stare(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} stares at {member.mention}"
        embed = await self.fetch_neko_action(description, "stare")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #think
    @app_commands.command(name="think", description="You think.")
    async def think(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} thinks"
        embed = await self.fetch_neko_action(description, "think")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #thumbsup
    @app_commands.command(name="thumbsup", description="You give a thumbs up.")
    async def thumbsup(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} gives a thumbs up"
        embed = await self.fetch_neko_action(description, "thumbsup")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #tickle
    @app_commands.command(name="tickle", description="You tickle the tagged user.")
    async def tickle(self, interaction: discord.Interaction, member: discord.User):
        description = f"{interaction.user.mention} tickles {member.mention}"
        embed = await self.fetch_neko_action(description, "tickle")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #wave
    @app_commands.command(name="wave", description="You wave.")
    async def wave(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} waves"
        embed = await self.fetch_neko_action(description, "wave")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    #wink
    @app_commands.command(name="wink", description="You wink.")
    async def wink(self, interaction: discord.Interaction):
        description = f"{interaction.user.mention} winks"
        embed = await self.fetch_neko_action(description, "wink")
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to retrieve data from API.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        # Synchronizace slash příkazů při spuštění bota
        await self.bot.tree.sync()
        print("Roleplay commands are ready!")


async def setup(bot: commands.Bot):
    await bot.add_cog(SlashRoleplay(bot))
