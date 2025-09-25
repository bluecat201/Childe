import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, time, timedelta
import asyncio
import os
from db_helpers import db_helpers

# QOTD functionality now uses database instead of JSON files

class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.qotd_task.start()

    # def cog_unload(self):
    #     self.qotd_task.cancel()

    async def send_questions_to_all_guilds(self):
        # Get all guilds with QOTD settings
        qotd_settings = await db_helpers.get_all_qotd_settings()
        
        for guild_id, settings in qotd_settings.items():
            channel_id = settings.get("channel_id")
            ping = settings.get("ping")
            
            if not channel_id:
                continue
            
            # Get next question for this guild
            question = await db_helpers.get_next_qotd_question(guild_id)
            if not question:
                continue
                
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            await channel.send(f"{ping or ''} **Question of the Day:** {question}")
            
            # Remove the sent question from database
            await db_helpers.remove_qotd_question(guild_id, question)

    # @qotd_task.before_loop
    # async def before_qotd_task(self):
    #     await self.bot.wait_until_ready()
    #     if not self.qotd_data:
    #         self.qotd_data = await load_qotd_data()

    @commands.command(name="addquestion")
    async def add_question(self, ctx, *, question):
        await db_helpers.add_qotd_question(str(ctx.guild.id), question)
        await ctx.send(f"Question was added: {question}")

    @commands.command(name="sendqotd")
    @commands.has_permissions(manage_guild=True)
    async def send_qotd(self, ctx):
        guild_id = str(ctx.guild.id)
        
        # Get QOTD settings for this guild
        settings = await db_helpers.get_qotd_settings(guild_id)
        channel_id = settings.get("channel_id") if settings else None
        ping = settings.get("ping") if settings else None
        
        # Get next question
        question = await db_helpers.get_next_qotd_question(guild_id)
        
        if not channel_id or not question:
            await ctx.send("No channel or question was set.")
            return
        
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            await ctx.send("This channel doesn't exist.")
            return

        await channel.send(f"{ping or ''} **Question of the Day:** {question}")
        
        # Remove the sent question from database
        await db_helpers.remove_qotd_question(guild_id, question)

    @commands.command(name="setqotdchannel")
    @commands.has_permissions(manage_guild=True)
    async def set_qotd_channel(self, ctx, channel: discord.TextChannel):
        await db_helpers.set_qotd_channel(str(ctx.guild.id), channel.id)
        await ctx.send(f"Channel for QOTD was set to {channel.mention}")

    @commands.command(name="setqotdping")
    @commands.has_permissions(manage_guild=True)
    async def set_qotd_ping(self, ctx, *, ping: str = None):
        await db_helpers.set_qotd_ping(str(ctx.guild.id), ping)
        await ctx.send(f"Ping for QOTD was set to: {ping}") 
           
    @commands.command(name="listquestions")
    @commands.has_permissions(manage_guild=True)
    async def list_questions(self, ctx):
        guild_id = str(ctx.guild.id)
        questions = await db_helpers.get_qotd_questions(guild_id)

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