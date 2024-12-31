
import syslog

MAX_LOG_LEVEL = "debug"

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
