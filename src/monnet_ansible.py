"""
Monnet Ansible Gateway

This code is just a basic/preliminary draft.

Tests

{
  "playbook": "mi_playbook.yml",
  "extra_vars": {
    "var1": "valor1",
    "var2": "valor2"
  },
  "ip": "192.168.1.100",
  "limit": "mi_grupo"
}

Netcat test

echo '{"playbook": "test.yml"}' | nc localhost 65432
echo '{"playbook": "test.yml", "extra_vars": {"var1": "value1", "var2": "value2"}}' | nc localhost 65432
echo '{"playbook": "linux-df.yml", "{}",  "ip": "192.168.2.117" }' | nc localhost 65432
echo '{"playbook": "linux-df.yml", "extra_vars": {},  "ip": "192.168.2.117", "user": "ansible" }' | nc localhost 65432


"""
import traceback
import syslog
import socket
import subprocess
import json
import signal
import sys
import os
import threading
from time import sleep

MAX_LOG_LEVEL = "info"
VERSION = 0
MIN_VERSION = 35
HOST = 'localhost' 
PORT = 65432 


"""

Client Handle

"""
def handle_client(conn, addr):
    try:
        log(f"Conexión establecida desde {addr}", "info")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            logpo("Data: ", data)
            try:
                # Convertir los datos recibidos en formato JSON
                request = json.loads(data.decode())
                playbook = request.get('playbook')
                extra_vars = request.get('extra_vars', {})
                ip = request.get('ip', None)
                limit = request.get('limit', None) 
                user = request.get('user', "ansible") 

                # Verificar que se haya proporcionado un playbook
                if not playbook:
                    response = {"status": "error", "message": "Playbook no especificado"}
                else:
                    try:
                        # Ejecutar el playbook y obtener el resultado
                        result = run_ansible_playbook(playbook, extra_vars, ip=ip, user=user, limit=limit)

                        # Convertir el resultado JSON en un diccionario
                        result_data = json.loads(result)  # Se espera que 'result' sea un JSON válido
                        logpo("ResultData: ", result_data)
                        response = {
                            "version": str(VERSION) + '.' + str(MIN_VERSION),
                            "status": "success",
                            "result": {}
                        }
                        response.update(result_data)
                    except json.JSONDecodeError as e:
                        response = {"status": "error", "message": "Error al decodificar JSON: " + str(e)}
                    except Exception as e:
                        response = {"status": "error", "message": "Error ejecutando el playbook: " + str(e)}
                logpo("Response: ", response)
                # Enviar la respuesta de vuelta al cliente en formato JSON
                conn.sendall(json.dumps(response).encode())
            
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                relevant_trace = [frame for frame in tb if "monnet_ansible.py" in frame.filename]
                if relevant_trace:
                    last_trace = relevant_trace[-1]
                else:
                    last_trace = tb[-1]

                error_message = {
                    "status": "error",
                    "message": str(e),
                    "file": last_trace.filename,
                    "line": last_trace.lineno
                }
                conn.sendall(json.dumps(error_message).encode())

        log(f"Conexión con {addr} cerrada", "info")
        conn.close()

    except Exception as e:
        log(f"Error manejando la conexión con {addr}: {str(e)}", "error")
"""

Server

"""        
def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen()
            log(f"v{VERSION}.{MIN_VERSION}: Esperando conexión en {HOST}:{PORT}...", "info")
            
            while True:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr)).start()

        except Exception as e:
            log(f"Error en el servidor: {str(e)}", "error")
            error_message = {"status": "error", "message": f"Error en el servidor: {str(e)}"}
            print(json.dumps(error_message))

"""
def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen()
            log(f"v{VERSION}.{MIN_VERSION}: Esperando conexión en {HOST}:{PORT}...", "info")
            
            # Aceptar una conexión entrante (servidor web será quien se conecte)
            conn, addr = s.accept()
            with conn:
                log(f"Conexión establecida desde {addr}", "info")
                
                while True:
                    data = conn.recv(1024)

                    if not data:
                        break  # Salir si no se recibe nada
                    logpo("Data: ", data)
                    try:
                        # Convertir los datos recibidos en formato JSON
                        request = json.loads(data.decode())
                        playbook = request.get('playbook')
                        extra_vars = request.get('extra_vars', {})
                        ip = request.get('ip', None)
                        limit = request.get('limit', None) 
                        user = request.get('user', "ansible") 

                        # Verificar que se haya proporcionado un playbook
                        if not playbook:
                            response = {"status": "error", "message": "Playbook no especificado"}
                        else:
                            try:
                                # Ejecutar el playbook y obtener el resultado
                                result = run_ansible_playbook(playbook, extra_vars, ip=ip, user=user, limit=limit)

                                # Convertir el resultado JSON en un diccionario
                                result_data = json.loads(result)  # Se espera que 'result' sea un JSON válido
                                logpo("ResultData: ", result_data)
                                response = {
                                    "version": str(VERSION) + '.' + str(MIN_VERSION) ,
                                    "status": "success",
                                    "result": {}                                    
                                }
                                response.update(result_data)
                            except json.JSONDecodeError as e:
                                response = {"status": "error", "message": "Error al decodificar JSON: " + str(e)}
                            except Exception as e:
                                response = {"status": "error", "message": "Error ejecutando el playbook: " + str(e)}
                        logpo("Response: ", response)
                        # Enviar la respuesta de vuelta al cliente en formato JSON
                        conn.sendall(json.dumps(response).encode())
                    
                    except Exception as e:
                        tb = traceback.extract_tb(e.__traceback__)
                        relevant_trace = [frame for frame in tb if "monnet_ansible.py" in frame.filename]
                        if relevant_trace:
                            last_trace = relevant_trace[-1]
                        else:                            
                            last_trace = tb[-1]

                        error_message = {
                            "status": "error",
                            "message": str(e),
                            "file": last_trace.filename,
                            "line": last_trace.lineno
                        }
                        conn.sendall(json.dumps(error_message).encode())
            log(f"Conexión con {addr} cerrada", "info")
        except Exception as e:            
            log(f"Error en el servidor: {str(e)}", "error")
            error_message = {"status": "error", "message": f"Error en el servidor: {str(e)}"}
            print(json.dumps(error_message))

"""

def run_ansible_playbook(playbook, extra_vars=None, ip=None, user=None, limit=None):
    # extra vars to json
    extra_vars_str = ""
    if extra_vars:
        extra_vars_str = json.dumps(extra_vars)

    playbook_path = os.path.join('playbooks', playbook)
    
    command = ['ansible-playbook', playbook_path]

    if extra_vars_str:
        command.extend(['--extra-vars', extra_vars_str])    

    if ip:
        command.insert(1, '-i')
        command.insert(2, f"{ip},") 

    if limit:
        command.extend(['--limit', limit])

    if user:
        command.extend(['-u', user])

    try:         
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()    
        if stderr:
            raise Exception(f"Error ejecutando Ansible: STDOUT: {stdout.decode()} STDERR: {stderr.decode()}")

    
        return stdout.decode()

    except Exception as e:
        error_message = {
            "status": "error",
            "message": str(e)
        }
        return json.dumps(error_message)

def signal_handler(sig, frame):
    """Manejador de señales para capturar la terminación del servicio"""
    log("Monnet ansible server shuttdown...", "info")
    sys.exit(0)

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

    if syslog_level[priority] <= syslog_level[MAX_LOG_LEVEL]:
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
        syslog.syslog(syslog_level[priority], message)
        syslog.closelog()


"""
    Main
"""

signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Ejecutar el servidor en segundo plano
    log("Iniciando el servicio Monnet Ansible...", "info")
    run_server()
