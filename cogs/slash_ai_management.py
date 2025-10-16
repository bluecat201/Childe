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

    def clean_prompt(self, prompt: str) -> str:
        """Clean up bot mentions in prompt for better display"""
        # Replace the specific bot mention with @Childe
        cleaned = prompt.replace("<@883325865474269192>", "@Childe")
        # Also handle the alternate mention format
        cleaned = cleaned.replace("<@!883325865474269192>", "@Childe")
        return cleaned

    ai = app_commands.Group(name="ai", description="AI management commands (Owner only)")

    @ai.command(name="history", description="View AI chat history")
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
                
            try:
                history = await self.db_helpers.get_ai_chat_history_by_session(session_id)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error fetching AI chat history: {e}", ephemeral=True)
                return
            
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

            history = await self.db_helpers.get_ai_chat_history_by_message_id(message_id_int)
            
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
                value=f"```{self.clean_prompt(history['prompt'])[:1000]}{'...' if len(self.clean_prompt(history['prompt'])) > 1000 else ''}```",
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

            history_list = await self.db_helpers.get_recent_ai_chat_history(limit=limit)
            
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

        history = await self.db_helpers.get_ai_chat_history_by_message_id(message_id_int)
        
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
            value=f"```{self.clean_prompt(history['prompt'])[:1000]}{'...' if len(self.clean_prompt(history['prompt'])) > 1000 else ''}```",
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

        history = await self.db_helpers.get_ai_chat_history_by_session(session_id)
        
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
            value=f"```{self.clean_prompt(history['prompt'])[:1000]}{'...' if len(self.clean_prompt(history['prompt'])) > 1000 else ''}```",
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

        history = await self.db_helpers.get_ai_chat_history_by_message_id(message_id_int)
        
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
            value=f"```{self.clean_prompt(history['prompt'])[:1000]}{'...' if len(self.clean_prompt(history['prompt'])) > 1000 else ''}```",
            inline=False
        )
        
        embed.add_field(
            name="🤖 AI Response", 
            value=f"```{history['response'][:1000]}{'...' if len(history['response']) > 1000 else ''}```",
            inline=False
        )
        
        embed.set_footer(text=f"Session ID: {history['session_id']} | Database ID: {history['id']}")
        
        await ctx.send(embed=embed)

    @ai.command(name="model", description="Change or view the current AI model")
    @app_commands.describe(
        action="View current model or set a new one",
        model="The AI model to use"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="view", value="view"),
            app_commands.Choice(name="set", value="set"),
            app_commands.Choice(name="list", value="list")
        ],
        model=[
            app_commands.Choice(name="gemini-2.5-flash (Fastest)", value="gemini-2.5-flash"),
            app_commands.Choice(name="gemini-2.5-pro (Best reasoning)", value="gemini-2.5-pro"),
            app_commands.Choice(name="gemini-2.0-flash (Alternative)", value="gemini-2.0-flash"),
            app_commands.Choice(name="gemini-flash (Alias for 2.5-flash)", value="gemini-flash"),
            app_commands.Choice(name="gemini-pro (Alias for 2.5-pro)", value="gemini-pro")
        ]
    )
    async def ai_model(self, interaction: discord.Interaction, action: str, model: str = None):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        # Import here to avoid circular imports
        from chatbot_ai import ChatbotAPI
        
        try:
            # Get the chatbot instance from the main bot
            chatbot = getattr(self.bot, 'chatbot_api', None)
            if not chatbot:
                # Create a temporary instance to check models
                chatbot = ChatbotAPI()

            if action == "view":
                current_model = chatbot.model
                model_info = chatbot.get_model_info(current_model)
                personality = chatbot.get_current_token_personality()
                
                embed = discord.Embed(
                    title="🤖 Current AI Configuration",
                    color=0x00d4aa
                )
                embed.add_field(
                    name="Current Model",
                    value=f"**{current_model}**\n{model_info['description']}",
                    inline=False
                )
                embed.add_field(
                    name="Speed & Capability",
                    value=f"Speed: {model_info['speed']}\nCapability: {model_info['capability']}",
                    inline=True
                )
                embed.add_field(
                    name="Current Personality",
                    value=personality,
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            elif action == "list":
                models = chatbot.get_available_models()
                embed = discord.Embed(
                    title="🤖 Available AI Models",
                    color=0x00d4aa
                )
                
                for available_model in models:
                    info = chatbot.get_model_info(available_model)
                    embed.add_field(
                        name=available_model,
                        value=f"{info['description']}\n{info['speed']} | {info['capability']}",
                        inline=True
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            elif action == "set":
                if not model:
                    await interaction.response.send_message("❌ Please specify a model to set.", ephemeral=True)
                    return
                
                success = chatbot.set_model(model)
                if success:
                    model_info = chatbot.get_model_info(model)
                    embed = discord.Embed(
                        title="✅ AI Model Updated",
                        description=f"Successfully changed to **{model}**",
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="Model Info",
                        value=f"{model_info['description']}\n{model_info['speed']} | {model_info['capability']}",
                        inline=False
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ Invalid model: `{model}`", ephemeral=True)
                    
        except Exception as e:
            await interaction.response.send_message(f"❌ Error managing AI model: {e}", ephemeral=True)

    @ai.command(name="token", description="Change or view the current AI token/personality")
    @app_commands.describe(
        action="View current token or set a new one",
        token="The AI token to use (changes personality)"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="view", value="view"),
            app_commands.Choice(name="set", value="set")
        ],
        token=[
            app_commands.Choice(name="test123 (Alex - Friendly)", value="test123"),
            app_commands.Choice(name="demo456 (Professor Minerva - Scholarly)", value="demo456"),
            app_commands.Choice(name="admin789 (Codex - Technical)", value="admin789")
        ]
    )
    async def ai_token(self, interaction: discord.Interaction, action: str, token: str = None):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        # Import here to avoid circular imports
        from chatbot_ai import ChatbotAPI
        
        try:
            # Get the chatbot instance from the main bot
            chatbot = getattr(self.bot, 'chatbot_api', None)
            if not chatbot:
                # Create a temporary instance
                chatbot = ChatbotAPI()

            if action == "view":
                current_token = chatbot.token
                personality = chatbot.get_current_token_personality()
                
                embed = discord.Embed(
                    title="🎭 Current AI Personality",
                    color=0x00d4aa
                )
                embed.add_field(
                    name="Current Token",
                    value=f"`{current_token}`",
                    inline=True
                )
                embed.add_field(
                    name="Personality",
                    value=personality,
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            elif action == "set":
                if not token:
                    await interaction.response.send_message("❌ Please specify a token to set.", ephemeral=True)
                    return
                
                old_token = chatbot.token
                chatbot.set_token(token)
                new_personality = chatbot.get_current_token_personality()
                
                embed = discord.Embed(
                    title="✅ AI Token/Personality Updated",
                    description=f"Successfully changed from `{old_token}` to `{token}`",
                    color=0x00ff00
                )
                embed.add_field(
                    name="New Personality",
                    value=new_personality,
                    inline=False
                )
                embed.add_field(
                    name="⚠️ Note",
                    value="Conversation history has been cleared as each token maintains separate memory.",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except Exception as e:
            await interaction.response.send_message(f"❌ Error managing AI token: {e}", ephemeral=True)

    @ai.command(name="reset", description="Reset AI conversation history")
    async def ai_reset(self, interaction: discord.Interaction):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        try:
            # Import here to avoid circular imports
            from chatbot_ai import ChatbotAPI
            
            # Get the chatbot instance from the main bot
            chatbot = getattr(self.bot, 'chatbot_api', None)
            if not chatbot:
                await interaction.response.send_message("❌ Chatbot not initialized.", ephemeral=True)
                return

            chatbot.clear_history()
            
            embed = discord.Embed(
                title="✅ AI History Reset",
                description="Local conversation history has been cleared.",
                color=0x00ff00
            )
            embed.add_field(
                name="ℹ️ Note",
                value="The API server still maintains its own conversation history per token. This only clears the local cache.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except Exception as e:
            await interaction.response.send_message(f"❌ Error resetting AI history: {e}", ephemeral=True)

    @ai.command(name="status", description="View AI system status and information")
    async def ai_status(self, interaction: discord.Interaction):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return

        try:
            # Import here to avoid circular imports
            from chatbot_ai import ChatbotAPI
            import aiohttp
            
            # Get the chatbot instance from the main bot
            chatbot = getattr(self.bot, 'chatbot_api', None)
            if not chatbot:
                # Create a temporary instance
                chatbot = ChatbotAPI()

            # Test API connectivity
            try:
                async with aiohttp.ClientSession() as session:
                    test_payload = {"prompt": "Hello", "model": "gemini-2.5-flash"}
                    test_headers = {"Content-Type": "application/json", "Authorization": f"sideteu {chatbot.token}"}
                    
                    async with session.post(chatbot.api_url, json=test_payload, headers=test_headers, timeout=5) as response:
                        api_status = "🟢 Online" if response.status == 200 else f"🔴 Error (HTTP {response.status})"
            except Exception as e:
                api_status = f"🔴 Offline ({str(e)[:50]}...)"

            embed = discord.Embed(
                title="🤖 AI System Status",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="API Status",
                value=api_status,
                inline=True
            )
            
            embed.add_field(
                name="Current Model",
                value=chatbot.model,
                inline=True
            )
            
            embed.add_field(
                name="Current Token",
                value=f"`{chatbot.token}`",
                inline=True
            )
            
            embed.add_field(
                name="Personality",
                value=chatbot.get_current_token_personality(),
                inline=False
            )
            
            embed.add_field(
                name="Local History",
                value=f"{len(chatbot.history)} conversations cached",
                inline=True
            )
            
            embed.add_field(
                name="API Endpoint",
                value=chatbot.api_url,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting AI status: {e}", ephemeral=True)

    # Simple test slash command to verify the cog is working
    @app_commands.command(name="ai_test", description="Test if AI management cog is working (Owner only)")
    async def ai_test(self, interaction: discord.Interaction):
        if not self.is_owner_or_co_owner(interaction.user.id):
            await interaction.response.send_message("❌ This command is restricted to bot owners only.", ephemeral=True)
            return
        
        await interaction.response.send_message("✅ AI Management cog is working! The `/ai` command group should be available with new API management features.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashAIManagement(bot))