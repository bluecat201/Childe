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
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Error reading {self.config_file}, creating default config")
                return self.create_default_config()
        else:
            print(f"{self.config_file} not found, creating default config")
            return self.create_default_config()
    
    
    def save_config(self, config_data: Dict[str, Any] = None):
        """Save configuration to file"""
        if config_data is None:
            config_data = self.config_data
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
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

# Global config instance
config = Config()