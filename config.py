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
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"ERROR: {self.config_file} is empty! Please add your configuration.")
                        return {}
                    return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"ERROR: JSON syntax error in {self.config_file} at line {e.lineno}, column {e.colno}: {e.msg}")
                print(f"Please fix the JSON syntax in your config file.")
                return {}
            except Exception as e:
                print(f"ERROR: Unexpected error reading {self.config_file}: {e}")
                return {}
        else:
            print(f"ERROR: {self.config_file} not found! Please create your config file from the template.")
            print(f"Run: cp config.json.template config.json")
            return {}
    
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
                print("ERROR: Config validation failed after reload!")
                print("Please check your config.json file for missing sections.")
            else:
                print("Configuration reloaded successfully")
        except Exception as e:
            print(f"Error reloading configuration: {e}")

# Global config instance
try:
    config = Config()
    if not config.validate_config():
        print("ERROR: Config validation failed! Please check your config.json file.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load config: {e}")
    print("Please ensure config.json exists and is properly formatted.")
    # Create a minimal fallback to prevent total crash
    class FallbackConfig:
        def get(self, key, default=None):
            return default
        @property
        def database(self):
            return {"host": "localhost", "port": 3306, "user": "", "password": "", "database": ""}
        @property 
        def bot(self):
            return {"default_prefix": "*"}
        @property
        def api(self):
            return {}
    config = FallbackConfig()
    print("WARNING: Using minimal fallback configuration - bot may not work properly!")