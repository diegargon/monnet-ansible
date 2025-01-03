"""
Payload Structure Documentation

{
    'id': str,                # Unique Host identifier 
    'cmd': str,               # Command to execute. Example: "ping"
    'token': str,             # Authentication token. Example: "73a7a18ce78742aa8aadacbe6a918dd8"
    'interval': int,          # Interval in seconds
    'version': str,           # Version software. Example:
    'data': {                 # Contains other info
        'mydata': {           
            'data1': 1,       
            'data2': 1,       
            'data3': 1        
        }
    },
    'meta': {                 # Metadata about the payload source and environment.
        'timestamp': str,     # ISO 8601 timestamp of when the payload was generated.
        'timezone': str,      # Time zone identifier.
        'hostname': str,      # Hostname of the system that generated the payload.
        'nodename': str,      # Nodename of the system.
        'ip_address': str,    # IP address of the system.
        'agent_version': str, # Version of the agent that generated the payload.
        'uuid': str           # Unique identifier (UUID) of the system or agent.
    }
    
Response Structure Documentation

{
    'cmd': str,              # Command response type. Example: "pong"
    'token': str,            # Token used for authentication or identification. Example: "73a7a18ce78742aa8aadacbe6a918dd8"
    'version': float,        # Version of the response or system. Example: 0.22
    'response_msg': bool,    # Indicates if the response message is successful. Example: True
    'refresh': int,          # Refresh interval in seconds. Example: 5
    'data': list             # List of data, typically empty in this case. Example: []
}    
"""
import os
import ssl
import time
import json
import signal
import uuid
import time
import psutil

from pathlib import Path
from datetime import datetime
import http.client

# Local
from log_linux import log, logpo
import info_linux
import time_utils
from datastore import Datastore
from event_processor import EventProcessor

# Config file
CONFIG_FILE_PATH = "/etc/monnet/agent-config"

# Global Var
AGENT_VERSION = "0.73"
running = True

def get_meta():
    """
    Builds metadata
    Returns:
        dict: Dict with metadata
    """

    timestamp = time_utils.get_datatime()
    local_timezone = time_utils.get_local_timezone()
    hostname = info_linux.get_hostname()
    nodename = info_linux.get_nodename()
    ip_address = info_linux.get_ip_address(hostname)    
    _uuid = str(uuid.uuid4())

    return {
        "timestamp": timestamp,                 # Timestamp  UTC
        "timezone": str(local_timezone),        # Timezone
        "hostname": hostname,                   
        "nodename": nodename,                   
        "ip_address": ip_address,               
        "agent_version": str(AGENT_VERSION),    
        "uuid": _uuid                           # ID uniq
    }
    
def load_config(file_path):
    """Load JSON config"""
    try:
        with open(file_path, "r") as file:
            config = json.load(file)
            return {
                "id": config.get("id"),
                "token": config.get("token"),
                "default_interval": config.get("default_interval", 10),
                "ignore_cert": config.get("ignore_cert", True),
                "server_host": config.get("server_host", "localhost"),
                "server_endpoint": config.get("server_endpoint", "/")
            }
    except Exception as e:
        log(f"Error loading configuration: {e}", "error")
        return None

""" 
    Send notification to server. No response 
    
"""
def send_notification(name, data):
    global config
    
    token = config["token"]
    id = config["id"]
    ignore_cert = config["ignore_cert"]
    server_host = config["server_host"]
    server_endpoint = config["server_endpoint"]
    meta = get_meta()
    if name == 'starting':
        data["msg"] = data["msg"].strftime("%H:%M:%S")
    data["name"] = name
    
    payload = {
        "id": id,
        "cmd": "notification",
        "token": token,
        "version": AGENT_VERSION,        
        "data": {
            "type": type,
            "msg": msg            
            },
        "meta": meta
    }

    try: 
        if ignore_cert:
            context = ssl._create_unverified_context()
        else:
            context = None
        connection = http.client.HTTPSConnection(server_host, context=context)
        headers = {"Content-Type": "application/json"}
        connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
        log(f"Notification sent: {payload['data']['type']} {payload['data']['msg']}", "debug")
    except Exception as e:
        log(f"Error sending notification: {e}", "err")
    finally:
        connection.close()
        
def send_request(cmd="ping", data=None):
    """
    Send request to server.

    Args:
        cmd (str): Command
        data (dict): Extra data

    Returns:
        dict or None: Server response o None if error
    """
    global config

    # Get base config
    token = config["token"]
    id = config["id"]
    interval = config["interval"]
    ignore_cert = config["ignore_cert"]
    server_host = config["server_host"]
    server_endpoint = config["server_endpoint"]
    meta = get_meta()
    payload = {
        "id": id,
        "cmd": cmd,
        "token": token,
        "interval": interval,
        "version": AGENT_VERSION,
        "data": data or {},
        "meta": meta
    }

    try:
        # Accept all certs
        if ignore_cert:
            context = ssl._create_unverified_context()
        else:
            context = None

        connection = http.client.HTTPSConnection(server_host, context=context)
        headers = {"Content-Type": "application/json"}
        log(f"Payload: {payload}", "debug")
        connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
        # Response
        response = connection.getresponse()
        raw_data = response.read().decode()
        log(f"Raw response: {raw_data}", "debug")

        if response.status == 200:
            if raw_data:
                return json.loads(raw_data)
            else:
                log("Empty response from server", "err")
        else:
            log(f"Error HTTP: {response.status} {response.reason}, Respuesta: {raw_data}", "err")

    except Exception as e:
        log(f"Error on request: {e}", "error")
    finally:
        # Close
        connection.close()

    return None

def validate_response(response, token):
    """ Basic response validation """
    if response and response.get("cmd") == "pong" and response.get("token") == token:
        return response
    log("Invalid response or wrong token.", "warning")
    return None

def handle_signal(signum, frame):
    """ Signal Handler """
    global running
    global config
    
    signal_name = None
    msg = None
    notification_type = "shutdown"
    
    if signum == signal.SIGTERM:
        signal_name = 'SIGTERM'
    elif signum == signal.SIGHUP:
        signal_name = 'SIGHUP'
    else:
        signal_name = signum
    
    if os.path.exists("/run/systemd/shutdown"):
        with open("/run/systemd/shutdown", "r") as f:
            shutdown_info = f.read()
            msg = "System shutdown: " + shutdown_info            
            notification_type = "system_shutdown"
    else:
        msg = "Signal receive: {signal_name}. Closing application."
        
    log(f"Receive Signal {signal_name}  Stopping app...", "notice")
    
    data = {"msg": msg}                    
    send_notification(notification_type, data)

    running = False

def validate_config(config):
    """
    Validates that all required keys exist in the config and are not empty.
    
    :param config: dict containing configuration values.
    :param required_keys: list of keys to validate.
    :return: None. Raises ValueError if validation fails.
    """
    required_keys = ["token", "id", "default_interval", "ignore_cert", "server_host", "server_endpoint"]
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")

def main():
    global running        
    
    datastore = Datastore()
    event_processor = EventProcessor()
    # Stats Interval 5m
    stats_interval = (5 * 60)     
    
    # Send load_avg['5m'] for stats every 5m    
    last_stats_sent = 0   
    # Used for iowait
    last_cpu_times = psutil.cpu_times()
  
    log("Init monnet linux agent", "info")
    # Cargar la configuracion desde el archivo
    config = load_config(CONFIG_FILE_PATH)
    if not config:
        log("Cant load config. Finishing", "error")
        return

    try:
        validate_config(config)
    except ValueError as e:
        log(str(e), "error")
        return     
    
    token = config["token"]
    config["interval"] = config["default_interval"]

    # Signal Handle
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while running:
        extra_data = {}
        current_load_avg = info_linux.get_load_avg()
        current_memory_info = info_linux.get_memory_info()
        current_disk_info = info_linux.get_disks_info()
        
        current_time = time.time() 
                           
        # Check and update load average
        if current_load_avg != datastore.get_data("last_load_avg"):
            datastore.update_data("last_load_avg", current_load_avg)
            extra_data.update(current_load_avg)               
        
        # Check and update memory info
        if current_memory_info != datastore.get_data("last_memory_info"):
            datastore.update_data("last_memory_info", current_memory_info)
            extra_data.update(current_memory_info)
        
        # Check and update disk info
        if current_disk_info != datastore.get_data("last_disk_info"):
            datastore.update_data("last_disk_info", current_disk_info)
            extra_data.update(current_disk_info)

        # Get IOwait
        current_cpu_times = psutil.cpu_times()
        current_iowait = info_linux.get_iowait(last_cpu_times, current_cpu_times)
        current_iowait = round(current_iowait, 2)
        if current_iowait != datastore.get_data("last_iowait"):            
            datastore.update_data("last_iowait", current_iowait)
            extra_data.update({'iowait': current_iowait})            
        last_cpu_times = current_cpu_times
        
        # Send stats ever stats interval
        if (current_time - last_stats_sent) > stats_interval:
            extra_data["loadavg_stats"] = current_load_avg['loadavg']['5min']
            extra_data["iowait_stats"] = current_iowait
            last_stats_sent = current_time
                        
        log("Sending ping to server. " + str(AGENT_VERSION), "debug")
        response = send_request(cmd="ping", data=extra_data)

        events = event_processor.process_changes(datastore)
        for event in events:
            logpo("Sending event:", event, "debug")
            send_notification(event["name"], event["data"])
                    
        if response:
            valid_response = validate_response(response, token)
            if valid_response:
                data = valid_response.get("data", {})
                if isinstance(data, dict) and "refresh" in data:
                    try:
                        new_interval = int(data["refresh"])
                        if (config["interval"] != new_interval):
                            config["interval"] = new_interval
                            log(f"Interval update to {config['interval']} seconds", "info")
                    except ValueError:
                        log("invalid refresh, using default interval.", "warning")
                        config["interval"] = config["default_interval"]
            else:
                log("Invalid response receive", "warning")
        
        end_time = time.time()
        duration = end_time - current_time
        log(f"Tiempo bucle {duration:.2f} + Sleeping {config['interval']} (segundos).", "debug")              
        time.sleep(config["interval"])

if __name__ == "__main__":
    main()
