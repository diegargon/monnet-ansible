import syslog
import time
import json
import signal
from pathlib import Path
from http.client import HTTPSConnection

MAX_LOG_LEVEL = "info"

# Ruta del archivo de configuración
CONFIG_FILE_PATH = "/etc/monnet/agent-config"

# Variables globales
AGENT_VERSION = "0.2"
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
    """Carga la configuración desde un archivo JSON."""
    try:
        with open(file_path, "r") as file:
            config = json.load(file)
            return {
                "id": config.get("id"),
                "token": config.get("token"),
                "default_interval": config.get("default_interval", 10),
                "ignore_cert": config.get("ignore_cert", False),
                "server_host": config.get("server_host", "localhost"),
                "server_endpoint": config.get("server_endpoint", "/")
            }
    except Exception as e:
        log(f"Error al cargar la configuración: {e}", "error")
        return None

def send_request(id, token, server_host, server_endpoint, ignore_cert):
    """Envía una petición al servidor."""
    payload = {
        "id": id,
        "cmd": "ping",
        "token": token,
        "version": AGENT_VERSION,
        "data": []
    }
    try:
        connection = HTTPSConnection(server_host, context=None if ignore_cert else None)
        headers = {"Content-Type": "application/json"}
        connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
        response = connection.getresponse()
        raw_data = response.read().decode()
        log(f"Respuesta cruda recibida: {raw_data}", "debug")
        
        if response.status == 200:  
            if raw_data:          
                return json.loads(raw_data)
            else:
                 log("Respuesta vacía del servidor", "error")
        else:
            log(f"Error HTTP: {response.status} {response.reason}, Respuesta: {raw_data}", "error")
        
    except Exception as e:
        log(f"Error al realizar la solicitud: {e}", "error")
    finally:
        connection.close()
    return None

def validate_response(response, token):
    """Valida la respuesta recibida."""
    if response and response.get("cmd") == "pong" and response.get("token") == token:
        return response
    log("Respuesta no válida o token no coincide.", "warning")
    return None

def handle_signal(signum, frame):
    """Maneja las señales de inicio y detención del daemon."""
    global running
    if signum in (signal.SIGINT, signal.SIGTERM):
        log("Señal de terminación recibida. Deteniendo el programa...", "info")
        running = False

def main():
    global running

    # Cargar la configuración desde el archivo
    config = load_config(CONFIG_FILE_PATH)
    if not config:
        log("No se pudo cargar la configuración. Terminando el programa.", "error")
        return

    token = config["token"]
    if not token:
        log("El archivo de configuración no contiene un token válido. Terminando el programa.", "error")
        return
    id = config["id"]
    interval = config["default_interval"]
    ignore_cert = config["ignore_cert"]
    server_host = config["server_host"]
    server_endpoint = config["server_endpoint"]

    # Configurar manejo de señales
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while running:
        log("Enviando solicitud al servidor...", "debug")
        response = send_request(id, token, server_host, server_endpoint, ignore_cert)

        if response:
            valid_response = validate_response(response, token)
            if valid_response:
                data = valid_response.get("data", {})
                if isinstance(data, dict) and "refresh" in data:
                    try:
                        new_interval = int(data["refresh"])
                        if (interval != new_interval):
                            interval = new_interval
                            log(f"Intervalo de actualización modificado a {interval} segundos.", "info")
                    except ValueError:
                        log("Valor de 'refresh' no es válido, usando el intervalo anterior.", "warning")

        time.sleep(interval)

if __name__ == "__main__":
    main()
