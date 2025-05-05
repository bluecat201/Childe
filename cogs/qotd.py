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
        self.qotd_task.start()

    async def cog_load(self):
        self.qotd_data = await load_qotd_data()

    def cog_unload(self):
        self.qotd_task.cancel()

    @tasks.loop(hours=24)
    async def qotd_task(self):
        now = datetime.now()
        target_time = time(12, 0)
        today_target = datetime.combine(now.date(), target_time)

        if now > today_target:
            await self.send_questions_to_all_guilds()
            delay = (timedelta(days=1) + today_target - now).total_seconds()
        else:
            delay = (today_target - now).total_seconds()

        await asyncio.sleep(delay)
        await self.send_questions_to_all_guilds()

    async def send_questions_to_all_guilds(self):
        for guild_id, data in self.qotd_data["guilds"].items():
            channel_id = data.get("channel_id")
            questions = data.get("questions", [])

            if not channel_id or not questions:
                continue

            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            question = questions.pop(0)
            ping = data.get("ping")
            await channel.send(f"{ping or ''} **Question of the Day:** {question}")

        await save_qotd_data(self.qotd_data)

    @qotd_task.before_loop
    async def before_qotd_task(self):
        await self.bot.wait_until_ready()
        if not self.qotd_data:
            self.qotd_data = await load_qotd_data()

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

        questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        await ctx.send(f"Current questions:\n{questions_list}")

async def setup(bot):
    await bot.add_cog(QOTD(bot))