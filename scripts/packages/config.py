"""
Configuration management for AlexCAD.

Handles saving and loading user preferences to ~/.alex/config.json
"""

import json
import os
from packages.constants import alex_dir


class Config:
    """Manages AlexCAD configuration settings."""
    
    def __init__(self):
        self.config_file = os.path.join(alex_dir, 'config.json')
        self.settings = self._load()
    
    def _load(self):
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load config: {e}")
                return self._defaults()
        return self._defaults()
    
    def _defaults(self):
        """Return default configuration."""
        return {
            'hot_reload_enabled': True,  # Default to enabled
        }
    
    def save(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save config: {e}")
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save."""
        self.settings[key] = value
        self.save()


# Global config instance
_config = None

def get_config():
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
