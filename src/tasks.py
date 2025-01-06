import threading

# Local
import globals
import info_linux
from log_linux import log, logpo


def check_listen_ports(datastore, notify_callback):
    
    if 'check_ports' in globals.timers:
        globals.timers['check_ports'].cancel()
    
    current_listen_ports_info = info_linux.get_listen_ports_info()
    last_listen_ports_info = datastore.get_data("last_listen_ports_info")
    
    if (current_listen_ports_info != last_listen_ports_info):        
        datastore.update_data("last_listen_ports_info", current_listen_ports_info)
        notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar
    #else : #debug
    #    notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar

    globals.timers['check_ports']  = threading.Timer(15, check_listen_ports, args=(datastore, notify_callback))
    globals.timers['check_ports'].start()
        
    #return timer  # Retorna el objeto Timer para control
    
