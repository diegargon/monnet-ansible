import os
import socket
import subprocess
import re
import subprocess
import re
import json

#from collections import defaultdict

# LOCAL
from log_linux import log, logpo

def bytes_to_mb(bytes_value):
    """
    bytes to megabytes.

import socket

def get_load_avg():
    load1, load5, load15 = os.getloadavg()
    current_cpu_usage = cpu_usage(load1)
    
    return {
        "loadavg": {
            "1min": round(load1, 2),
            "5min": round(load5, 2),
            "15min": round(load15, 2),
            "usage": round(current_cpu_usage, 2)
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

    return {"disksinfo": disks_info}

def get_cpus():
    return os.cpu_count()

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    return uptime_seconds

def cpu_usage(cpu_load):
    total_cpus = get_cpus()
    if total_cpus == 0:
        return False
    
    cpu_usage_percentage = (cpu_load / total_cpus) * 100

    return round(cpu_usage_percentage, 2)    

def read_cpu_stats():
    """ CPU Stats from /proc/stat."""
    with open("/proc/stat", "r") as f:
        for line in f:
            if line.startswith("cpu "):
                parts = line.split()
                user, nice, system, idle, iowait = map(int, parts[1:6])
                return user, nice, system, idle, iowait
    return None

def get_iowait(last_cpu_times, current_cpu_times):
    """
    Io wait/delay calculation
    :return: Percent IO Wait within call median
                     
    """

    # Calcular diferencias acumulativas
    user_diff = current_cpu_times.user - last_cpu_times.user
    nice_diff = current_cpu_times.nice - last_cpu_times.nice
    system_diff = current_cpu_times.system - last_cpu_times.system
    idle_diff = current_cpu_times.idle - last_cpu_times.idle
    iowait_diff = (current_cpu_times.iowait - last_cpu_times.iowait) if hasattr(current_cpu_times, 'iowait') else 0

    # Suma total de diferencias
    total_diff = user_diff + nice_diff + system_diff + idle_diff + iowait_diff

    # Actualizar el estado anterior
    last_cpu_times = current_cpu_times

    # Calcular el porcentaje de IO Wait
    if total_diff > 0:
        return (iowait_diff / total_diff) * 100

    return 0 


def get_listen_ports_info():
    """
    Fetch active connections using `ss` and return a flattened list of port details.
    """
    # Lista para almacenar los resultados planos
    ports_flattened = []

    try:
        # Run `ss` command to list listening sockets (both TCP and UDP)
        output = subprocess.check_output(['ss', '-tulnp'], text=True).splitlines()

        # Regex to parse `ss` output lines
        ss_regex = re.compile(r'(?P<state>LISTEN|UNCONN)\s+\d+\s+\d+\s+(?P<local_address>[^:]+|\*)\:(?P<port>\d+)\s+[^:]+:\*\s+users:\(\((?P<service>.+?)\)\)')

        for line in output:
            match = ss_regex.search(line)
            if match:
                local_address = match.group('local_address')
                port = int(match.group('port'))

                # Extract all services (multiple possible)
                services_raw = match.group('service')
                services = re.findall(r'"([^"]+)"', services_raw)

                # Determine protocol (TCP/UDP)
                protocol = 'tcp' if 'tcp' in line else 'udp'

                # Determine if IPv4 or IPv6
                ip_version = 'ipv6' if ':' in local_address else 'ipv4'

                # Add results for each service
                for service in services:
                    if local_address == '*':
                        # Handle wildcard address for both IPv4 and IPv6
                        ports_flattened.append({'interface': '0.0.0.0', 'port': port, 'service': service, 'protocol': protocol, 'ip_version': 'ipv4'})
                        ports_flattened.append({'interface': '[::]', 'port': port, 'service': service, 'protocol': protocol, 'ip_version': 'ipv6'})
                    else:
                        ports_flattened.append({'interface': local_address, 'port': port, 'service': service, 'protocol': protocol, 'ip_version': ip_version})

    except subprocess.CalledProcessError as e:
        print(f"Error executing ss command: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")

    return {"listen_ports_info": ports_flattened}


def is_system_shutting_down():
    """ Detecta si se esta apagando el sistema """
    try:
        result = subprocess.run(
            ["systemctl", "is-system-running"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() == "stopping"
    except subprocess.CalledProcessError as e:
        log(f"Error ejecutando el comando: {e}")
        return False
