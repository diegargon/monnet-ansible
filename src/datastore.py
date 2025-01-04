import json
from typing import Optional, Dict, Any
from log_linux import log, logpo

class Datastore:
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
            "last_ports_info": None,
            "last_iowait": 0,
        }
        self.load_data()

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

    def save_data(self):
        """
        Saves the current data to a JSON file.
        """
        try:
            with open(self.filename, "w") as file:
                json.dump(self.data, file, indent=4)
            log(f"Data saved successfully to {self.filename}")
        except Exception as e:
            log(f"Error saving data to {self.filename}: {e}")

    def load_data(self):
        """
        Loads data from a JSON file.
        """
        try:
            with open(self.filename, "r") as file:
                self.data = json.load(file)
            log(f"Data loaded successfully from {self.filename}")
        except FileNotFoundError:
            log(f"No existing data file found. Starting fresh.")
        except Exception as e:
            log(f"Error loading data from {self.filename}: {e}")
