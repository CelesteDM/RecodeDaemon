import threading
import os

class SharedState:
    def __init__(self, state_dir) -> None:
        self.state_dir = os.path.expandvars(state_dir)
        self._lock = threading.Lock()
        self._data = {
            "state": "",
            "active_queue": {},
            "queues": {},
        }

    def update(self, **kwargs) -> None:
        with self._lock:
            self._data.update(kwargs)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._data)

