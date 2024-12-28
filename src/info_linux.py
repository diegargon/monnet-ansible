import os

import socket

def get_load_avg():
    load1, load5, load15 = os.getloadavg()

    return {
        "loadavg": {
            "1min": round(load1, 2),
            "5min": round(load5, 2),
            "15min": round(load15, 2)
        }
    }

def get_memory_info():
    """
    Obtiene informacion detallada sobre la memoria del sistema.

    Returns:
        dict: Diccionario con la informacion de memoria bajo la clave "meminfo".
    """
    meminfo = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            key, value = line.split(":")
            meminfo[key.strip()] = int(value.split()[0]) * 1024  # Convertir a bytes

    return {
        "meminfo": {
            "total": meminfo.get("MemTotal", 0),
            "available": meminfo.get("MemAvailable", 0),
            "free": meminfo.get("MemFree", 0),
            "used": meminfo.get("MemTotal", 0) - meminfo.get("MemFree", 0),
            "percent": round((meminfo.get("MemTotal", 0) - meminfo.get("MemFree", 0)) / meminfo.get("MemTotal", 1) * 100, 2),
        }
    }

def get_nodename():
    return os.uname().nodename

def get_hostname():
    return socket.gethostname()

def get_ip_address(hostname):
    return socket.gethostbyname(hostname)