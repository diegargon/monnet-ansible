import time
from typing import List, Dict, Any
# Local
from log_linux import log, logpo

class EventProcessor:
    def __init__(self, cpu_threshold: float = 80.0, event_expiration: int = 300):
        """
        Inicializa el procesador de eventos.
        :param cpu_threshold: Umbral para el uso de CPU.
        :param event_expiration: Tiempo en segundos después del cual un evento puede reenviarse.
        """
         # Dict  processed events with time stamp
        self.processed_events: Dict[str, float] = {} 
        self.cpu_threshold = cpu_threshold
        self.event_expiration = event_expiration

    def process_changes(self, datastore) -> List[Dict[str, Any]]:
        """
        Procesa los cambios en los datos del Datastore
        Devuelve una lista de eventos que no hayan sido enviados recientemente o hayan expirado.
        """
        events = []
        current_time = time.time()
        # Event > Iowait threshold
        iowait = datastore.get_data("last_iowait")
        if iowait > 0.8:
            event_id = "high_io_delay"
            if self._should_send_event(event_id, current_time):
                events.append({
                    "name": "high_iowait",
                    "data": {"iowait": iowait}
                })
                self._mark_event(event_id, current_time)

        # Event: > CPU threshold
        load_avg = datastore.get_data("last_load_avg")
        # logpo("Load avg", load_avg, "debug")
        if load_avg and "loadavg" in load_avg:
            loadavg_data = load_avg["loadavg"]
            if loadavg_data.get("usage") is not None and loadavg_data.get("usage") > self.cpu_threshold:
                event_id = "high_cpu_usage"
                if self._should_send_event(event_id, current_time):
                    events.append({
                        "name": "high_cpu_usage",
                        "data": {"cpu_usage": loadavg_data["usage"]}
                    })
                    self._mark_event(event_id, current_time)

        # Event: > Memory threshold
        memory_info = datastore.get_data("last_memory_info")
        # logpo("Memory info", memory_info, "debug")
        if memory_info and "meminfo" in memory_info:
            meminfo_data = memory_info["meminfo"]
            if meminfo_data.get("used") is not None and meminfo_data.get("total", 1) > 0:
                if meminfo_data["used"] / meminfo_data["total"] > 0.8: # threshold
                    event_id = "high_memory_usage"
                    if self._should_send_event(event_id, current_time):
                        events.append({
                            "name": "high_memory_usage",
                            "data": {"memory_usage": meminfo_data}
                        })
                        self._mark_event(event_id, current_time)

        # Evento: Disk threshold
        disk_info = datastore.get_data("last_disk_info")
        if isinstance(disk_info, dict) and "disksinfo" in disk_info:
            for stats in disk_info["disksinfo"]:
                if isinstance(stats, dict): 
                    if stats.get("used") is not None and stats.get("total", 0) > 0:
                        if stats["used"] / stats["total"] > 0.9:  # threashold
                            event_id = f"high_disk_usage_{stats.get('device', 'unknown')}"
                            if self._should_send_event(event_id, current_time):
                                events.append({
                                    "name": "high_disk_usage",
                                    "data": stats
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
