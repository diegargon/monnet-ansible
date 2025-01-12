"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

    Misc utils

"""
import json
#from collections import defaultdict
from log_linux import log, logpo

"""
def normalize(data):
    if isinstance(data, defaultdict):
        return {k: normalize(v) for k, v in data.items()}
    elif isinstance(data, dict):
        return {k: normalize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize(v) for v in data]
    elif isinstance(data, tuple):  # Convierte tuplas en listas
        return list(data)
    elif isinstance(data, (str, int, float, bool)) or data is None:
        return data
    else:
        return str(data)
"""

""" NOT USED """
def are_equal(obj1, obj2):
    json1 = json.dumps(obj1, sort_keys=True)
    json2 = json.dumps(obj2, sort_keys=True)
    return json1 == json2

""" NOT USED """
def deep_compare(obj1, obj2):
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        if obj1.keys() != obj2.keys():
            return False
        return all(deep_compare(obj1[k], obj2[k]) for k in obj1)
    elif isinstance(obj1, list) and isinstance(obj2, list):
        if len(obj1) != len(obj2):
            return False
        return all(deep_compare(i, j) for i, j in zip(obj1, obj2))
    else:
        return obj1 == obj2