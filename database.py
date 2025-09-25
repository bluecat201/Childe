try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    print("Warning: mysql-connector-python not installed. Database functionality will be disabled.")
    print("Install it with: pip install mysql-connector-python")
    MYSQL_AVAILABLE = False
    # Mock classes for when MySQL is not available
    class mysql:
        class connector:
            @staticmethod
            def connect(*args, **kwargs):
                raise ImportError("MySQL connector not available")
    
    class Error(Exception):
        pass

import json
import asyncio
from typing import Dict, List, Any, Optional
import logging
from config import config

class DatabaseManager:
    def __init__(self):
        self.connection = None
        # Load database credentials from config
        db_config = config.database
        self.host = db_config.get("host", "localhost")
        self.port = db_config.get("port", 3306)
        self.user = db_config.get("user", "")
        self.password = db_config.get("password", "")
        self.database = db_config.get("database", "")
        
    async def connect(self):
        """Establish database connection"""
        if not MYSQL_AVAILABLE:
            logging.error("MySQL connector not available. Please install mysql-connector-python")
            return False
            
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True
            )
            if self.connection.is_connected():
                logging.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error connecting to database: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("MySQL connection closed")
    
    async def create_tables(self):
        """Create all necessary tables for the bot data"""
        cursor = self.connection.cursor()
        
        try:
            # Economy table (mainbank.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                    user_id BIGINT PRIMARY KEY,
                    wallet INT DEFAULT 0,
                    bank INT DEFAULT 0,
                    bag JSON DEFAULT NULL
                )
            """)
            
            # Leveling table (leveling.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leveling (
                    guild_id BIGINT,
                    user_id BIGINT,
                    xp INT DEFAULT 0,
                    level INT DEFAULT 1,
                    messages INT DEFAULT 0,
                    total_xp INT DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            
            # User mood data (user_mood_data.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_moods (
                    user_id BIGINT PRIMARY KEY,
                    happy INT DEFAULT 0,
                    sad INT DEFAULT 0,
                    stressed INT DEFAULT 0,
                    calm INT DEFAULT 0,
                    tired INT DEFAULT 0,
                    motivated INT DEFAULT 0,
                    others JSON DEFAULT NULL
                )
            """)
            
            # Server mood data (server_mood_data.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_moods (
                    guild_id BIGINT PRIMARY KEY,
                    mood_data JSON DEFAULT NULL
                )
            """)
            
            # Server settings (server_settings.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id BIGINT PRIMARY KEY,
                    prefix VARCHAR(10) DEFAULT '*',
                    settings JSON DEFAULT NULL
                )
            """)
            
            # Announcements (announcement_settings.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    guild_id BIGINT PRIMARY KEY,
                    settings JSON DEFAULT NULL
                )
            """)
            
            # Warnings (warnings.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    guild_id BIGINT,
                    user_id BIGINT,
                    warnings JSON DEFAULT NULL,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            
            # QOTD (qotd.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qotd (
                    guild_id BIGINT PRIMARY KEY,
                    settings JSON DEFAULT NULL
                )
            """)
            
            # Prefixes (prefixes.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prefixes (
                    guild_id BIGINT PRIMARY KEY,
                    prefix VARCHAR(10) DEFAULT '*'
                )
            """)
            
            # Mention preferences (mention_prefs.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mention_prefs (
                    user_id BIGINT PRIMARY KEY,
                    preferences JSON DEFAULT NULL
                )
            """)
            
            # Mental health config (mental_health_config.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mental_health_config (
                    guild_id BIGINT PRIMARY KEY,
                    config JSON DEFAULT NULL
                )
            """)
            
            # Mood dates (mood_dates.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mood_dates (
                    user_id BIGINT PRIMARY KEY,
                    dates JSON DEFAULT NULL
                )
            """)
            
            # Log channels (log_channels.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_channels (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT
                )
            """)
            
            # Level up channels (level_up_channels.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS level_up_channels (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT
                )
            """)
            
            # Leveling enabled (leveling_enabled.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leveling_enabled (
                    guild_id BIGINT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Ignored channels (ignored_channels.json)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ignored_channels (
                    guild_id BIGINT,
                    channel_id BIGINT,
                    PRIMARY KEY (guild_id, channel_id)
                )
            """)
            
            # Migration status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_status (
                    id INT PRIMARY KEY DEFAULT 1,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logging.info("All database tables created successfully")
            
        except Error as e:
            logging.error(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()
    
    async def is_migration_completed(self) -> bool:
        """Check if migration has already been completed"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT completed FROM migration_status WHERE id = 1")
            result = cursor.fetchone()
            return result[0] if result else False
        except Error:
            return False
        finally:
            cursor.close()
    
    async def mark_migration_completed(self):
        """Mark migration as completed"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO migration_status (id, completed) 
                VALUES (1, TRUE) 
                ON DUPLICATE KEY UPDATE completed = TRUE, completed_at = CURRENT_TIMESTAMP
            """)
        finally:
            cursor.close()
    
    async def migrate_json_data(self) -> Dict[str, Any]:
        """Migrate all JSON data to database"""
        migration_results = {
            "success": [],
            "errors": [],
            "total_records": 0
        }
        
        try:
            # Migrate economy data (mainbank.json)
            try:
                with open('mainbank.json', 'r') as f:
                    economy_data = json.load(f)
                
                cursor = self.connection.cursor()
                for user_id, data in economy_data.items():
                    cursor.execute("""
                        INSERT INTO economy (user_id, wallet, bank, bag) 
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        wallet = VALUES(wallet), 
                        bank = VALUES(bank), 
                        bag = VALUES(bag)
                    """, (int(user_id), data.get('wallet', 0), data.get('bank', 0), json.dumps(data.get('bag', []))))
                
                cursor.close()
                migration_results["success"].append(f"Economy: {len(economy_data)} records")
                migration_results["total_records"] += len(economy_data)
            except FileNotFoundError:
                migration_results["errors"].append("mainbank.json not found")
            except Exception as e:
                migration_results["errors"].append(f"Economy migration error: {str(e)}")
            
            # Migrate leveling data
            try:
                with open('leveling.json', 'r') as f:
                    leveling_data = json.load(f)
                
                cursor = self.connection.cursor()
                record_count = 0
                for guild_id, users in leveling_data.items():
                    for user_id, data in users.items():
                        cursor.execute("""
                            INSERT INTO leveling (guild_id, user_id, xp, level, messages, total_xp) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                            xp = VALUES(xp), 
                            level = VALUES(level), 
                            messages = VALUES(messages), 
                            total_xp = VALUES(total_xp)
                        """, (int(guild_id), int(user_id), data.get('xp', 0), 
                             data.get('level', 1), data.get('messages', 0), data.get('total_xp', 0)))
                        record_count += 1
                
                cursor.close()
                migration_results["success"].append(f"Leveling: {record_count} records")
                migration_results["total_records"] += record_count
            except FileNotFoundError:
                migration_results["errors"].append("leveling.json not found")
            except Exception as e:
                migration_results["errors"].append(f"Leveling migration error: {str(e)}")
            
            # Continue with other migrations...
            await self._migrate_remaining_files(migration_results)
            
        except Exception as e:
            migration_results["errors"].append(f"General migration error: {str(e)}")
        
        return migration_results
    
    async def _migrate_remaining_files(self, migration_results: Dict[str, Any]):
        """Migrate remaining JSON files"""
        json_files = [
            ('user_mood_data.json', self._migrate_user_moods),
            ('server_mood_data.json', self._migrate_server_moods),
            ('server_settings.json', self._migrate_server_settings),
            ('announcement_settings.json', self._migrate_announcements),
            ('warnings.json', self._migrate_warnings),
            ('qotd.json', self._migrate_qotd),
            ('prefixes.json', self._migrate_prefixes),
            ('mention_prefs.json', self._migrate_mention_prefs),
            ('mental_health_config.json', self._migrate_mental_health_config),
            ('mood_dates.json', self._migrate_mood_dates),
            ('log_channels.json', self._migrate_log_channels),
            ('level_up_channels.json', self._migrate_level_up_channels),
            ('leveling_enabled.json', self._migrate_leveling_enabled),
            ('ignored_channels.json', self._migrate_ignored_channels)
        ]
        
        for filename, migrate_func in json_files:
            try:
                count = await migrate_func()
                migration_results["success"].append(f"{filename}: {count} records")
                migration_results["total_records"] += count
            except FileNotFoundError:
                migration_results["errors"].append(f"{filename} not found")
            except Exception as e:
                migration_results["errors"].append(f"{filename} migration error: {str(e)}")
    
    async def _migrate_user_moods(self) -> int:
        with open('user_mood_data.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for user_id, moods in data.items():
            cursor.execute("""
                INSERT INTO user_moods (user_id, happy, sad, stressed, calm, tired, motivated, others) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                happy = VALUES(happy), sad = VALUES(sad), stressed = VALUES(stressed),
                calm = VALUES(calm), tired = VALUES(tired), motivated = VALUES(motivated),
                others = VALUES(others)
            """, (int(user_id), moods.get('happy', 0), moods.get('sad', 0), 
                 moods.get('stressed', 0), moods.get('calm', 0), moods.get('tired', 0),
                 moods.get('motivated', 0), json.dumps(moods.get('others', {}))))
        cursor.close()
        return len(data)
    
    async def _migrate_server_moods(self) -> int:
        with open('server_mood_data.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, mood_data in data.items():
            cursor.execute("""
                INSERT INTO server_moods (guild_id, mood_data) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE mood_data = VALUES(mood_data)
            """, (int(guild_id), json.dumps(mood_data)))
        cursor.close()
        return len(data)
    
    async def _migrate_server_settings(self) -> int:
        with open('server_settings.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        count = 0
        if 'guilds' in data:
            for guild_id, settings in data['guilds'].items():
                cursor.execute("""
                    INSERT INTO server_settings (guild_id, prefix, settings) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE prefix = VALUES(prefix), settings = VALUES(settings)
                """, (int(guild_id), settings.get('prefix', '*'), json.dumps(settings)))
                count += 1
        cursor.close()
        return count
    
    async def _migrate_announcements(self) -> int:
        with open('announcement_settings.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, settings in data.items():
            cursor.execute("""
                INSERT INTO announcements (guild_id, settings) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE settings = VALUES(settings)
            """, (int(guild_id), json.dumps(settings)))
        cursor.close()
        return len(data)
    
    async def _migrate_warnings(self) -> int:
        with open('warnings.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        count = 0
        for guild_id, users in data.items():
            for user_id, warnings in users.items():
                cursor.execute("""
                    INSERT INTO warnings (guild_id, user_id, warnings) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE warnings = VALUES(warnings)
                """, (int(guild_id), int(user_id), json.dumps(warnings)))
                count += 1
        cursor.close()
        return count
    
    async def _migrate_qotd(self) -> int:
        with open('qotd.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, settings in data.items():
            cursor.execute("""
                INSERT INTO qotd (guild_id, settings) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE settings = VALUES(settings)
            """, (int(guild_id), json.dumps(settings)))
        cursor.close()
        return len(data)
    
    async def _migrate_prefixes(self) -> int:
        with open('prefixes.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, prefix in data.items():
            cursor.execute("""
                INSERT INTO prefixes (guild_id, prefix) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE prefix = VALUES(prefix)
            """, (int(guild_id), prefix))
        cursor.close()
        return len(data)
    
    async def _migrate_mention_prefs(self) -> int:
        with open('mention_prefs.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for user_id, prefs in data.items():
            cursor.execute("""
                INSERT INTO mention_prefs (user_id, preferences) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE preferences = VALUES(preferences)
            """, (int(user_id), json.dumps(prefs)))
        cursor.close()
        return len(data)
    
    async def _migrate_mental_health_config(self) -> int:
        with open('mental_health_config.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, config in data.items():
            cursor.execute("""
                INSERT INTO mental_health_config (guild_id, config) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE config = VALUES(config)
            """, (int(guild_id), json.dumps(config)))
        cursor.close()
        return len(data)
    
    async def _migrate_mood_dates(self) -> int:
        with open('mood_dates.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for user_id, dates in data.items():
            cursor.execute("""
                INSERT INTO mood_dates (user_id, dates) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE dates = VALUES(dates)
            """, (int(user_id), json.dumps(dates)))
        cursor.close()
        return len(data)
    
    async def _migrate_log_channels(self) -> int:
        with open('log_channels.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, channel_id in data.items():
            cursor.execute("""
                INSERT INTO log_channels (guild_id, channel_id) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
            """, (int(guild_id), int(channel_id)))
        cursor.close()
        return len(data)
    
    async def _migrate_level_up_channels(self) -> int:
        with open('level_up_channels.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, channel_id in data.items():
            cursor.execute("""
                INSERT INTO level_up_channels (guild_id, channel_id) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
            """, (int(guild_id), int(channel_id)))
        cursor.close()
        return len(data)
    
    async def _migrate_leveling_enabled(self) -> int:
        with open('leveling_enabled.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        for guild_id, enabled in data.items():
            cursor.execute("""
                INSERT INTO leveling_enabled (guild_id, enabled) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE enabled = VALUES(enabled)
            """, (int(guild_id), bool(enabled)))
        cursor.close()
        return len(data)
    
    async def _migrate_ignored_channels(self) -> int:
        with open('ignored_channels.json', 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        count = 0
        for guild_id, channels in data.items():
            for channel_id in channels:
                cursor.execute("""
                    INSERT IGNORE INTO ignored_channels (guild_id, channel_id) 
                    VALUES (%s, %s)
                """, (int(guild_id), int(channel_id)))
                count += 1
        cursor.close()
        return count

# Global database instance
db = DatabaseManager()