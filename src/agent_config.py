"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)
"""

import json
import os
# Local
from log_linux import log, logpo

def load_config(file_path):
    """Load JSON config"""
    try:
        with open(file_path, "r") as file:
            config = json.load(file)
            config['_config_path'] = file_path
            return config
    except Exception as e:
        log(f"Error loading configuration: {e}", "err")
        return None

def update_config(config: dict, key: str, value):
    """
    Updates or adds a key-value pair in the given configuration dictionary and saves it to the file.

    Args:
        config (dict): The loaded configuration dictionary containing `_config_path`.
        key (str): The key to add or update.
        value (Any): The value to set for the key.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    try:
        if '_config_path' not in config:
            raise ValueError("Configuration dictionary missing '_config_path' key.")

        # Update or add the key-value pair
        config[key] = value

        # Save the updated config back to the file
        with open(config['_config_path'], 'w') as file:
            json.dump(config, file, indent=4)

        return True
    except Exception as e:
        print(f"Error updating configuration: {e}")
        return False
