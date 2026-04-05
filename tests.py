from time import sleep
import threading
from SharedState import SharedState
from SocketHandler import SocketHandler
from Daemon import Daemon

DAEMON_STATE_DIR = "$XDG_STATE_HOME/recoder"
THREADS = []

def test_setup():
    shared = SharedState(DAEMON_STATE_DIR)
    sockethandler = SocketHandler(shared)
    daemon = Daemon(shared)

    THREADS.append(threading.Thread(
        target=daemon.run, daemon=True
    ))

    THREADS.append(threading.Thread(
        target=sockethandler.run, daemon=True
    ))

    for thread in THREADS:
        thread.start()

    while True:
        sleep(60)

test_setup()
