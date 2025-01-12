"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Ansible Gateway

This code is just a basic/preliminary draft.

Originally to do task only ansible relate but will be a move to a more generic monnet-gateway service


Recive
{
    "command": playbook
    "data": {
        "playbook": "mi_playbook.yml",
        "extra_vars": {
            "var1": "valor1",
            "var2": "valor2"
        },
        "ip": "192.168.1.100",
        "limit": "mi_grupo"
        "user": "user" # optional
    }
}

Netcat test

echo '{"command": "playbook", "data": {"playbook": "test.yml"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "test.yml", "extra_vars": {"var1": "value1", "var2": "value2"}}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "linux-df.yml", "extra_vars": {}, "ip": "192.168.2.117"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "linux-df.yml", "extra_vars": {}, "ip": "192.168.2.117", "user": "ansible"}}' | nc localhost 65432

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

# Local
from log_linux import log, logpo

VERSION = "0.2"
MINOR_VERSION = 5
HOST = 'localhost'
PORT = 65432

ALLOWED_COMMANDS = ["playbook"]

"""

Client Handle

"""
def handle_client(conn, addr):
    try:
        log(f"Connection established from {addr}", "info")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            logpo("Data: ", data)
            try:
                # Convert received data to JSON
                request = json.loads(data.decode())

                # Check if 'command' exists
                command = request.get('command')
                if not command:
                    response = {"status": "error", "message": "Command not specified"}
                    conn.sendall(json.dumps(response).encode())
                    continue

                # Validate the command
                if command not in ALLOWED_COMMANDS:
                    response = {"status": "error", "message": f"Invalid command: {command}"}
                    conn.sendall(json.dumps(response).encode())
                    continue

                # Extract 'data' content
                data_content = request.get('data', {})

                # Process command-specific logic
                if command == "playbook":
                    # Extract fields specific to the "playbook" command
                    playbook = data_content.get('playbook')
                    extra_vars = data_content.get('extra_vars', {})
                    ip = data_content.get('ip', None)
                    limit = data_content.get('limit', None)
                    user = data_content.get('user', "ansible")

                    # Ensure playbook is specified
                    if not playbook:
                        response = {"status": "error", "message": "Playbook not specified"}
                    else:
                        try:
                            # Execute the playbook and retrieve the result
                            result = run_ansible_playbook(
                                playbook, extra_vars,
                                ip=ip,
                                user=user,
                                limit=limit
                            )

                            # Convert the result JSON to a dictionary
                            result_data = json.loads(result)  # Expected valid JSON
                            logpo("ResultData: ", result_data)
                            response = {
                                "version": str(VERSION) + '.' + str(MINOR_VERSION),
                                "status": "success",
                                "command": command,
                                "result": {}
                            }
                            response.update(result_data)
                        except json.JSONDecodeError as e:
                            response = {
                                "status": "error",
                                "message": "Failed to decode JSON: " + str(e)
                            }
                        except Exception as e:
                            response = {
                                "status": "error",
                                "message": "Error executing the playbook: " + str(e)
                            }

                # elif command == "another_command":
                #     # Handle 'another_command' logic
                #     pass

                logpo("Response: ", response)
                # Send the response back to the client in JSON format
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

        log(f"Connection with {addr} closed", "info")
        conn.close()

    except Exception as e:
        log(f"Error handling connection with {addr}: {str(e)}", "error")
"""

Server

"""
def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen()
            log(f"v{VERSION}.{MINOR_VERSION}: Esperando conexión en {HOST}:{PORT}...", "info")

            while True:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr)).start()

        except Exception as e:
            log(f"Error en el servidor: {str(e)}", "error")
            error_message = {"status": "error", "message": f"Error en el servidor: {str(e)}"}
            print(json.dumps(error_message))

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
            raise Exception(
                f"Error ejecutando Ansible: STDOUT: {stdout.decode()} STDERR: {stderr.decode()}"
            )


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

"""
    Main
"""

signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Ejecutar el servidor en segundo plano
    log("Iniciando el servicio Monnet Ansible...", "info")
    run_server()
