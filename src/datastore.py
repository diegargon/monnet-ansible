from typing import Optional, Dict, Any
# Local
from log_linux import log, logpo

from typing import Optional, Dict, Any

class Datastore:
    def __init__(self):
        # Initialization
        self.data: Dict[str, Optional[Dict[str, Any]]] = {
            "last_load_avg": None,
            "last_memory_info": None,
            "last_disk_info": None,
        }

    def update_data(self, key: str, data: Dict[str, Any]):
        """
        Updates the specified data set.
        If the key does not exist, it is automatically added to allow future expansion.
        """
        if key not in self.data:
            log(f"New data set added: {key}")
        self.data[key] = data

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
