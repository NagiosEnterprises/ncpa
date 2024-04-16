daemon_instance = None

def set_daemon(instance):
    global daemon_instance
    daemon_instance = instance

def get_daemon():
    return daemon_instance