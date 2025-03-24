import json
import os

class ConfigLoader:
    """Loads configuration settings from `config.json` with dynamic paths."""

    def __init__(self, config_path=None):
        """Loads `config.json` from `src/main/`, unless a custom path is provided."""
        base_dir = os.path.abspath(os.path.dirname(__file__))
        self.config_path = config_path or os.path.join(base_dir, "config.json")
        self.config = self._load_config()

    def _load_config(self):
        """Loads JSON config data and updates paths dynamically."""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
                for key in config["paths"]:
                    config["paths"][key] = os.path.abspath(config["paths"][key])
                return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            return {}

    def get(self, key, default=None):
        """Fetches a value using dot notation."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                print(f"Warning: '{key}' not found in config.json. Using default: {default}")
                return default
        return value

config_loader = ConfigLoader()