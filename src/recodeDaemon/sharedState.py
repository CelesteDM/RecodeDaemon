import threading, os, subprocess, pickle

class SharedState:
    def __init__(self, state_dir: str) -> None:
        self.state_dir = state_dir
        self._lock = threading.Lock()
        self._workers = []
        self._threads = []
        self._data = {
            "status": "",
            "active_queue": "",
            "queues": {},
        }

    def update(self, **kwargs) -> None:
        with self._lock:
            self._data.update(kwargs)

    def append_worker(self, worker: subprocess.Popen) -> None:
        with self._lock:
            self._workers.append(worker)

    def remove_worker(self, worker: subprocess.Popen) -> None:
        with self._lock:
            self._workers.remove(worker)

    def workers_len(self) -> int:
        return len(self._workers)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._data)

    def read_history(self) -> dict:
        history_path = os.path.join(self.state_dir, "history")
        if not os.access(history_path, os.F_OK):
            return {}
        history = {}
        len = os.path.getsize(history_path)
        with open(history_path, 'rb') as history_file:
            while history_file.tell() < len:
                queue = pickle.load(history_file)
                history[queue["queue_id"]] = queue
        return history

