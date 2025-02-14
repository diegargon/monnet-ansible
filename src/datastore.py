"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)
"""

import json
from typing import Optional, Dict, Any
from log_linux import log

from typing import Optional, Dict, Any

class Datastore:
    """
        Keep data and Save/Load from disk in json format
    """
    def __init__(self, filename: str = "datastore.json"):
        """
        Initialization
        :param filename: File to save/load data.
        """
        self.filename = filename
        self.data: Dict[str, Optional[Dict[str, Any]]] = {
            "last_load_avg": None,
            "last_memory_info": None,
            "last_disk_info": None,
            "last_iowait": 0,
        }

    def update_data(self, key: str, data: Dict[str, Any]):
        """
        Updates the specified data set.
        If the key does not exist, it is automatically added to allow future expansion.
        """
        if key not in self.data:
            log(f"New data set added: {key}")
        self.data[key] = data
        # TODO save on exit or each X time
        self.save_data()

    def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the data set associated with the given key.
        """
        return self.data.get(key)

    def list_keys(self) -> list:
        """
        Returns a list of all registered keys.
        """
        return list(self.data.keys())
