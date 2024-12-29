from datetime import datetime, timezone


def get_datatime():
    return datetime.now(timezone.utc).isoformat()

def get_local_timezone():
    return datetime.now().astimezone().tzinfo