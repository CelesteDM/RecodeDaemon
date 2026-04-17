from time import sleep
import threading
from SharedState import SharedState
from Daemon import Daemon

DAEMON_STATE_DIR = "$XDG_STATE_HOME/recoder"
THREADS = []

def test_setup():
    shared = SharedState(DAEMON_STATE_DIR)
    daemon = Daemon(shared)

    threading.Thread(target=daemon.run, daemon=False).start()

    while True:
        sleep(2)

test_setup()
