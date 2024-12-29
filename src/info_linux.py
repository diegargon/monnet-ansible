import os
import socket

def bytes_to_mb(bytes_value):
    """
    bytes to megabytes.

    Args:
        bytes_value (int): bytes.

    Returns:
        int:  megabytes (rounded).
    """
    return round(bytes_value / (1024 ** 2))

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
    Obtain memory info

    Returns:
        dict: "meminfo" dict
    """
    meminfo = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            key, value = line.split(":")
            meminfo[key.strip()] = int(value.split()[0]) * 1024  # Convertir a bytes

    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    free = meminfo.get("MemFree", 0)
    used = total - free

    return {
        "meminfo": {
            "total": bytes_to_mb(total),
            "available": bytes_to_mb(available),
            "free": bytes_to_mb(free),
            "used": bytes_to_mb(used),
            "percent": round((used / total) * 100, 2) if total > 0 else 0
        }
    }

def get_nodename():
    return os.uname().nodename

def get_hostname():
    return socket.gethostname()

def get_ip_address(hostname):
    return socket.gethostbyname(hostname)

def get_disks_info():
    """
    Obtain disks info from /proc/mount (/dev)

    Returns:
        dict: Disk partions info Key: disks
    """
    disks_info = []

    # Read
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            parts = line.split()
            device, mountpoint, fstype = parts[0], parts[1], parts[2]

            # Filter
            if not device.startswith("/dev/") or device == '/dev/fuse':
                continue

            # Info os.statvfs
            try:
                stat = os.statvfs(mountpoint)
                total = bytes_to_mb(stat.f_blocks * stat.f_frsize)
                free = bytes_to_mb(stat.f_bfree * stat.f_frsize)
                used = total - free
                percent = (used / total) * 100 if total > 0 else 0
                disks_info.append({
                    "device": device,           # Nombre del dispositivo
                    "mountpoint": mountpoint,   # Punto de montaje
                    "fstype": fstype,           # Tipo de sistema de archivos
                    "total": total,             # Tamaño total en bytes
                    "used": used,               # Espacio usado en bytes
                    "free": free,               # Espacio libre en bytes
                    "percent": round(percent, 2)# Porcentaje usado
                })
            except OSError:
                continue

    return {"disks": disks_info}