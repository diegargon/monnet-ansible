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

def get_disks_info():
    """
    Obtain disks info from /proc/mount (/dev)

    Returns:
        dict: Disk partions info Key: disks
    """
    disks_info = []
    
    real_filesystems = {
        "ext4", "ext3", "ext2", "xfs", "zfs", "btrfs", "reiserfs",
        "vfat", "fat32", "ntfs", "hfsplus", "exfat", "iso9660",
        "udf", "f2fs", "nfs"
    }

    # Read
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            parts = line.split()
            device, mountpoint, fstype = parts[0], parts[1], parts[2]

            # Filter
            if fstype not in real_filesystems:
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

    return {"disksinfo": disks_info}


def get_cpus():
    return os.cpu_count()

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    return uptime_seconds