import discord
from discord.ext import commands
import aiohttp

class Roleplay(commands.Cog, name="Roleplay"):
    """Příkazy pro roleplay interakce s ostatními uživateli."""

    def __init__(self, bot):
        self.bot = bot

    # Obecná funkce pro příkazy
    async def fetch_neko_action(self, ctx, description, endpoint, member=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://nekos.best/api/v2/{endpoint}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    image_url = data["results"][0]["url"]
                    embed = discord.Embed(description=description, color=0xadd8e6)
                    embed.set_image(url=image_url)
                    await ctx.message.delete()
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Failed to retrieve data from API. Please try again.")

    # Bite
    @commands.command(aliases=['Bite', 'BITE'], help="Bites the tagged user.")
    async def bite(self, ctx, member: discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} bites {member.mention}"
            await self.fetch_neko_action(ctx, description, "bite")

    #blush
    @commands.command(aliases=['Blush', 'BLUSH'], help="You blush.")
    async def blush(self, ctx):
        description = f"{ctx.author.mention} is blushing"
        await self.fetch_neko_action(ctx, description, "blush")

    #bored
    @commands.command(aliases=['Bored','BORED'], help='You are bored.')
    async def bored(self, ctx):
        description = f"{ctx.author.mention} is bored."
        await self.fetch_neko_action(ctx, description, "bored")

    #cry
    @commands.command(aliases=['Cry','CRY'], help='You cry.')
    async def cry(self, ctx):
        description = f"{ctx.author.mention} cry."
        await self.fetch_neko_action(ctx, description, "cry")

    #cuddle
    @commands.command(aliases=['Cuddle', 'CUDDLE'], help='You are cuddling with the tagged user.')
    async def cuddle(self, ctx, member: discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} cuddling with {member.mention}"
            await self.fetch_neko_action(ctx, description, "cuddle")

    #dance
    @commands.command(aliases=['Dance', 'DANCE'], help="You dance.")
    async def dance(self, ctx):
        description = f"{ctx.author.mention} is dancing."
        await self.fetch_neko_action(ctx, description, "dance")

    #facepalm
    @commands.command(aliases=['Facepalm','FACEPALM'], help="You're giving yourself a facepalm.")
    async def facepalm(self, ctx):
        description = f"{ctx.author.mention} facepalms."
        await self.fetch_neko_action(ctx, description, "facepalm")

    #feed
    @commands.command(aliases=['Feed','FEED'], help='You are feeding the tagged user.')
    async def feed(self, ctx,member : discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone.")
        else:
            description = f"{ctx.author.mention} is feeding {member.mention}"
            await self.fetch_neko_action(ctx, description, "feed")

    #happy
    @commands.command(aliases=['Happy','HAPPY'], help='You are happy.')
    async def happy(self, ctx):
        description = f"{ctx.author.mention} is happy."
        await self.fetch_neko_action(ctx, description, "happy")

    #highfive
    @commands.command(aliases=['Highfive','HIGHFIVE'], help='You are having a highfive with the tagged user.')
    async def highfive(self, ctx,member : discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} is having a highfive with {member.mention}"
            await self.fetch_neko_action(ctx, description, "highfive")

    # Hug
    @commands.command(aliases=['Hug', 'HUG'], help="You hugs the tagged user.")
    async def hug(self, ctx, member: discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} hugs {member.mention}"
            await self.fetch_neko_action(ctx, description, "hug")

    # Kiss
    @commands.command(aliases=['Kiss', 'KISS'], help="You kiss the tagged user.")
    async def kiss(self, ctx, member: discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} kisses {member.mention}"
            await self.fetch_neko_action(ctx, description, "kiss")

    #laugh
    @commands.command(aliases=['Laugh','LAUGH'], help='You're laughing.')
    async def laugh(self, ctx):
        description = f"{ctx.author.mention} she laughs."
        await self.fetch_neko_action(ctx, description, "laugh")

    #pat
    @commands.command(aliases=['Pat','PAT'], help='You are patting the tagged user.')
    async def pat(self, ctx,member : discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} is patting {member.mention}"
            await self.fetch_neko_action(ctx, description, "pat")

    #poke
    @commands.command(aliases=['Poke','POKE'], help='You are poking the tagged user.')
    async def poke(self, ctx,member : discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} is poking {member.mention}"
            await self.fetch_neko_action(ctx, description, "poke")

    #pout
    @commands.command(aliases=['Pout','POUT'], help='You are pouting')
    async def pout(self, ctx):
        description = f"{ctx.author.mention} is pouting"
        await self.fetch_neko_action(ctx, description, "pout")

    #shrug
    @commands.command(aliases=['Shrug','SHRUG'], help='You shrug.')
    async def shrug(self, ctx):
        description = f"{ctx.author.mention} shrugs"
        await self.fetch_neko_action(ctx, description, "shrug")

    #slap
    @commands.command(aliases=['Slap', 'SLAP'], help='You slap the tagged user.')
    async def slap(self, ctx, member: discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} is slapping {member.mention}"
            await self.fetch_neko_action(ctx, description, "slap")

    #sleep
    @commands.command(aliases=['Sleep','SLEEP'], help='You are sleeping')
    async def sleep(self, ctx):
        description = f"{ctx.author.mention} sleeping"
        await self.fetch_neko_action(ctx, description, "sleep")

    #smile
    @commands.command(aliases=['Smile','SMILE'], help='You are smiling.')
    async def smile(self, ctx):
        description = f"{ctx.author.mention} smiling"
        await self.fetch_neko_action(ctx, description, "smile")

    #smug
    @commands.command(aliases=['Smug','SMUG'], help='You smug')
    async def smug(self, ctx):
        description = f"{ctx.author.mention} smugs"
        await self.fetch_neko_action(ctx, description, "smug")

    #stare
    @commands.command(aliases=['Stare','STARE'], help='You are staring at the tagged user.')
    async def stare(self, ctx,member : discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} stares on {member.mention}"
            await self.fetch_neko_action(ctx, description, "stare")

    #think
    @commands.command(aliases=['Think','THINK'], help='You're thinking.')
    async def think(self, ctx):
        description = f"{ctx.author.mention} is thinking"
        await self.fetch_neko_action(ctx, description, "think")

    #thumbsup
    @commands.command(aliases=['Thumbsup','THUMBSUP'], help='You give a thumbs up.')
    async def thumbsup(self, ctx):
        description = f"{ctx.author.mention} gives a thumbs up."
        await self.fetch_neko_action(ctx, description, "thumbsup")

    #tickle
    @commands.command(aliases=['Tickle','TICKLE'], help='You tickle the tagged user.')
    async def tickle(self, ctx,member : discord.User = None):
        if member is None:
            await ctx.send("You must tag/enter ID someone")
        else:
            description = f"{ctx.author.mention} tickle {member.mention}"
            await self.fetch_neko_action(ctx, description, "tickle")

    #wave
    @commands.command(aliases=['Wave','WAVE'], help='You wave')
    async def wave(self, ctx):
        description = f"{ctx.author.mention} is waving"
        await self.fetch_neko_action(ctx, description, "wave")

    #wink
    @commands.command(aliases=['Wink','WINK'], help='You wink')
    async def wink(self, ctx):
        description = f"{ctx.author.mention} winks"
        await self.fetch_neko_action(ctx, description, "wink")
  
async def setup(bot: commands.Bot):
    await bot.add_cog(Roleplay(bot))
