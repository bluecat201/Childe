"""
Database helper functions for Discord bot cogs
This module provides database equivalents for all JSON operations
"""

import json
from typing import Dict, List, Any, Optional, Tuple

try:
    import mysql.connector
    from database import db
    DATABASE_AVAILABLE = True
except ImportError:
    print("Warning: Database not available. Using fallback implementations.")
    DATABASE_AVAILABLE = False
    # Mock db object
    class MockDB:
        @property
        def connection(self):
            return None
    db = Mo    @staticmethod
    async def get_level_up_channel(guild_id: int) -> Optional[int]:
        """Get level up channel for a guild"""
        if not await DatabaseHelpers.ensure_connection():()

class DatabaseHelpers:
    """Helper functions for database operations used by cogs"""
    
    @staticmethod
    async def ensure_connection():
        """Ensure database connection is available, attempt to reconnect if needed"""
        if not DATABASE_AVAILABLE:
            return False
            
        if not db.connection or not db.connection.is_connected():
            print("Database connection lost, attempting to reconnect...")
            try:
                await db.connect()
                print("✅ Database reconnected successfully!")
                return True
            except Exception as e:
                print(f"❌ Database reconnection failed: {e}")
                return False
        return True
    
    # ECONOMY HELPERS
    @staticmethod
    async def get_bank_data() -> Dict[str, Any]:
        """Get all economy data (replacement for mainbank.json)"""
        if not await DatabaseHelpers.ensure_connection():
            return {}
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT user_id, wallet, bank, bag FROM economy")
            results = cursor.fetchall()
            
            # Convert to the expected format
            bank_data = {}
            for row in results:
                bag = json.loads(row['bag']) if row['bag'] else []
                bank_data[str(row['user_id'])] = {
                    'wallet': row['wallet'],
                    'bank': row['bank'],
                    'bag': bag
                }
            return bank_data
        finally:
            cursor.close()
    
    @staticmethod
    async def open_account(user) -> bool:
        """Create new economy account for user"""
        if not await DatabaseHelpers.ensure_connection():
            return False
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                INSERT IGNORE INTO economy (user_id, wallet, bank, bag) 
                VALUES (%s, 0, 0, %s)
            """, (user.id, json.dumps([])))
            return cursor.rowcount > 0
        finally:
            cursor.close()
    
    @staticmethod
    async def update_bank(user, change: int = 0, mode: str = "wallet") -> List[int]:
        """Update user's bank balance"""
        if not await DatabaseHelpers.ensure_connection():
            return [0, 0]
        cursor = db.connection.cursor()
        try:
            # First ensure account exists
            await DatabaseHelpers.open_account(user)
            
            # Update the balance
            cursor.execute(f"""
                UPDATE economy SET {mode} = {mode} + %s WHERE user_id = %s
            """, (change, user.id))
            
            # Get updated balances
            cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = %s", (user.id,))
            result = cursor.fetchone()
            return [result[0], result[1]] if result else [0, 0]
        finally:
            cursor.close()
    
    @staticmethod
    async def get_user_balance(user) -> Tuple[int, int]:
        """Get user's wallet and bank balance"""
        if not await DatabaseHelpers.ensure_connection():
            return (0, 0)
        cursor = db.connection.cursor()
        try:
            await DatabaseHelpers.open_account(user)
            cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = %s", (user.id,))
            result = cursor.fetchone()
            return (result[0], result[1]) if result else (0, 0)
        finally:
            cursor.close()
    
    @staticmethod
    async def buy_item(user, item_name: str, amount: int, price: int) -> bool:
        """Add item to user's bag and deduct money"""
        cursor = db.connection.cursor()
        try:
            await DatabaseHelpers.open_account(user)
            
            # Get current bag
            cursor.execute("SELECT bag, wallet FROM economy WHERE user_id = %s", (user.id,))
            result = cursor.fetchone()
            if not result or result[1] < price * amount:
                return False
                
            bag = json.loads(result[0]) if result[0] else []
            
            # Find if item already exists in bag
            item_found = False
            for item in bag:
                if item['item'].lower() == item_name.lower():
                    item['amount'] += amount
                    item_found = True
                    break
            
            if not item_found:
                bag.append({"item": item_name, "amount": amount})
            
            # Update database
            new_wallet = result[1] - (price * amount)
            cursor.execute("""
                UPDATE economy SET wallet = %s, bag = %s WHERE user_id = %s
            """, (new_wallet, json.dumps(bag), user.id))
            
            return True
        finally:
            cursor.close()
    
    @staticmethod
    async def get_user_bag(user) -> List[Dict[str, Any]]:
        """Get user's bag contents"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return []
        cursor = db.connection.cursor()
        try:
            await DatabaseHelpers.open_account(user)
            cursor.execute("SELECT bag FROM economy WHERE user_id = %s", (user.id,))
            result = cursor.fetchone()
            return json.loads(result[0]) if result and result[0] else []
        finally:
            cursor.close()
    
    # LEVELING HELPERS
    @staticmethod
    async def get_leveling_data() -> Dict[str, Dict[str, Any]]:
        """Get all leveling data"""
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT guild_id, user_id, xp, level, messages, total_xp FROM leveling")
            results = cursor.fetchall()
            
            leveling_data = {}
            for row in results:
                guild_id = str(row['guild_id'])
                user_id = str(row['user_id'])
                
                if guild_id not in leveling_data:
                    leveling_data[guild_id] = {}
                
                leveling_data[guild_id][user_id] = {
                    'xp': row['xp'],
                    'level': row['level'],
                    'messages': row['messages'],
                    'total_xp': row['total_xp']
                }
            return leveling_data
        finally:
            cursor.close()
    
    @staticmethod
    async def update_user_xp(guild_id: int, user_id: int, xp_gain: int, message_count: int = 1):
        """Update user's XP and level"""
        # Ensure database connection is available
        if not await DatabaseHelpers.ensure_connection():
            print(f"Database not available for XP update: user {user_id} in guild {guild_id}")
            return False
            
        cursor = db.connection.cursor()
        try:
            # Get current stats
            cursor.execute("""
                SELECT xp, level, messages, total_xp FROM leveling 
                WHERE guild_id = %s AND user_id = %s
            """, (guild_id, user_id))
            result = cursor.fetchone()
            
            if result:
                current_xp, current_level, messages, total_xp = result
                new_xp = current_xp + xp_gain
                new_total_xp = total_xp + xp_gain
                new_messages = messages + message_count
                
                # Calculate new level (simple formula: level = sqrt(total_xp / 100))
                import math
                new_level = int(math.sqrt(new_total_xp / 100)) + 1
                
                # If leveled up, reset XP for current level
                if new_level > current_level:
                    new_xp = new_xp - (current_level * current_level * 100)
                
                cursor.execute("""
                    UPDATE leveling SET xp = %s, level = %s, messages = %s, total_xp = %s
                    WHERE guild_id = %s AND user_id = %s
                """, (new_xp, new_level, new_messages, new_total_xp, guild_id, user_id))
                
                return new_level > current_level  # Return True if leveled up
            else:
                # Create new entry
                cursor.execute("""
                    INSERT INTO leveling (guild_id, user_id, xp, level, messages, total_xp)
                    VALUES (%s, %s, %s, 1, %s, %s)
                """, (guild_id, user_id, xp_gain, message_count, xp_gain))
                return False
        except Exception as e:
            print(f"Error updating user XP: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    async def get_guild_leaderboard(guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get guild leveling leaderboard"""
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT user_id, xp, level, messages, total_xp 
                FROM leveling 
                WHERE guild_id = %s 
                ORDER BY total_xp DESC 
                LIMIT %s
            """, (guild_id, limit))
            return cursor.fetchall()
        finally:
            cursor.close()
    
    # SERVER SETTINGS HELPERS
    @staticmethod
    async def get_server_settings() -> Dict[str, Any]:
        """Get all server settings"""
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT guild_id, prefix, settings FROM server_settings")
            results = cursor.fetchall()
            
            settings_data = {"guilds": {}}
            for row in results:
                guild_settings = json.loads(row['settings']) if row['settings'] else {}
                guild_settings['prefix'] = row['prefix']
                settings_data["guilds"][str(row['guild_id'])] = guild_settings
            
            return settings_data
        finally:
            cursor.close()
    
    @staticmethod
    async def update_server_setting(guild_id: int, key: str, value: Any):
        """Update a specific server setting"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return
        cursor = db.connection.cursor()
        try:
            # Get current settings
            cursor.execute("SELECT settings FROM server_settings WHERE guild_id = %s", (guild_id,))
            result = cursor.fetchone()
            
            if result:
                settings = json.loads(result[0]) if result[0] else {}
            else:
                settings = {}
            
            # Update the setting
            if key == 'prefix':
                cursor.execute("""
                    INSERT INTO server_settings (guild_id, prefix, settings) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE prefix = VALUES(prefix)
                """, (guild_id, value, json.dumps(settings)))
            else:
                settings[key] = value
                cursor.execute("""
                    INSERT INTO server_settings (guild_id, prefix, settings) 
                    VALUES (%s, '*', %s)
                    ON DUPLICATE KEY UPDATE settings = VALUES(settings)
                """, (guild_id, json.dumps(settings)))
        finally:
            cursor.close()
    
    @staticmethod
    async def get_server_setting(guild_id: str, key: str) -> Any:
        """Get a specific server setting"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return None
        cursor = db.connection.cursor()
        try:
            if key == "prefix":
                cursor.execute("SELECT prefix FROM server_settings WHERE guild_id = %s", (guild_id,))
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor.execute("SELECT settings FROM server_settings WHERE guild_id = %s", (guild_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    settings = json.loads(result[0])
                    return settings.get(key)
                return None
        finally:
            cursor.close()
    
    # MOOD DATA HELPERS
    @staticmethod
    async def get_server_mood_data():
        """Get server mood data"""
        if not await DatabaseHelpers.ensure_connection():
            return {}
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT user_id, happy, sad, stressed, calm, tired, motivated, others FROM user_moods")
            results = cursor.fetchall()
            
            mood_data = {}
            for row in results:
                others = json.loads(row['others']) if row['others'] else {}
                mood_data[str(row['user_id'])] = {
                    'happy': row['happy'],
                    'sad': row['sad'],
                    'stressed': row['stressed'],
                    'calm': row['calm'],
                    'tired': row['tired'],
                    'motivated': row['motivated'],
                    'others': others
                }
            return mood_data
        finally:
            cursor.close()
    
    @staticmethod
    async def update_user_mood(user_id: int, mood_type: str, custom_mood: str = None):
        """Update user's mood data"""
        if not await DatabaseHelpers.ensure_connection():
            return
        cursor = db.connection.cursor()
        try:
            # Get current mood data
            cursor.execute("SELECT happy, sad, stressed, calm, tired, motivated, others FROM user_moods WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            if result:
                happy, sad, stressed, calm, tired, motivated, others_json = result
                others = json.loads(others_json) if others_json else {}
            else:
                happy = sad = stressed = calm = tired = motivated = 0
                others = {}
            
            # Update mood count
            if mood_type in ['happy', 'sad', 'stressed', 'calm', 'tired', 'motivated']:
                if mood_type == 'happy':
                    happy += 1
                elif mood_type == 'sad':
                    sad += 1
                elif mood_type == 'stressed':
                    stressed += 1
                elif mood_type == 'calm':
                    calm += 1
                elif mood_type == 'tired':
                    tired += 1
                elif mood_type == 'motivated':
                    motivated += 1
            elif custom_mood:
                others[custom_mood] = others.get(custom_mood, 0) + 1
            
            # Update database
            cursor.execute("""
                INSERT INTO user_moods (user_id, happy, sad, stressed, calm, tired, motivated, others)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                happy = VALUES(happy), sad = VALUES(sad), stressed = VALUES(stressed),
                calm = VALUES(calm), tired = VALUES(tired), motivated = VALUES(motivated),
                others = VALUES(others)
            """, (user_id, happy, sad, stressed, calm, tired, motivated, json.dumps(others)))
        finally:
            cursor.close()
    
    # WARNINGS HELPERS
    @staticmethod
    async def get_warnings_data() -> Dict[str, Dict[str, List]]:
        """Get all warnings data"""
        if not await DatabaseHelpers.ensure_connection():
            return {}
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT guild_id, user_id, warnings FROM warnings")
            results = cursor.fetchall()
            
            warnings_data = {}
            for row in results:
                guild_id = str(row['guild_id'])
                user_id = str(row['user_id'])
                warnings = json.loads(row['warnings']) if row['warnings'] else []
                
                if guild_id not in warnings_data:
                    warnings_data[guild_id] = {}
                
                warnings_data[guild_id][user_id] = warnings
            
            return warnings_data
        finally:
            cursor.close()
    
    @staticmethod
    async def add_warning(guild_id: int, user_id: int, warning: Dict[str, Any]):
        """Add a warning to a user"""
        cursor = db.connection.cursor()
        try:
            # Get current warnings
            cursor.execute("SELECT warnings FROM warnings WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
            result = cursor.fetchone()
            
            if result:
                warnings = json.loads(result[0]) if result[0] else []
            else:
                warnings = []
            
            warnings.append(warning)
            
            cursor.execute("""
                INSERT INTO warnings (guild_id, user_id, warnings)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE warnings = VALUES(warnings)
            """, (guild_id, user_id, json.dumps(warnings)))
        finally:
            cursor.close()
    
    # GENERAL JSON FILE HELPERS
    @staticmethod
    async def load_json_data(table_name: str, key_column: str = None) -> Dict[str, Any]:
        """Generic function to load JSON data from database tables"""
        cursor = db.connection.cursor(dictionary=True)
        try:
            if key_column:
                cursor.execute(f"SELECT * FROM {table_name}")
                results = cursor.fetchall()
                return {str(row[key_column]): row for row in results}
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
                return cursor.fetchall()
        finally:
            cursor.close()
    
    @staticmethod
    async def save_json_data(table_name: str, key_column: str, key_value: Any, data: Dict[str, Any]):
        """Generic function to save JSON data to database tables"""
        if not await DatabaseHelpers.ensure_connection():
            return
        cursor = db.connection.cursor()
        try:
            # This is a simplified version - specific implementations should be used for complex tables
            placeholders = ', '.join(['%s'] * len(data))
            columns = ', '.join(data.keys())
            values = list(data.values())
            
            cursor.execute(f"""
                INSERT INTO {table_name} ({key_column}, {columns})
                VALUES (%s, {placeholders})
                ON DUPLICATE KEY UPDATE {', '.join([f'{k} = VALUES({k})' for k in data.keys()])}
            """, [key_value] + values)
        finally:
            cursor.close()
    
    # LEVELING SYSTEM HELPERS
    @staticmethod
    def get_leveling_settings(guild_id: int) -> Dict[str, Any]:
        """Get leveling settings for a guild"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return {'enabled': True}
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT enabled FROM leveling_enabled WHERE guild_id = %s", (guild_id,))
            result = cursor.fetchone()
            return {'enabled': result[0] if result else True}
        except Exception as e:
            print(f"Error getting leveling settings: {e}")
            return {'enabled': True}
        finally:
            cursor.close()
    
    @staticmethod
    def get_ignored_channels(guild_id: int) -> List[str]:
        """Get list of ignored channels for a guild"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return []
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT channel_id FROM ignored_channels WHERE guild_id = %s", (guild_id,))
            results = cursor.fetchall()
            return [str(row[0]) for row in results]
        except Exception as e:
            print(f"Error getting ignored channels: {e}")
            return []
        finally:
            cursor.close()
    
    @staticmethod
    def get_level_up_channel(guild_id: int) -> Optional[int]:
        """Get level up channel ID for a guild"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return None
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT channel_id FROM level_up_channels WHERE guild_id = %s", (guild_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting level up channel: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_user_preference(user_id: int, preference_key: str, default_value: Any = None) -> Any:
        """Get user preference value"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return default_value
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT preferences FROM mention_prefs WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                import json
                prefs = json.loads(result[0])
                return prefs.get(preference_key, default_value)
            return default_value
        except Exception as e:
            print(f"Error getting user preference: {e}")
            return default_value
        finally:
            cursor.close()
    
    @staticmethod
    def set_user_preference(user_id: int, preference_key: str, value: Any) -> bool:
        """Set user preference value"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return False
            
        cursor = db.connection.cursor()
        try:
            # Get existing preferences
            cursor.execute("SELECT preferences FROM mention_prefs WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            import json
            if result and result[0]:
                prefs = json.loads(result[0])
            else:
                prefs = {}
            
            prefs[preference_key] = value
            prefs_json = json.dumps(prefs)
            
            # Insert or update
            cursor.execute("""
                INSERT INTO mention_prefs (user_id, preferences) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE preferences = VALUES(preferences)
            """, (user_id, prefs_json))
            
            return True
        except Exception as e:
            print(f"Error setting user preference: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    async def update_leveling_settings(guild_id: int, enabled: bool) -> bool:
        """Update leveling settings for a guild"""
        if not await DatabaseHelpers.ensure_connection():
            return False
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO leveling_enabled (guild_id, enabled) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE enabled = VALUES(enabled)
            """, (guild_id, enabled))
            return True
        except Exception as e:
            print(f"Error updating leveling settings: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def add_ignored_channel(guild_id: int, channel_id: int) -> bool:
        """Add a channel to the ignored list"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return False
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                INSERT IGNORE INTO ignored_channels (guild_id, channel_id) 
                VALUES (%s, %s)
            """, (guild_id, channel_id))
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error adding ignored channel: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def remove_ignored_channel(guild_id: int, channel_id: int) -> bool:
        """Remove a channel from the ignored list"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return False
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                DELETE FROM ignored_channels 
                WHERE guild_id = %s AND channel_id = %s
            """, (guild_id, channel_id))
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing ignored channel: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def set_level_up_channel(guild_id: int, channel_id: Optional[int]) -> bool:
        """Set level up channel for a guild"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return False
            
        cursor = db.connection.cursor()
        try:
            if channel_id is None:
                # Remove level up channel
                cursor.execute("DELETE FROM level_up_channels WHERE guild_id = %s", (guild_id,))
            else:
                # Set level up channel
                cursor.execute("""
                    INSERT INTO level_up_channels (guild_id, channel_id) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
                """, (guild_id, channel_id))
            return True
        except Exception as e:
            print(f"Error setting level up channel: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_leaderboard(guild_id: int, limit: int = 10) -> List[Tuple[int, int, int, int]]:
        """Get guild leaderboard (user_id, level, total_xp, messages)"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return []
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                SELECT user_id, level, total_xp, messages 
                FROM leveling 
                WHERE guild_id = %s 
                ORDER BY total_xp DESC 
                LIMIT %s
            """, (guild_id, limit))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
        finally:
            cursor.close()
    
    @staticmethod
    async def get_user_level_data(user_id: int, guild_id: int) -> Optional[Tuple[int, int, int]]:
        """Get user level data (level, total_xp, messages)"""
        # Ensure database connection is available
        if not await DatabaseHelpers.ensure_connection():
            return None
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                SELECT level, total_xp, messages 
                FROM leveling 
                WHERE guild_id = %s AND user_id = %s
            """, (guild_id, user_id))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error getting user level data: {e}")
            return None
        finally:
            cursor.close()
    
    # AI CHAT HISTORY HELPERS
    @staticmethod
    async def save_ai_chat_interaction(session_id: str, user_id: int, username: str, 
                                  user_display_name: str, guild_id: Optional[int], 
                                  guild_name: Optional[str], channel_id: int, 
                                  channel_name: str, message_id: Optional[int],
                                  prompt: str, response: str) -> bool:
        """Save AI chat interaction to database"""
        # Ensure database connection is available
        if not await DatabaseHelpers.ensure_connection():
            print("Database not available for AI chat logging")
            return False
            
        cursor = db.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO ai_chat_history 
                (session_id, user_id, username, user_display_name, guild_id, guild_name, 
                 channel_id, channel_name, message_id, prompt, response)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, user_id, username, user_display_name, guild_id, guild_name,
                  channel_id, channel_name, message_id, prompt, response))
            return True
        except Exception as e:
            print(f"Error saving AI chat interaction: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_ai_chat_history_by_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get AI chat history by session ID"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return None
            
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM ai_chat_history 
                WHERE session_id = %s 
                ORDER BY timestamp DESC
            """, (session_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching AI chat history by session: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_ai_chat_history_by_message_id(message_id: int) -> Optional[Dict[str, Any]]:
        """Get AI chat history by Discord message ID"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return None
            
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM ai_chat_history 
                WHERE message_id = %s 
                ORDER BY timestamp DESC
            """, (message_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching AI chat history by message ID: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_all_ai_chat_history(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all AI chat history with pagination (owner/co-owner only)"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
            return []
            
        cursor = db.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM ai_chat_history 
                ORDER BY timestamp DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching all AI chat history: {e}")
            return []
        finally:
            cursor.close()
    
    # MESSAGE LOGGING HELPERS
    @staticmethod
    async def log_message(user_id: int, message_id: int, server_id: int = None, 
                         channel_id: int = None, parent_channel_id: int = None, 
                         username: str = None, message_text: str = None, 
                         attachments: list = None) -> bool:
        """Log every message sent by users for future analysis - BULLETPROOF VERSION"""
        
        # Triple redundancy system
        success_attempts = 0
        
        # Attempt 1: Primary connection attempt
        try:
            if await DatabaseHelpers.ensure_connection():
                if await DatabaseHelpers._log_message_to_db(user_id, message_id, server_id, 
                                                          channel_id, parent_channel_id, 
                                                          username, message_text, attachments):
                    success_attempts += 1
        except Exception as e:
            print(f"Message logging attempt 1 failed: {e}")
        
        # Attempt 2: Backup connection attempt (if first failed)
        if success_attempts == 0:
            try:
                # Force reconnection
                from database import db
                await db.disconnect()
                await db.connect()
                
                if await DatabaseHelpers._log_message_to_db(user_id, message_id, server_id, 
                                                          channel_id, parent_channel_id, 
                                                          username, message_text, attachments):
                    success_attempts += 1
                    print("✅ Message logged on backup connection attempt")
            except Exception as e:
                print(f"Message logging attempt 2 failed: {e}")
        
        # Attempt 3: File-based fallback logging
        if success_attempts == 0:
            try:
                import json
                import os
                from datetime import datetime
                
                # Create fallback directory if it doesn't exist
                os.makedirs("fallback_logs", exist_ok=True)
                
                # Log to file as backup
                fallback_data = {
                    "user_id": user_id,
                    "message_id": message_id,
                    "server_id": server_id,
                    "channel_id": channel_id,
                    "parent_channel_id": parent_channel_id,
                    "username": username,
                    "message_text": message_text,
                    "attachments": attachments,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Append to daily fallback file
                date_str = datetime.now().strftime("%Y%m%d")
                fallback_file = f"fallback_logs/messages_{date_str}.json"
                
                # Read existing data or create new list
                if os.path.exists(fallback_file):
                    with open(fallback_file, 'r') as f:
                        existing_data = json.load(f)
                else:
                    existing_data = []
                
                existing_data.append(fallback_data)
                
                # Write back to file
                with open(fallback_file, 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                success_attempts += 1
                print(f"📁 Message logged to fallback file: {fallback_file}")
                
            except Exception as e:
                print(f"CRITICAL: All message logging attempts failed including file backup: {e}")
        
        return success_attempts > 0
    
    @staticmethod
    async def _log_message_to_db(user_id: int, message_id: int, server_id: int = None, 
                                channel_id: int = None, parent_channel_id: int = None, 
                                username: str = None, message_text: str = None, 
                                attachments: list = None) -> bool:
        """Internal method to log message to database"""
        from database import db
        
        if not db.connection or not db.connection.is_connected():
            return False
            
        cursor = db.connection.cursor()
        try:
            # Prepare attachments as JSON
            attachments_json = json.dumps(attachments) if attachments else None
            
            # Insert message log
            cursor.execute("""
                INSERT IGNORE INTO message_logs 
                (user_id, message_id, server_id, channel_id, parent_channel_id, 
                 username, message_text, attachments)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, message_id, server_id, channel_id, parent_channel_id,
                  username, message_text, attachments_json))
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Database message logging error: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    async def get_user_message_count(user_id: int, server_id: int = None, days: int = 30) -> int:
        """Get message count for user (optionally in specific server)"""
        if not await DatabaseHelpers.ensure_connection():
            return 0
            
        from database import db
        cursor = db.connection.cursor()
        try:
            if server_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM message_logs 
                    WHERE user_id = %s AND server_id = %s 
                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                """, (user_id, server_id, days))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM message_logs 
                    WHERE user_id = %s 
                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                """, (user_id, days))
            
            result = cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            print(f"Error getting user message count: {e}")
            return 0
        finally:
            cursor.close()
    
    @staticmethod
    async def get_server_activity_stats(server_id: int, days: int = 7) -> dict:
        """Get server activity statistics"""
        if not await DatabaseHelpers.ensure_connection():
            return {}
            
        from database import db
        cursor = db.connection.cursor(dictionary=True)
        try:
            # Get total messages, unique users, and most active channel
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT user_id) as unique_users,
                    channel_id,
                    COUNT(*) as channel_messages
                FROM message_logs 
                WHERE server_id = %s 
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY channel_id
                ORDER BY channel_messages DESC
                LIMIT 1
            """, (server_id, days))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'total_messages': result['total_messages'],
                    'unique_users': result['unique_users'],
                    'most_active_channel': result['channel_id'],
                    'most_active_channel_messages': result['channel_messages']
                }
            return {}
            
        except Exception as e:
            print(f"Error getting server activity stats: {e}")
            return {}
        finally:
            cursor.close()

# Global instance
db_helpers = DatabaseHelpers()