import discord
from discord import app_commands
from discord.ext import commands
from db_helpers import DatabaseHelpers
from datetime import datetime
from config import config

class SlashAIManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_helpers = DatabaseHelpers()
        
        # Load owner and co-owner IDs from config
        self.owner_id = config.get("bot.owner_user_id", 443842350377336860)
        self.co_owner_id = config.get("bot.co_owner_user_id", 1335248197467242519)

    def is_owner_or_co_owner(self, user_id: int) -> bool:
        """Check if user is owner or co-owner"""
        return user_id == self.owner_id or user_id == self.co_owner_id

    # AI command group
    ai_group = app_commands.Group(name="ai", description="AI management commands (Owner only)")

    @ai_group.command(name="history", description="View AI chat history")
    @app_commands.describe(
        action="Choose what to view",
        session_id="Session ID (for 'session' action)",
        message_id="Discord message ID (for 'message' action)",
        limit="Number of recent interactions to show (for 'list' action, max 25)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="session", value="session"),
        app_commands.Choice(name="message", value="message"),
        app_commands.Choice(name="list", value="list")
    ])
    async def ai_history(self, interaction: discord.Interaction, action: str, 
                        session_id: str = None, message_id: str = None, limit: int = 10):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        if action == "session":
            if not session_id:
                await interaction.response.send_message("❌ Please provide a session ID for session lookup.", ephemeral=True)
                return
                
            history = self.db_helpers.get_ai_chat_history_by_session(session_id)
            
            if not history:
                await interaction.response.send_message(f"❌ No AI chat history found for session ID: `{session_id}`", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🤖 AI Chat History - Session #{session_id}",
                color=0x00d4aa,
                timestamp=history['timestamp']
            )
            
            # User information
            embed.add_field(
                name="👤 User Information",
                value=f"**User:** {history['username']} ({history['user_display_name']})\n"
                      f"**User ID:** `{history['user_id']}`",
                inline=False
            )
            
            # Server/Channel information
            server_info = f"**Guild:** {history['guild_name'] or 'DM'}\n"
            if history['guild_id']:
                server_info += f"**Guild ID:** `{history['guild_id']}`\n"
            server_info += f"**Channel:** {history['channel_name']}\n**Channel ID:** `{history['channel_id']}`"
            
            if history['message_id']:
                server_info += f"\n**Message ID:** `{history['message_id']}`"
            
            embed.add_field(
                name="🏠 Server & Channel",
                value=server_info,
                inline=False
            )
            
            # Prompt and Response
            embed.add_field(
                name="❓ User Prompt",
                value=f"```{history['prompt'][:1000]}{'...' if len(history['prompt']) > 1000 else ''}```",
                inline=False
            )
            
            embed.add_field(
                name="🤖 AI Response",
                value=f"```{history['response'][:1000]}{'...' if len(history['response']) > 1000 else ''}```",
                inline=False
            )
            
            embed.set_footer(text=f"Session ID: {session_id} | Database ID: {history['id']}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "message":
            if not message_id:
                await interaction.response.send_message("❌ Please provide a message ID for message lookup.", ephemeral=True)
                return

            try:
                message_id_int = int(message_id)
            except ValueError:
                await interaction.response.send_message("❌ Invalid message ID format. Please provide a valid Discord message ID.", ephemeral=True)
                return

            history = self.db_helpers.get_ai_chat_history_by_message_id(message_id_int)
            
            if not history:
                await interaction.response.send_message(f"❌ No AI chat history found for message ID: `{message_id}`", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🤖 AI Chat History - Message ID: {message_id}",
                color=0x00d4aa,
                timestamp=history['timestamp']
            )
            
            # User information
            embed.add_field(
                name="👤 User Information",
                value=f"**User:** {history['username']} ({history['user_display_name']})\n"
                      f"**User ID:** `{history['user_id']}`",
                inline=False
            )
            
            # Server/Channel information  
            server_info = f"**Guild:** {history['guild_name'] or 'DM'}\n"
            if history['guild_id']:
                server_info += f"**Guild ID:** `{history['guild_id']}`\n"
            server_info += f"**Channel:** {history['channel_name']}\n**Channel ID:** `{history['channel_id']}`"
            server_info += f"\n**Session ID:** `{history['session_id']}`"
            
            embed.add_field(
                name="🏠 Server & Channel",
                value=server_info,
                inline=False
            )
            
            # Prompt and Response
            embed.add_field(
                name="❓ User Prompt",
                value=f"```{history['prompt'][:1000]}{'...' if len(history['prompt']) > 1000 else ''}```",
                inline=False
            )
            
            embed.add_field(
                name="🤖 AI Response", 
                value=f"```{history['response'][:1000]}{'...' if len(history['response']) > 1000 else ''}```",
                inline=False
            )
            
            embed.set_footer(text=f"Session ID: {history['session_id']} | Database ID: {history['id']}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "list":
            if limit > 25:
                limit = 25
            elif limit < 1:
                limit = 1

            history_list = self.db_helpers.get_all_ai_chat_history(limit=limit)
            
            if not history_list:
                await interaction.response.send_message("❌ No AI chat history found in database.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🤖 Recent AI Chat Interactions (Last {len(history_list)})",
                color=0x00d4aa
            )
            
            for i, entry in enumerate(history_list, 1):
                timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                guild_name = entry['guild_name'] or "DM"
                prompt_preview = entry['prompt'][:80] + "..." if len(entry['prompt']) > 80 else entry['prompt']
                
                embed.add_field(
                    name=f"{i}. Session #{entry['session_id']} - {timestamp}",
                    value=f"**User:** {entry['user_display_name']}\n"
                          f"**Guild:** {guild_name}\n"
                          f"**Prompt:** {prompt_preview}\n"
                          f"**Message ID:** `{entry['message_id'] or 'N/A'}`",
                    inline=False
                )

            embed.set_footer(text=f"Use '/ai history session:<id>' or '/ai history message:<id>' to view full details")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ai_history_by_message", description="View AI chat history by Discord message ID (Owner only)")
    async def ai_history_by_message(self, interaction: discord.Interaction, message_id: str):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID format. Please provide a valid Discord message ID.", ephemeral=True)
            return

        history = self.db_helpers.get_ai_chat_history_by_message_id(message_id_int)
        
        if not history:
            await interaction.response.send_message(f"❌ No AI chat history found for message ID: `{message_id}`", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🤖 AI Chat History - Message ID: {message_id}",
            color=0x00d4aa,
            timestamp=history['timestamp']
        )
        
        # User information
        embed.add_field(
            name="👤 User Information",
            value=f"**User:** {history['username']} ({history['user_display_name']})\n"
                  f"**User ID:** `{history['user_id']}`",
            inline=False
        )
        
        # Server/Channel information  
        server_info = f"**Guild:** {history['guild_name'] or 'DM'}\n"
        if history['guild_id']:
            server_info += f"**Guild ID:** `{history['guild_id']}`\n"
        server_info += f"**Channel:** {history['channel_name']}\n**Channel ID:** `{history['channel_id']}`"
        server_info += f"\n**Session ID:** `{history['session_id']}`"
        
        embed.add_field(
            name="🏠 Server & Channel",
            value=server_info,
            inline=False
        )
        
        # Prompt and Response
        embed.add_field(
            name="❓ User Prompt",
            value=f"```{history['prompt'][:1000]}{'...' if len(history['prompt']) > 1000 else ''}```",
            inline=False
        )
        
        embed.add_field(
            name="🤖 AI Response", 
            value=f"```{history['response'][:1000]}{'...' if len(history['response']) > 1000 else ''}```",
            inline=False
        )
        
        embed.set_footer(text=f"Session ID: {history['session_id']} | Database ID: {history['id']}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ai_history_list", description="List recent AI chat interactions (Owner only)")
    async def ai_history_list(self, interaction: discord.Interaction, limit: int = 10):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        if limit > 25:
            limit = 25
        elif limit < 1:
            limit = 1

        history_list = self.db_helpers.get_all_ai_chat_history(limit=limit)
        
        if not history_list:
            await interaction.response.send_message("❌ No AI chat history found in database.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🤖 Recent AI Chat Interactions (Last {len(history_list)})",
            color=0x00d4aa
        )
        
        for i, entry in enumerate(history_list, 1):
            timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            guild_name = entry['guild_name'] or "DM"
            prompt_preview = entry['prompt'][:80] + "..." if len(entry['prompt']) > 80 else entry['prompt']
            
            embed.add_field(
                name=f"{i}. Session #{entry['session_id']} - {timestamp}",
                value=f"**User:** {entry['user_display_name']}\n"
                      f"**Guild:** {guild_name}\n"
                      f"**Prompt:** {prompt_preview}\n"
                      f"**Message ID:** `{entry['message_id'] or 'N/A'}`",
                inline=False
            )

        embed.set_footer(text=f"Use /ai_history_by_session or /ai_history_by_message to view full details")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Regular command versions for compatibility
    @commands.command(name="ai_history_session", help="View AI chat history by session ID (Owner only)")
    async def ai_history_session_cmd(self, ctx, session_id: str):
        if not self.is_owner_or_co_owner(ctx.author.id):
            await ctx.send("❌ This command is restricted to bot owners only.")
            return

        history = self.db_helpers.get_ai_chat_history_by_session(session_id)
        
        if not history:
            await ctx.send(f"❌ No AI chat history found for session ID: `{session_id}`")
            return

        embed = discord.Embed(
            title=f"🤖 AI Chat History - Session #{session_id}",
            color=0x00d4aa,
            timestamp=history['timestamp']
        )
        
        # User information
        embed.add_field(
            name="👤 User Information",
            value=f"**User:** {history['username']} ({history['user_display_name']})\n"
                  f"**User ID:** `{history['user_id']}`",
            inline=False
        )
        
        # Server/Channel information
        server_info = f"**Guild:** {history['guild_name'] or 'DM'}\n"
        if history['guild_id']:
            server_info += f"**Guild ID:** `{history['guild_id']}`\n"
        server_info += f"**Channel:** {history['channel_name']}\n**Channel ID:** `{history['channel_id']}`"
        
        if history['message_id']:
            server_info += f"\n**Message ID:** `{history['message_id']}`"
        
        embed.add_field(
            name="🏠 Server & Channel",
            value=server_info,
            inline=False
        )
        
        # Prompt and Response
        embed.add_field(
            name="❓ User Prompt",
            value=f"```{history['prompt'][:1000]}{'...' if len(history['prompt']) > 1000 else ''}```",
            inline=False
        )
        
        embed.add_field(
            name="🤖 AI Response",
            value=f"```{history['response'][:1000]}{'...' if len(history['response']) > 1000 else ''}```",
            inline=False
        )
        
        embed.set_footer(text=f"Session ID: {session_id} | Database ID: {history['id']}")
        
        await ctx.send(embed=embed)

    @commands.command(name="ai_history_message", help="View AI chat history by Discord message ID (Owner only)")
    async def ai_history_message_cmd(self, ctx, message_id: str):
        if not self.is_owner_or_co_owner(ctx.author.id):
            await ctx.send("❌ This command is restricted to bot owners only.")
            return

        try:
            message_id_int = int(message_id)
        except ValueError:
            await ctx.send("❌ Invalid message ID format. Please provide a valid Discord message ID.")
            return

        history = self.db_helpers.get_ai_chat_history_by_message_id(message_id_int)
        
        if not history:
            await ctx.send(f"❌ No AI chat history found for message ID: `{message_id}`")
            return

        embed = discord.Embed(
            title=f"🤖 AI Chat History - Message ID: {message_id}",
            color=0x00d4aa,
            timestamp=history['timestamp']
        )
        
        # User information
        embed.add_field(
            name="👤 User Information",
            value=f"**User:** {history['username']} ({history['user_display_name']})\n"
                  f"**User ID:** `{history['user_id']}`",
            inline=False
        )
        
        # Server/Channel information  
        server_info = f"**Guild:** {history['guild_name'] or 'DM'}\n"
        if history['guild_id']:
            server_info += f"**Guild ID:** `{history['guild_id']}`\n"
        server_info += f"**Channel:** {history['channel_name']}\n**Channel ID:** `{history['channel_id']}`"
        server_info += f"\n**Session ID:** `{history['session_id']}`"
        
        embed.add_field(
            name="🏠 Server & Channel",
            value=server_info,
            inline=False
        )
        
        # Prompt and Response
        embed.add_field(
            name="❓ User Prompt",
            value=f"```{history['prompt'][:1000]}{'...' if len(history['prompt']) > 1000 else ''}```",
            inline=False
        )
        
        embed.add_field(
            name="🤖 AI Response", 
            value=f"```{history['response'][:1000]}{'...' if len(history['response']) > 1000 else ''}```",
            inline=False
        )
        
        embed.set_footer(text=f"Session ID: {history['session_id']} | Database ID: {history['id']}")
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashAIManagement(bot))