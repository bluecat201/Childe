import os
import json
import datetime
import pytz
import aiofiles
from discord.ext import commands, tasks

QOTD_FILE = "qotd.json"

class QOTDTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qotd_data = None
        self.bot.loop.create_task(self.load_data_and_start())

    async def load_data_and_start(self):
        self.qotd_data = await self.load_qotd_data()
        self.selftimer.start()

    async def load_qotd_data(self):
        if not os.path.exists(QOTD_FILE):
            default_data = {"guilds": {}}
            await self.save_qotd_data(default_data)
            return default_data
        async with aiofiles.open(QOTD_FILE, mode="r") as f:
            data = await f.read()
            return json.loads(data) if data else {"guilds": {}}

    async def save_qotd_data(self, data):
        async with aiofiles.open(QOTD_FILE, mode="w") as f:
            await f.write(json.dumps(data, indent=4))

    async def qotd_send(self, guild_id):
        guild_data = self.qotd_data["guilds"].get(str(guild_id), {})
        channel_id = guild_data.get("channel_id")
        questions = guild_data.get("questions", [])

        if not channel_id or not questions:
            print(f"[QOTD-Timer] No channel or questions set for guild {guild_id}.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"[QOTD-Timer] Channel ID {channel_id} not found for guild {guild_id}.")
            return

        question = questions.pop(0)
        ping = guild_data.get("ping", "")

        await channel.send(f"{ping} **Question of the Day:** {question}")
        await self.save_qotd_data(self.qotd_data)

    @tasks.loop(time=datetime.time(hour=10, minute=0, tzinfo=pytz.timezone('Europe/Prague')))
    async def selftimer(self):
        for guild_id in self.qotd_data["guilds"]:
            await self.qotd_send(guild_id)

    def cog_unload(self):
        self.selftimer.cancel()
