"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)
"""

import time
from typing import List, Dict, Any
# Local
import globals
from log_linux import log, logpo
from constants import LogLevel
from constants import EventType

class EventProcessor:
    """
        Event Processor. Process and track the events avoid spamming
    """
    def __init__(self, ):
        """
        Inicializa el procesador de eventos.
        """
         # Dict  processed events with time stamp
        self.processed_events: Dict[str, float] = {}

        self.event_expiration = globals.EVENT_EXPIRATION

    def process_changes(self, datastore) -> List[Dict[str, Any]]:
        """
        Procesa los cambios en los datos del Datastore
        Devuelve una lista de eventos que no hayan sido enviados recientemente o hayan expirado.
        """
        events = []
        current_time = time.time()
        # Event > Iowait threshold
        iowait = datastore.get_data("last_iowait")
        if iowait  > globals.WARN_THRESHOLD:
            event_id = "high_io_delay"
            if iowait > globals.ALERT_THRESHOLD :
                log_level = LogLevel.ALERT# globals.LT_EVENT_ALERT
            else:
                log_level = LogLevel.WARNING
            event_type = EventType.HIGH_IOWAIT

            if self._should_send_event(event_id, current_time) :
                events.append({
                    "name": "high_iowait",
                    "data": {
                        "iowait": iowait,
                        "event_value": iowait,
                        "log_level": log_level,
                        "event_type": event_type
                        }
                })
                self._mark_event(event_id, current_time)

        # Event: > CPU threshold
        load_avg = datastore.get_data("last_load_avg")
        # logpo("Load avg", load_avg, "debug")
        if load_avg and "loadavg" in load_avg :
            loadavg_data = load_avg["loadavg"]
            if (
                loadavg_data.get("usage") is not None
                and loadavg_data.get("usage") > globals.WARN_THRESHOLD
            ):

                if loadavg_data.get("usage") > globals.ALERT_THRESHOLD :
                    log_level = LogLevel.ALERT
                else:
                    log_level = LogLevel.WARNING

                event_type = EventType.HIGH_CPU_USAGE
                event_id = "high_cpu_usage"

                if self._should_send_event(event_id, current_time):
                    events.append({
                        "name": "high_cpu_usage",
                        "data": {
                            "cpu_usage": loadavg_data["usage"],
                            "event_value": loadavg_data.get("usage"),
                            "log_level": log_level,
                            "event_type": event_type}
                    })
                    self._mark_event(event_id, current_time)

        # Event: > Memory threshold
        memory_info = datastore.get_data("last_memory_info")
        # logpo("Memory info", memory_info, "debug")
        if memory_info and "meminfo" in memory_info:
            meminfo_data = memory_info["meminfo"]
            if meminfo_data["percent"] > globals.WARN_THRESHOLD :
                event_id = "high_memory_usage"
                if meminfo_data["percent"] > globals.ALERT_THRESHOLD :
                    log_level = LogLevel.ALERT
                else:
                    log_level = LogLevel.WARNING

                event_type = EventType.HIGH_MEMORY_USAGE

                if self._should_send_event(event_id, current_time) :
                    events.append({
                        "name": "high_memory_usage",
                        "data": {
                            "memory_usage": meminfo_data,
                            "event_value": meminfo_data["percent"],
                            "log_level": log_level,
                            "event_type": event_type
                            }
                    })
                    self._mark_event(event_id, current_time)

        # Evento: Disk threshold
        disk_info = datastore.get_data("last_disk_info")
        if isinstance(disk_info, dict) and "disksinfo" in disk_info:
            for stats in disk_info["disksinfo"]:
                if isinstance(stats, dict):
                    if stats.get("percent")  and stats["percent"] > globals.WARN_THRESHOLD :
                        if stats["percent"] > globals.ALERT_THRESHOLD :
                            log_level = LogLevel.ALERT
                        else:
                            log_level = LogLevel.WARNING

                        event_type = EventType.HIGH_DISK_USAGE
                        event_id = f"high_disk_usage_{stats.get('device', 'unknown')}"

                        if self._should_send_event(event_id, current_time):
                            events.append({
                                "name": "high_disk_usage",
                                "data": {
                                    "disks_stats": stats,
                                    "event_value": stats["percent"],
                                    "log_level": log_level,
                                    "event_type": event_type
                                    }
                            })
                            self._mark_event(event_id, current_time)
        else:
            log(f"Unexpected structure in disk info: {type(disk_info)} -> {disk_info}", "error")
        # Cleanup processed_events
        self._cleanup_events(current_time)

        return events

    def _should_send_event(self, event_id: str, current_time: float) -> bool:
        """
        Verify if we send the event (time mark)
        """
        last_time = self.processed_events.get(event_id)
        return last_time is None or (current_time - last_time > self.event_expiration)

    def _mark_event(self, event_id: str, current_time: float):
        """
        Mark event, update time
        """
        self.processed_events[event_id] = current_time

    def _cleanup_events(self, current_time: float):
        """
        Clean old events
        """
        self.processed_events = {
            event_id: timestamp
            for event_id, timestamp in self.processed_events.items()
            if current_time - timestamp <= self.event_expiration * 2
        }
