import unittest
from unittest.mock import patch, MagicMock
import json
import subprocess
import socket
import sys
import os
import signal
import time
import select


# Modificar sys.path para incluir el directorio src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from monnet_ansible import run_ansible_playbook

class TestMonnetAnsible(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Configurar el entorno para iniciar el servidor una vez"""
        cls.server_script = os.path.abspath("src/monnet_ansible.py")

        # Iniciar el servidor en un subproceso
        cls.server_process = subprocess.Popen(
            ["python3", cls.server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(1)  # Dar tiempo para que el servidor inicie

        """ Verificar que arranco """
        if cls.server_process.poll() is not None:
            stdout, stderr = cls.server_process.communicate()
            raise RuntimeError(
                f"El servidor no se inició correctamente:\nSTDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
            )

    @classmethod
    def tearDownClass(cls):
        """Detener el servidor después de todas las pruebas"""
        if cls.server_process.poll() is None:  # Si el proceso sigue activo
            os.kill(cls.server_process.pid, signal.SIGTERM)
            cls.server_process.wait()   

    def test_server_is_running(self):
        """Verificar que el servidor sigue ejecutándose después de iniciarlo"""
        self.assertIsNone(
            self.server_process.poll(), 
            "El servidor no está corriendo después de iniciarlo"
        )

    def test_server_no_output(self):
        """Comprobar que el servidor no produce salida inesperada al iniciarse"""
        # Esperar un breve momento para verificar salida
        time.sleep(3)

        stdout_lines = []
        stderr_lines = []

        start_time = time.time()
        while time.time() - start_time < 3:
            # Usamos select para verificar si hay datos para leer sin bloquear
            readable, _, _ = select.select([self.server_process.stdout, self.server_process.stderr], [], [], 0.1)

            for stream in readable:
                if stream is self.server_process.stdout:
                    stdout_line = stream.readline()
                    if stdout_line:
                        stdout_lines.append(stdout_line)

                if stream is self.server_process.stderr:
                    stderr_line = stream.readline()
                    if stderr_line:
                        stderr_lines.append(stderr_line)
            
            time.sleep(0.1) 

        self.assertEqual(b"".join(stdout_lines), b"", "El servidor produjo salida inesperada en stdout")
        self.assertEqual(b"".join(stderr_lines), b"", "El servidor produjo errores en stderr")

        # Imprimimos la salida si existe
        if stdout_lines:
            print("stdout server lines:")
            print(b"".join(stdout_lines).decode())

        if stderr_lines:
            print("stderr server lines:")
            print(b"".join(stderr_lines).decode())

    @patch('subprocess.Popen')    
    def test_run_ansible_playbook_success(self, mock_subprocess):
        # Simular un resultado exitoso de Ansible
        mock_process = MagicMock()  # Creamos el mock del proceso
        mock_process.returncode = 0  # El código de salida es 0 (éxito)
        mock_process.communicate.return_value = (b'{"status": "success", "result": {"custom_stats": {}, "global_custom_stats": {}}}', b"")

        # Cuando se llame a subprocess.Popen, devolveremos nuestro mock del proceso
        mock_subprocess.return_value = mock_process

        # Llamar a la función
        result = run_ansible_playbook("test.yml", {"var1": "value1"}, "127.0.0.1", "ansible")
        
        result_dict = json.loads(result) 
        print("Resultado completo:", result_dict)
        # Validar el resultado
        self.assertEqual(result_dict['status'], 'success')
        self.assertEqual(result_dict['result']['custom_stats'], {})
        self.assertEqual(result_dict['result']['global_custom_stats'], {})

"""
    @patch('subprocess.run')
    def test_run_ansible_playbook_failure(self, mock_subprocess):
        # Simular un error en Ansible
        mock_subprocess.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"Error ejecutando Ansible")
        
        # Validar que se lance una excepción
        with self.assertRaises(Exception):
            run_ansible_playbook("test_playbook.yml", {"var1": "value1"})
"""

if __name__ == '__main__':
    unittest.main()
