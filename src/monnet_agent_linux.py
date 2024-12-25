import ssl
import syslog
import time
import json
import signal
from pathlib import Path
import http.client

MAX_LOG_LEVEL = "debug"

# Ruta del archivo de configuracion
CONFIG_FILE_PATH = "/etc/monnet/agent-config"

# Variables globales
AGENT_VERSION = 0.8

running = True

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
        "debug": syslog.LOG_DEBUG,
        "info": syslog.LOG_INFO,
        "warning": syslog.LOG_WARNING,
        "error": syslog.LOG_ERR,
        "critical": syslog.LOG_CRIT,
    }

    if priority not in syslog_level:
        raise ValueError(f"Invalid priority level: {priority}. Valid options are {list(syslog_level.keys())}")
    if MAX_LOG_LEVEL not in syslog_level:
        raise ValueError(f"Invalid MIN_LOG_LEVEL: {MAX_LOG_LEVEL}. Valid options are {list(syslog_level.keys())}")

    if syslog_level[priority] <= syslog_level[MAX_LOG_LEVEL]:
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
        syslog.syslog(syslog_level[priority], message)
        syslog.closelog()

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
        log(f"Error loading configuration: {e}", "error")
        return None

def send_request(config):
    """ Send request to server """
    token = config["token"]
    id = config["id"]
    interval = config["default_interval"]
    ignore_cert = config["ignore_cert"]
    server_host = config["server_host"]
    server_endpoint = config["server_endpoint"]    
    
    payload = {
        "id": id,
        "cmd": "ping",
        "token": token,
        "interval": interval,
        "version": AGENT_VERSION,
        "data": []
    }
    
    try: 
        if ignore_cert:
            context = ssl._create_unverified_context()
        else:
            context = None
        connection = http.client.HTTPSConnection(server_host, context = context)       
        headers = {"Content-Type": "application/json"}
        connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
        response = connection.getresponse()
        raw_data = response.read().decode()
        log(f"Raw response: {raw_data}", "debug")
        
        if response.status == 200:  
            if raw_data:          
                return json.loads(raw_data)
            else:
                 log("Empty response from server", "error")
        else:
            log(f"Error HTTP: {response.status} {response.reason}, Respuesta: {raw_data}", "error")
        
    except Exception as e:
        log(f"Error on request: {e}", "error")
    finally:
        connection.close()
    return None

def validate_response(response, token):
    """Valida la respuesta recibida."""
    if response and response.get("cmd") == "pong" and response.get("token") == token:
        return response
    log("Invalid response or wrong token.", "warning")
    return None

def handle_signal(signum, frame):
    """Maneja las senales de inicio y detencion del daemon."""
    global running
    if signum in (signal.SIGINT, signal.SIGTERM):
        log("Signal finish receive. Stopping app...", "info")
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
    interval = config["default_interval"]

    # Configurar manejo de senales
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while running:
        log("Sending request to server. " + str(AGENT_VERSION), "debug")
        response = send_request(config)

        if response:
            valid_response = validate_response(response, token)
            if valid_response:
                data = valid_response.get("data", {})
                if isinstance(data, dict) and "refresh" in data:
                    try:
                        new_interval = int(data["refresh"])
                        if (interval != new_interval):
                            interval = new_interval
                            log(f"Interval update to {interval} seconds", "info")
                    except ValueError:
                        log("invalid refresh, using last valid interval.", "warning")

        time.sleep(interval)

if __name__ == "__main__":
    main()
