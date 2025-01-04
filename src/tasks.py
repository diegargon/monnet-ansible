import threading

# Local
import globals
import info_linux
from log_linux import log, logpo
import utils

def check_ports(datastore, notify_callback):
    
    if 'check_ports' in globals.timers:
        globals.timers['check_ports'].cancel()
    
    """ defaultdict need normalization for compare """        
    current_ports_info = utils.normalize(info_linux.get_ports_grouped())
    last_ports_info = utils.normalize(datastore.get_data("last_ports_info"))

    #if not utils.are_equal(current_ports_info, last_ports_info):
    if (current_ports_info != last_ports_info):        
        datastore.update_data("last_ports_info", current_ports_info)
        notify_callback("ports_info", current_ports_info)  # Notificar al __main__       

    globals.timers['check_ports']  = threading.Timer(15 * 60, check_ports, args=(datastore, notify_callback))
    globals.timers['check_ports'].start()
        
    #return timer  # Retorna el objeto Timer para control
    
