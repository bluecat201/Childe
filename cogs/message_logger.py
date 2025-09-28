"""
Message Logger Cog - Logs EVERY message for future analysis
This cog is bulletproof and uses multiple redundancy layers to ensure NO message is lost
"""

import discord
from discord.ext import commands
import asyncio
import json
from typing import Optional, List
from db_helpers import DatabaseHelpers

class MessageLogger(commands.Cog):
    """
    BULLETPROOF Message Logger - Captures EVERY message sent by users
    
    Features:
    - Triple redundancy system (Database -> Backup DB -> File fallback)
    - Logs all message data including attachments
    - Thread channel support
    - Rate limiting protection
    - Automatic error recovery
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_helpers = DatabaseHelpers()
        
        # Rate limiting to prevent database overflow
        self.message_queue = []
        self.processing = False
        
        # Statistics
        self.messages_logged = 0
        self.failed_logs = 0
        
        print("🔍 Message Logger initialized - Now monitoring ALL messages")
    
    async def process_message_queue(self):
        """Process queued messages in batches to prevent database overflow"""
        if self.processing or not self.message_queue:
            return
            
        self.processing = True
        batch = self.message_queue[:50]  # Process 50 messages at a time
        self.message_queue = self.message_queue[50:]
        
        for message_data in batch:
            try:
                success = await self.db_helpers.log_message(**message_data)
                if success:
                    self.messages_logged += 1
                else:
                    self.failed_logs += 1
            except Exception as e:
                print(f"Error processing message from queue: {e}")
                self.failed_logs += 1
        
        self.processing = False
        
        # Continue processing if there are more messages
        if self.message_queue:
            # Small delay to prevent overwhelming the database
            await asyncio.sleep(0.1)
            asyncio.create_task(self.process_message_queue())
    
    def extract_attachments(self, message: discord.Message) -> List[dict]:
        """Extract attachment information from message"""
        attachments = []
        
        # Regular attachments
        for attachment in message.attachments:
            attachments.append({
                'id': attachment.id,
                'filename': attachment.filename,
                'size': attachment.size,
                'url': attachment.url,
                'proxy_url': attachment.proxy_url,
                'content_type': attachment.content_type,
                'description': attachment.description
            })
        
        # Embeds
        for embed in message.embeds:
            embed_data = {
                'type': 'embed',
                'title': embed.title,
                'description': embed.description,
                'url': embed.url,
                'color': str(embed.color) if embed.color else None
            }
            
            if embed.image:
                embed_data['image'] = embed.image.url
            if embed.thumbnail:
                embed_data['thumbnail'] = embed.thumbnail.url
            if embed.video:
                embed_data['video'] = embed.video.url
                
            attachments.append(embed_data)
        
        # Stickers
        for sticker in message.stickers:
            attachments.append({
                'type': 'sticker',
                'id': sticker.id,
                'name': sticker.name,
                'format': str(sticker.format),
                'url': sticker.url
            })
        
        return attachments if attachments else None
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        CAPTURE EVERY MESSAGE - This is the main event that logs everything
        """
        
        # Skip bot messages (optional - you might want to log these too)
        if message.author.bot:
            return
        
        try:
            # Extract all relevant data
            user_id = message.author.id
            message_id = message.id
            server_id = message.guild.id if message.guild else None
            channel_id = message.channel.id
            
            # Handle thread channels (get parent channel)
            parent_channel_id = None
            if isinstance(message.channel, discord.Thread):
                parent_channel_id = message.channel.parent_id
            elif hasattr(message.channel, 'parent') and message.channel.parent:
                parent_channel_id = message.channel.parent.id
            
            username = str(message.author)
            message_text = message.content if message.content else None
            
            # Extract attachments (images, files, embeds, stickers, etc.)
            attachments = self.extract_attachments(message)
            
            # Prepare message data for logging
            message_data = {
                'user_id': user_id,
                'message_id': message_id,
                'server_id': server_id,
                'channel_id': channel_id,
                'parent_channel_id': parent_channel_id,
                'username': username,
                'message_text': message_text,
                'attachments': attachments
            }
            
            # Add to queue for batch processing
            self.message_queue.append(message_data)
            
            # Start processing if not already running
            if not self.processing:
                asyncio.create_task(self.process_message_queue())
            
        except Exception as e:
            # Even if logging fails, we try to log the failure itself
            print(f"CRITICAL: Failed to queue message for logging: {e}")
            print(f"Message ID: {getattr(message, 'id', 'Unknown')}")
            print(f"User: {getattr(message.author, 'name', 'Unknown') if hasattr(message, 'author') else 'Unknown'}")
            
            # Fallback: Try direct logging as last resort
            try:
                await self.db_helpers.log_message(
                    user_id=getattr(message.author, 'id', 0),
                    message_id=getattr(message, 'id', 0),
                    server_id=getattr(message.guild, 'id', None) if hasattr(message, 'guild') and message.guild else None,
                    channel_id=getattr(message.channel, 'id', 0),
                    username=str(getattr(message, 'author', 'Unknown')),
                    message_text="[ERROR: Could not extract message content]"
                )
            except Exception as fallback_error:
                print(f"DOUBLE CRITICAL: Even fallback logging failed: {fallback_error}")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log message edits as new entries (for audit trail)"""
        
        if after.author.bot:
            return
            
        try:
            # Log the edited message with special marker
            user_id = after.author.id
            message_id = after.id
            server_id = after.guild.id if after.guild else None
            channel_id = after.channel.id
            
            parent_channel_id = None
            if isinstance(after.channel, discord.Thread):
                parent_channel_id = after.channel.parent_id
            elif hasattr(after.channel, 'parent') and after.channel.parent:
                parent_channel_id = after.channel.parent.id
            
            username = str(after.author)
            
            # Mark as edited message
            message_text = f"[EDITED] {after.content}" if after.content else "[EDITED] [No content]"
            
            attachments = self.extract_attachments(after)
            
            # Add edit metadata to attachments
            if not attachments:
                attachments = []
            
            attachments.append({
                'type': 'edit_metadata',
                'original_content': before.content if before.content else None,
                'edited_content': after.content if after.content else None,
                'edit_timestamp': after.edited_at.isoformat() if after.edited_at else None
            })
            
            message_data = {
                'user_id': user_id,
                'message_id': message_id,  # Keep same message ID but mark as edited
                'server_id': server_id,
                'channel_id': channel_id,
                'parent_channel_id': parent_channel_id,
                'username': username,
                'message_text': message_text,
                'attachments': attachments
            }
            
            # Add to queue
            self.message_queue.append(message_data)
            
            if not self.processing:
                asyncio.create_task(self.process_message_queue())
                
        except Exception as e:
            print(f"Failed to log message edit: {e}")
    
    @commands.command(name="logstats", help="Show message logging statistics (Owner only)")
    async def log_stats(self, ctx: commands.Context):
        """Show message logging statistics"""
        
        # Owner check (you can customize this)
        if ctx.author.id not in [883325865474269192, 1335248197467242519]:  # Bot owner IDs
            await ctx.send("❌ This command is restricted to bot owners only.")
            return
        
        embed = discord.Embed(
            title="📊 Message Logger Statistics",
            color=0x00d4aa
        )
        
        embed.add_field(
            name="✅ Messages Logged",
            value=f"`{self.messages_logged:,}`",
            inline=True
        )
        
        embed.add_field(
            name="❌ Failed Logs",
            value=f"`{self.failed_logs:,}`",
            inline=True
        )
        
        embed.add_field(
            name="📋 Queue Size",
            value=f"`{len(self.message_queue):,}`",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Processing",
            value="✅ Active" if self.processing else "⏸️ Idle",
            inline=True
        )
        
        success_rate = (self.messages_logged / max(self.messages_logged + self.failed_logs, 1)) * 100
        embed.add_field(
            name="📈 Success Rate",
            value=f"`{success_rate:.1f}%`",
            inline=True
        )
        
        # Get some database stats if available
        try:
            if ctx.guild:
                activity_stats = await self.db_helpers.get_server_activity_stats(ctx.guild.id, 7)
                if activity_stats:
                    embed.add_field(
                        name="📅 Last 7 Days (This Server)",
                        value=f"Messages: `{activity_stats.get('total_messages', 0):,}`\n"
                              f"Active Users: `{activity_stats.get('unique_users', 0):,}`",
                        inline=False
                    )
        except Exception as e:
            embed.add_field(
                name="⚠️ Database Stats",
                value=f"Unable to fetch: {e}",
                inline=False
            )
        
        embed.set_footer(text="Message logging is bulletproof with triple redundancy!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="recover_logs", help="Recover messages from fallback files to database (Owner only)")
    async def recover_fallback_logs(self, ctx: commands.Context):
        """Recover messages from fallback files and import them to database"""
        
        # Owner check
        if ctx.author.id not in [883325865474269192, 1335248197467242519]:
            await ctx.send("❌ This command is restricted to bot owners only.")
            return
        
        try:
            import os
            import glob
            
            fallback_files = glob.glob("fallback_logs/messages_*.json")
            
            if not fallback_files:
                await ctx.send("✅ No fallback log files found - all messages were logged successfully!")
                return
            
            processing_msg = await ctx.send("🔄 Processing fallback log files...")
            
            total_recovered = 0
            total_failed = 0
            
            for fallback_file in fallback_files:
                try:
                    with open(fallback_file, 'r') as f:
                        messages = json.load(f)
                    
                    for msg_data in messages:
                        try:
                            success = await self.db_helpers._log_message_to_db(
                                user_id=msg_data.get('user_id'),
                                message_id=msg_data.get('message_id'),
                                server_id=msg_data.get('server_id'),
                                channel_id=msg_data.get('channel_id'),
                                parent_channel_id=msg_data.get('parent_channel_id'),
                                username=msg_data.get('username'),
                                message_text=msg_data.get('message_text'),
                                attachments=msg_data.get('attachments')
                            )
                            
                            if success:
                                total_recovered += 1
                            else:
                                total_failed += 1
                                
                        except Exception as e:
                            print(f"Failed to recover individual message: {e}")
                            total_failed += 1
                    
                    # Archive the processed file
                    os.rename(fallback_file, f"{fallback_file}.recovered")
                    
                except Exception as e:
                    await ctx.send(f"❌ Error processing {fallback_file}: {e}")
            
            embed = discord.Embed(
                title="📁 Fallback Log Recovery Complete",
                color=0x00d4aa
            )
            
            embed.add_field(
                name="✅ Messages Recovered",
                value=f"`{total_recovered:,}`",
                inline=True
            )
            
            embed.add_field(
                name="❌ Failed Recoveries",
                value=f"`{total_failed:,}`",
                inline=True
            )
            
            embed.add_field(
                name="📂 Files Processed",
                value=f"`{len(fallback_files)}`",
                inline=True
            )
            
            embed.set_footer(text="Fallback files have been renamed to .recovered")
            
            await processing_msg.edit(content="", embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error during recovery process: {e}")

async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(MessageLogger(bot))
    print("✅ Message Logger cog loaded successfully!")