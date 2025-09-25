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
    db = MockDB()

class DatabaseHelpers:
    """Helper functions for database operations used by cogs"""
    
    # ECONOMY HELPERS
    @staticmethod
    async def get_bank_data() -> Dict[str, Any]:
        """Get all economy data (replacement for mainbank.json)"""
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
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
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
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
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
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
        if not DATABASE_AVAILABLE or not db.connection or not db.connection.is_connected():
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
    async def get_user_mood_data() -> Dict[str, Any]:
        """Get all user mood data"""
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

# Global instance
db_helpers = DatabaseHelpers()