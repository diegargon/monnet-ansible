"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)
"""

# Standard
import threading

# Local
import globals
import info_linux
#from log_linux import log, logpo


def check_listen_ports(datastore, notify_callback, startup=None):
    """

        Send port changes. Startup force send update every agent start/restart

    """
    if 'check_ports' in globals.timers:
        globals.timers['check_ports'].cancel()

    current_listen_ports_info = info_linux.get_listen_ports_info()
    last_listen_ports_info = datastore.get_data("last_listen_ports_info")

    if ( (current_listen_ports_info != last_listen_ports_info) or startup):
        datastore.update_data("last_listen_ports_info", current_listen_ports_info)
        notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar
    #else : #debug
    #    notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar

    globals.timers['check_ports']  = threading.Timer(
        globals.TIMER_STATS_INTERVAL,
        check_listen_ports,
        args=(datastore, notify_callback)
    )
    globals.timers['check_ports'].start()


def send_stats(datastore, notify_callback):
    """
        Send stats every TIME_STATS_INTERVAL
    """
    if 'send_stats' in globals.timers :
        globals.timers['send_stats'].cancel()
    # Load
    last_avg_stats = datastore.get_data("last_load_avg")
    if (last_avg_stats is None) :
        return
    load_stats_5m = last_avg_stats['loadavg']['5min']
    # Io wait
    iowait_last_stats = datastore.get_data("iowait_last_stat")
    if not iowait_last_stats:
        iowait_last_stats = datastore.get_data("last_iowait")
    last_iowait = datastore.get_data("last_iowait")
    average_iowait =  (iowait_last_stats + last_iowait) / 2
    datastore.update_data("iowait_last_stats", last_iowait)

    data = {
          'load_avg_stats': load_stats_5m,
          'iowait_stats': average_iowait
    }
    notify_callback('send_stats', data)
    globals.timers['send_stats']  = threading.Timer(
        globals.TIMER_STATS_INTERVAL,
        send_stats,
        args=(datastore, notify_callback)
    )
    globals.timers['send_stats'].start()
