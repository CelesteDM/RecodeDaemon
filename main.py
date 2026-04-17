from SharedState import SharedState
from Recoder import Recoder
from daemon import DaemonContext

DAEMON_STATE_DIR = "$XDG_STATE_HOME/recoder"

shared = SharedState(DAEMON_STATE_DIR)

with DaemonContext():
    Recoder(shared).run()
