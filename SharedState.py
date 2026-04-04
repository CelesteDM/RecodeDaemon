import threading
import os
from pickle import load

class SharedState:
    def __init__(self, state_dir) -> None:
        self.state_dir = os.path.expandvars(state_dir)
        self._lock = threading.Lock()
        self._data = {
            "status": "",
            "active_queue": {},
            "queues": {},
        }

    def update(self, **kwargs) -> None:
        with self._lock:
            self._data.update(kwargs)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._data)

    def read_history(self) -> dict:
        history_path = os.path.join(self.state_dir, "history")
        if not os.access(history_path, os.F_OK):
            return {}
        history, index = {}, 0
        len = os.path.getsize(history_path)
        with open(history_path, 'rb') as history_file:
            while history_file.tell() < len:
                history[index] = load(history_file)
                index += 1
        return history

