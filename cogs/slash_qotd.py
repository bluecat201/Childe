import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from datetime import datetime, timedelta
import asyncio
import os
import aiofiles
import random  # Add this import for random selection

QOTD_FILE = "qotd.json"

# Načtení/uložení QOTD dat
async def load_qotd_data():
    if not os.path.exists(QOTD_FILE):
        default_data = {"guilds": {}}
        await save_qotd_data(default_data)  # Vytvoří soubor s výchozími daty, pokud neexistuje
        return default_data

    async with aiofiles.open(QOTD_FILE, mode="r") as f:
        data = await f.read()
        return json.loads(data) if data else {"guilds": {}}  # Ošetření prázdného souboru


async def save_qotd_data(data):
    async with aiofiles.open(QOTD_FILE, mode="w") as f:
        await f.write(json.dumps(data, indent=4))

class QOTD_slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.qotd_task.start()

    async def cog_load(self):
        self.qotd_data = await load_qotd_data()  # Načtení existujících dat při spuštění

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

    # Slash příkaz: Přidání otázky
    @app_commands.command(name="addquestion", description="Adds question to the list.")
    async def add_question(self, interaction: discord.Interaction, question: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.qotd_data["guilds"]:
            self.qotd_data["guilds"][guild_id] = {"questions": [], "channel_id": None, "ping": None}

        self.qotd_data["guilds"][guild_id]["questions"].append(question)
        await save_qotd_data(self.qotd_data)
        await interaction.response.send_message(f"Added question: {question}", ephemeral=True)

    # Slash příkaz: Manuální odeslání otázky
    @app_commands.command(name="sendqotd", description="Sends the question of the day.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def send_qotd(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_data = self.qotd_data["guilds"].get(guild_id, {})
        channel_id = guild_data.get("channel_id")
        questions = guild_data.get("questions", [])

        if not channel_id or not questions:
            await interaction.response.send_message("No channel, or no questions have been set!", ephemeral=True)
            return

        # Convert to int if it's a string
        if isinstance(channel_id, str):
            channel_id = int(channel_id)
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("This channel doesn't exist!", ephemeral=True)
            return

        question = questions.pop(0)
        ping = guild_data.get("ping")

        # Create embed
        embed = discord.Embed(
            title="Question of the Day",
            description=question,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Send message with ping outside embed if exists
        await channel.send(content=ping or '', embed=embed)
        await save_qotd_data(self.qotd_data)
        await interaction.response.send_message("The QOTD has been sent!", ephemeral=True)

    # Slash příkaz: Nastavení místnosti
    @app_commands.command(name="setqotdchannel", description="Sets the room for QOTD.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_qotd_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.qotd_data["guilds"]:
            self.qotd_data["guilds"][guild_id] = {"questions": [], "channel_id": None, "ping": None}

        self.qotd_data["guilds"][guild_id]["channel_id"] = channel.id
        await save_qotd_data(self.qotd_data)
        await interaction.response.send_message(f"QOTD channel set to: {channel.mention}", ephemeral=True)

    # Slash příkaz: Nastavení pingu
    @app_commands.command(name="setqotdping", description="Sets the ping for QOTD.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_qotd_ping(self, interaction: discord.Interaction, ping: str = None):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.qotd_data["guilds"]:
            self.qotd_data["guilds"][guild_id] = {"questions": [], "channel_id": None, "ping": None}

        self.qotd_data["guilds"][guild_id]["ping"] = ping
        await save_qotd_data(self.qotd_data)
        await interaction.response.send_message(f"Ping for QOTD was set to: {ping}", ephemeral=True)

    @app_commands.command(name="listquestions", description="Lists all questions for this server.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def list_questions(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_data = self.qotd_data["guilds"].get(guild_id, {})
        questions = guild_data.get("questions", [])

        if not questions:
            await interaction.response.send_message("No questions in the database!", ephemeral=True)
            return
        embeds = []
        current_embed = discord.Embed(
            title="Questions in the Database",
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
                    title="Questions in the Database (Continued)",
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
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="testqotd", description="DEV qotd tester")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def test_qotd(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_data = self.qotd_data["guilds"].get(guild_id, {})
        questions = guild_data.get("questions", [])

        if not questions:
            await interaction.response.send_message("No questions in the database to test with!", ephemeral=True)
            return

        # Get test channel
        test_channel_id = 1325107856801923113
        test_channel = self.bot.get_channel(test_channel_id)
        
        if not test_channel:
            await interaction.response.send_message("Test channel not found. Please check the channel ID.", ephemeral=True)
            return

        # Select up to 5 random questions
        sample_size = min(5, len(questions))
        selected_questions = random.sample(questions, sample_size)
        
        # Create embed with the questions
        embed = discord.Embed(
            title="qotd tesetr",
            description="som bol najebany trocha",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for i, question in enumerate(selected_questions, 1):
            embed.add_field(name=f"Question {i}", value=question, inline=False)
        
        await test_channel.send(embed=embed)
        await interaction.response.send_message(f"Sent {sample_size} random questions to the test channel!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(QOTD_slash(bot))