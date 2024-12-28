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
import ssl
import syslog
import time
import json
import signal
import uuid
from pathlib import Path
from datetime import datetime

# Local

import http.client
import info_linux
import time_utils

MAX_LOG_LEVEL = "info"

# Ruta del archivo de configuracion
CONFIG_FILE_PATH = "/etc/monnet/agent-config"

# Variables globales
AGENT_VERSION = "0.46"
running = True
config = None

def logpo(msg: str, data, priority: str = "info") -> None:
    """
    Converts any Python data type to a string and logs it with a specified priority.

    Args:
        msg: A str
        data: The data to log. Can be any Python object.
        priority (str): The priority level (info, warning, error, critical).
                        Defaults to 'info'.

    Raises:
        ValueError: If the priority level is invalid in the underlying `log` function.
    """
    try:
        message = msg + str(data)  # Convert the data to a string representation
        log(message, priority)  # Call the original log function
    except ValueError as e:
        raise ValueError(f"Error in logging: {e}")

def log(message: str, priority: str = "info") -> None:
    """
    Sends a message to the system log (syslog) with a specified priority.

    Args:
        message (str): The message to log.
        priority (str): The priority level (info, warning, error, critical).
                        Defaults to 'info'.

    Raises:
        ValueError: If the priority level is invalid.
    """

    syslog_level = {
        "emerg": syslog.LOG_EMERG,
        "alert": syslog.LOG_ALERT,
        "crit": syslog.LOG_CRIT,
        "err": syslog.LOG_ERR,
        "warning": syslog.LOG_WARNING,
        "notice": syslog.LOG_NOTICE,
        "info": syslog.LOG_INFO,        
        "debug": syslog.LOG_DEBUG,        
    }

    if priority not in syslog_level:
        raise ValueError(f"Invalid priority level: {priority}. Valid options are {list(syslog_level.keys())}")
    if MAX_LOG_LEVEL not in syslog_level:
        raise ValueError(f"Invalid MIN_LOG_LEVEL: {MAX_LOG_LEVEL}. Valid options are {list(syslog_level.keys())}")

    if syslog_level[priority] <= syslog_level[MAX_LOG_LEVEL]:
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
        syslog.syslog(syslog_level[priority], message)
        syslog.closelog()

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
        "timestamp": timestamp,                 # Timestamp en UTC
        "timezone": str(local_timezone),        # Zona horaria local
        "hostname": hostname,                   # Nombre del host
        "nodename": nodename,                   # Nodename
        "ip_address": ip_address,               # Dirección IP local
        "agent_version": str(AGENT_VERSION),    # Versión del agente
        "uuid": _uuid                            # ID único de la petición
    }
    
def load_config(file_path):
    """Carga la configuracion desde un archivo JSON."""
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
        log(f"Error loading configuration: {e}", "err")
        return None

def send_notification(type, msg):
    """Send notification to server. No response"""
    global config
    
    token = config["token"]
    id = config["id"]
    ignore_cert = config["ignore_cert"]
    server_host = config["server_host"]
    server_endpoint = config["server_endpoint"]
    meta = get_meta()
    if type == 'starting':
        msg = msg.strftime("%H:%M:%S")

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

    # Datos básicos de configuración
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
        log(f"Error on request: {e}", "err")
    finally:
        # Close
        connection.close()

    return None

def validate_response(response, token):
    """Valida la respuesta recibida."""
    if response and response.get("cmd") == "pong" and response.get("token") == token:
        return response
    log("Invalid response from server or wrong token.", "warning")
    return None

def handle_signal(signum, frame):
    """Maneja las senales de inicio y detencion del daemon."""
    global running
    global config
    
    send_notification('signal', f"Signal receive {signum}")
    if signum in (signal.SIGINT, signal.SIGTERM):
        log(f"Signal {signum} finish receive. Stopping app...", "notice")
        running = False

def validate_config():
    """
    Validates that all required keys exist in the config and are not empty.
    
    :param config: dict containing configuration values.
    :param required_keys: list of keys to validate.
    :return: Tue or Raises ValueError if validation fails.
    """
    global config
    
    required_keys = ["token", "id", "default_interval", "ignore_cert", "server_host", "server_endpoint"]
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")
    else:
        log("Configuration is valid", "debug")
    return True

def main():
    global running        
    global config
    
    last_load_avg = None
    # Send load 5m for stats every 5m
    last_loadavg_stats_sent = 0   
    last_memory_info  = None
    last_disk_info = None
  
    log("Init monnet linux agent", "info")
    # Cargar la configuracion desde el archivo
    config = load_config(CONFIG_FILE_PATH)
    if not config:
        log("Cant load config. Finishing", "err")
        return

    try:
        validate_config()
    except ValueError as e:
        log(str(e), "err")
        return     
    
    token = config["token"]
    config["interval"] = config["default_interval"]

    # Configurar manejo de senales
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    send_notification('starting', datetime.now().time())
    
    while running:
        extra_data = {}
        current_load_avg = info_linux.get_load_avg()
        current_memory_info = info_linux.get_memory_info()
        current_disk_info = info_linux.get_disks_info()
        
        current_time = time.time() 
        
        if current_load_avg != last_load_avg:
            last_load_avg = current_load_avg
            extra_data.update(current_load_avg)
            
        if (current_time - last_loadavg_stats_sent) > (5 * 60):
            extra_data["loadavg_stats"] = current_load_avg['loadavg']['5min']
            last_loadavg_stats_sent = current_time                
            
        if (current_memory_info != last_memory_info):
            last_memory_info = current_memory_info
            extra_data.update(current_memory_info)
        
        if (current_disk_info != last_disk_info):
            last_disk_info = current_disk_info
            extra_data.update(current_disk_info)
       

        log("Sending ping to server. " + str(AGENT_VERSION), "debug")
        response = send_request(cmd="ping", data=extra_data)


        if response:
            log("Response receive... validating", "debug")
            valid_response = validate_response(response, token)
            if valid_response:                
                data = valid_response.get("data", {})
                new_interval = valid_response.get("refresh")
                if new_interval and config['interval'] != int(new_interval):
                    config["interval"] = new_interval
                    log(f"Interval update to {config['interval']} seconds", "info")
                if isinstance(data, dict) and "something" in data:
                    # example
                    try:
                        pass
                    except ValueError:
                        log("invalid", "warning")                        
            else:
                log("Invalid response receive", "warning")
        log(f"Sleeping for {config['interval']} seconds", "debug")                
        time.sleep(config["interval"])

if __name__ == "__main__":
    main()
