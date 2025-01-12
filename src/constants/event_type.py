"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)
"""

class EventType:
    HIGH_IOWAIT = 1
    HIGH_MEMORY_USAGE = 2
    HIGH_DISK_USAGE = 3
    HIGH_CPU_USAGE = 4
    STARTING = 5
    APP_SHUTDOWN = 6
    SYSTEM_SHUTDOWN = 7
    PORT_UP= 8
    PORT_DOWN = 9
    PORT_NEW = 10
    SEND_STATS = 11
    SERVICE_NAME_CHANGE = 12
    HOST_INFO_CHANGE = 13
    HOST_BECOME_ON = 14
    HOST_BECOME_OFF = 15
    NEW_HOST_DISCOVERY = 16
