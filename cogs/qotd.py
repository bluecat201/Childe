import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, time, timedelta
import asyncio
import os
import aiofiles

QOTD_FILE = "qotd.json"

# Načtení/uložení QOTD dat
async def load_qotd_data():
    if not os.path.exists(QOTD_FILE):
        default_data = {"guilds": {}}
        await save_qotd_data(default_data)  # Vytvoří soubor s výchozími daty
        return default_data
    
    async with aiofiles.open(QOTD_FILE, mode="r") as f:
        data = await f.read()
        return json.loads(data) if data else {"guilds": {}}  # Ošetření prázdného souboru


async def save_qotd_data(data):
    async with aiofiles.open(QOTD_FILE, mode="w") as f:
        await f.write(json.dumps(data, indent=4))

class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.qotd_task.start()

    async def cog_load(self):
        self.qotd_data = await load_qotd_data()

    # def cog_unload(self):
    #     self.qotd_task.cancel()

    async def send_questions_to_all_guilds(self):
        for guild_id, data in self.qotd_data["guilds"].items():
            channel_id = data.get("channel_id")
            questions = data.get("questions", [])

            if not channel_id or not questions:
                continue

            # Convert channel_id to integer if it's a string
            if isinstance(channel_id, str):
                channel_id = int(channel_id)
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            question = questions.pop(0)
            ping = data.get("ping")
            await channel.send(f"{ping or ''} **Question of the Day:** {question}")

        await save_qotd_data(self.qotd_data)

    # @qotd_task.before_loop
    # async def before_qotd_task(self):
    #     await self.bot.wait_until_ready()
    #     if not self.qotd_data:
    #         self.qotd_data = await load_qotd_data()

    @commands.command(name="addquestion")
    async def add_question(self, ctx, *, question):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.qotd_data["guilds"]:
            self.qotd_data["guilds"][guild_id] = {"questions": [], "channel_id": None, "ping": None}

        self.qotd_data["guilds"][guild_id]["questions"].append(question)
        await save_qotd_data(self.qotd_data)
        await ctx.send(f"Question was added: {question}")

    @commands.command(name="sendqotd")
    @commands.has_permissions(manage_guild=True)
    async def send_qotd(self, ctx):
        guild_id = str(ctx.guild.id)
        guild_data = self.qotd_data["guilds"].get(guild_id, {})
        channel_id = guild_data.get("channel_id")
        questions = guild_data.get("questions", [])

        if not channel_id or not questions:
            await ctx.send("No channel or question was set.")
            return

        # Convert to int if it's a string
        if isinstance(channel_id, str):
            channel_id = int(channel_id)
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("This channel doesn't exist.")
            return

        question = questions.pop(0)
        ping = guild_data.get("ping")

        await channel.send(f"{ping or ''} **Question of the Day:** {question}")
        await save_qotd_data(self.qotd_data)

    @commands.command(name="setqotdchannel")
    @commands.has_permissions(manage_guild=True)
    async def set_qotd_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.qotd_data["guilds"]:
            self.qotd_data["guilds"][guild_id] = {"questions": [], "channel_id": None, "ping": None}

        self.qotd_data["guilds"][guild_id]["channel_id"] = channel.id
        await save_qotd_data(self.qotd_data)
        await ctx.send(f"Channel for QOTD was set to {channel.mention}")

    @commands.command(name="setqotdping")
    @commands.has_permissions(manage_guild=True)
    async def set_qotd_ping(self, ctx, *, ping: str = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.qotd_data["guilds"]:
            self.qotd_data["guilds"][guild_id] = {"questions": [], "channel_id": None, "ping": None}

        self.qotd_data["guilds"][guild_id]["ping"] = ping
        await save_qotd_data(self.qotd_data)
        await ctx.send(f"Ping for QOTD was set to: {ping}") 
           
    @commands.command(name="listquestions")
    @commands.has_permissions(manage_guild=True)
    async def list_questions(self, ctx):
        guild_id = str(ctx.guild.id)
        guild_data = self.qotd_data["guilds"].get(guild_id, {})
        questions = guild_data.get("questions", [])

        if not questions:
            await ctx.send("No question in database.")
            return

        embeds = []
        current_embed = discord.Embed(
            title="Questions in the database",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        field_count = 0
        questions_in_current_embed = []
        
        for i, question in enumerate(questions, 1):
            if field_count >= 25:
                for j, q_batch in enumerate(questions_in_current_embed, 1):
                    current_embed.add_field(
                        name=f"Questions {j}",
                        value=q_batch,
                        inline=False
                    )
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title="Questions in the database (Continued)",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                field_count = 0
                questions_in_current_embed = []
            
            question_text = f"{i}. {question}\n"
            
            if not questions_in_current_embed:
                questions_in_current_embed.append(question_text)
            elif len(questions_in_current_embed[-1]) + len(question_text) < 1000:
                questions_in_current_embed[-1] += question_text
            else:
                questions_in_current_embed.append(question_text)
                field_count += 1
        
        for j, q_batch in enumerate(questions_in_current_embed, 1):
            current_embed.add_field(
                name=f"Questions {j}",
                value=q_batch,
                inline=False
            )
        
        embeds.append(current_embed)
        
        for i, embed in enumerate(embeds):
            embed.set_footer(text=f"Page {i+1}/{len(embeds)}")
        
        for embed in embeds:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QOTD(bot))