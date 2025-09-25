"""
Configuration file for Discord Bot
Contains database credentials and other sensitive settings
"""

import os
import json
from typing import Dict, Any

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.config_data = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"{self.config_file} is empty, creating default config")
                        return self.create_default_config()
                    return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON syntax error in {self.config_file} at line {e.lineno}, column {e.colno}: {e.msg}")
                print(f"Creating backup of corrupted config and generating new default config")
                # Backup the corrupted file
                import shutil
                try:
                    shutil.copy(self.config_file, f"{self.config_file}.corrupted.backup")
                    print(f"Corrupted config backed up to {self.config_file}.corrupted.backup")
                except Exception as backup_e:
                    print(f"Failed to backup corrupted config: {backup_e}")
                return self.create_default_config()
            except FileNotFoundError:
                print(f"Error reading {self.config_file}, creating default config")
                return self.create_default_config()
            except Exception as e:
                print(f"Unexpected error reading {self.config_file}: {e}")
                return self.create_default_config()
        else:
            print(f"{self.config_file} not found, creating default config")
            return self.create_default_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration file"""
        default_config = {
            "database": {
                "host": "",
                "port": 3306,
                "user": "",
                "password": "",
                "database": ""
            },
            "bot": {
                "token": "",
                "default_prefix": "*",
                "guild_id": ,
                "announcement_channel_id": ,
                "startup_channel_id": ,
                "owner_user_id": ,
                "co_owner_user_id": 
            },
            "api": {
                "twitch": {
                    "channel": "bluecat201",
                    "client_id": "",
                    "client_secret": ""
                }
            }
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config_data: Dict[str, Any] = None):
        """Save configuration to file"""
        if config_data is None:
            config_data = self.config_data
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
            raise
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'database.host')"""
        keys = key_path.split('.')
        value = self.config_data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        self.save_config()
    
    @property
    def database(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config_data.get("database", {})
    
    @property
    def bot(self) -> Dict[str, Any]:
        """Get bot configuration"""
        return self.config_data.get("bot", {})
    
    @property
    def api(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.config_data.get("api", {})
    
    def validate_config(self) -> bool:
        """Validate configuration structure"""
        required_sections = ["database", "bot", "api"]
        for section in required_sections:
            if section not in self.config_data:
                print(f"Missing required config section: {section}")
                return False
        
        # Validate database section
        db_config = self.config_data.get("database", {})
        required_db_keys = ["host", "port", "user", "password", "database"]
        for key in required_db_keys:
            if key not in db_config:
                print(f"Missing required database config: {key}")
                return False
        
        return True
    
    def reload(self):
        """Reload configuration from file"""
        try:
            self.config_data = self.load_config()
            if not self.validate_config():
                print("Config validation failed after reload, using default config")
                self.config_data = self.create_default_config()
            print("Configuration reloaded successfully")
        except Exception as e:
            print(f"Error reloading configuration: {e}")

# Global config instance with error handling
try:
    config = Config()
    if not config.validate_config():
        print("Config validation failed, recreating default config")
        config.config_data = config.create_default_config()
except Exception as e:
    print(f"Critical error initializing config: {e}")
    # Create a minimal config to prevent total failure
    class FallbackConfig:
        def get(self, key, default=None):
            return default
        @property
        def database(self):
            return {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "childe"}
        @property 
        def bot(self):
            return {"default_prefix": "*"}
        @property
        def api(self):
            return {}
    config = FallbackConfig()
    print("Using fallback configuration")