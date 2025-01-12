""" Global Vars """


AGENT_VERSION = "0.128"

# Track timers
timers = {}

# Constants

# Log Types

LT_DEFAULT = 0
LT_EVENT = 1
LT_REMOTE_PORT_STATUS = 2
LT_ALERT = 3
LT_WARN = 4
LT_EVENT_ALERT = 5
LT_EVENT_WARN = 6

# Threshold

ALERT_THRESHOLD = 90
WARN_THRESHOLD = 80

# Timer Stats interval

TIMER_STATS_INTERVAL = 300

# Events
EVENT_EXPIRATION = 86400