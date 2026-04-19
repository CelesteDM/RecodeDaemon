import sys
import os
import pickle
from time import sleep
import threading
import socket
import json
from struct import pack
from string import ascii_lowercase
from Queue import Queue
from random import choice
from SharedState import SharedState

class Recoder:
    queues: dict[str, Queue] = {}
    status = ""

    def __init__(self, shared: SharedState) -> None:
        self.shared = shared
        self.state_dir = shared.state_dir
        self.queues_path = os.path.join(self.state_dir, "queues")
        self.history_path = os.path.join(self.state_dir, "history")
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_path = os.path.join(self.state_dir, "recode.sock")

        self.init_state_dir()
        self.load_queues()
        
        # Socket init
        self.socket.listen()
        threading.Thread(
            target=self.skt_listen,
            daemon=True
        ).start()

        self.set_status("IDLE")

    def init_state_dir(self) -> None:
        if not os.access(self.state_dir, os.F_OK):
            try:
                os.makedirs(self.state_dir)
            except PermissionError:
                sys.stderr.write(f"Could not create state direnctory. PermissionError\nos.makedirs({self.state_dir}): Permission Denied.\n")
                exit(1)

        elif not os.access(self.state_dir, os.R_OK) or not os.access(self.state_dir, os.W_OK):
            sys.stderr.write(f"Could not open state directory. PermissionError\n{self.state_dir}: Permission Denied.\n")
            exit(1)

        # Socket bind
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        self.socket.bind(self.socket_path)

    def terminate(self) -> None:
        self.set_status("STOPPING")

    def skt_listen(self) -> None:
        while self.status != "STOPPING":
            conn, _ = self.socket.accept()
            threading.Thread(
                target=self.skt_handle_request,
                args=[conn],
                daemon=True
            ).start()

        self.socket.close()

    def skt_handle_request(self, conn) -> None:
        try:
            data = conn.recv(4096)
            if not data:
                return

            request = json.loads(data.decode())
            match request["cmd"]:

                case "status":
                    response = self.shared.snapshot()

                case "daemon":
                    match request["action"]:
                        case "stop":
                            self.terminate()
                            response = {"status": "done"}

                        case _:
                            response = {"error": "unknown command"}

                case "queue":
                    match request["action"]:
                        case "create":
                            queue_id = self.create_queue(
                                request["path"],
                                request["preset"],
                                request["animation"],
                                request["recursive"])
                            response = {"status": "done", "queue_id": queue_id}

                        case "list":
                            response = self.list_queues(
                                request["completed"],
                                request["all"])

                        case "delete":
                            response = {"error": "not implemented"}

                        case "pause":
                            response = {"error": "not implemented"}

                        case "resume":
                            response = {"error": "not implemented"}

                        case _:
                            response = {"error": "unknown command"}

                case _:
                    response = {"error": "unknown command"}

        except Exception as e:
            response = {"error": str(e)}
        finally:
            data = json.dumps(response).encode()
            conn.sendall(pack('>I', len(data)))
            conn.sendall(data)
            conn.close()

    def list_queues(self, completed: bool, all: bool):
        queues = self.shared.snapshot()["queues"]
        waiting = {}

        history = self.shared.read_history()
        for queue_id in self.queues:
            if queues[queue_id].status in ["COMPLETED", "FAILED"]:
                history[queue_id] = queues[queue_id]
            else:
                waiting[queue_id] = queues[queue_id]

        if not all:
            if completed:
                return history
            else:
                return waiting
        else:
            return waiting | history


    def create_queue(self, path: list, preset: str, animation: bool, recursive: bool) -> str:
        queue_id = ''.join(choice(ascii_lowercase) for _ in range(6))
        while queue_id in self.queues:
            queue_id = ''.join(choice(ascii_lowercase) for _ in range(6))

        new_queue = Queue(self.shared, queue_id, path, preset, animation, recursive)
        new_queue.populate()
        self.queues[queue_id] = new_queue

        return queue_id

    def dump_history(self, queue) -> None:
        with open(self.history_path, 'wb') as history_file:
            pickle.dump(queue.snapshot(), history_file)

    def set_status(self, status: str) -> None:
        self.status = status
        self.shared.update(status=status)

    def dump_queues(self) -> None:
        snapshot = {}
        with open(self.queues_path, 'wb') as queue_file:
            for item in self.queues:
                snapshot[item] = self.queues[item].snapshot()
                pickle.dump(snapshot[item], queue_file)
        self.shared.update(queues=snapshot)

    def load_queues(self) -> None:
        if not os.access(self.queues_path, os.F_OK):
            return
        queues = {}
        len = os.path.getsize(self.queues_path)
        with open(self.queues_path, 'rb') as state_file:
            while state_file.tell() < len:
                snapshot = pickle.load(state_file)
                new_queue = Queue(self.shared)
                new_queue.restore(snapshot)
                queues[new_queue.queue_id] = new_queue
        if queues:
            self.queues = queues

    def run_queues(self) -> None:

        active_queue = ""
        for queue_id in self.queues:
            if self.queues[queue_id] not in ["SUCCESS", "FAILED", "WARNING"]:
                active_queue = self.queues[queue_id]
                break

        if active_queue:
            while active_queue.status not in ["SUCCESS", "FAILED", "WARNING"]:
                self.active_worker = threading.Thread(target=active_queue.run_next, daemon=False)
                self.active_worker.start()
                self.set_status("RECODING")
                self.shared.update(active_queue=active_queue.queue_id)

                current_snapshot, last_snapshot = {}, {}
                while self.active_worker.is_alive():
                    current_snapshot = active_queue.snapshot()
                    if last_snapshot:
                        if last_snapshot != current_snapshot:            
                            self.dump_queues()

                    last_snapshot = current_snapshot
                    sleep(3)

                self.active_worker = None
                self.shared.update(active_queue="")
                self.set_status("WAITING")
                self.dump_queues()

            self.dump_history(active_queue)
            self.queues.pop(active_queue.queue_id)
            self.dump_queues()

    def run(self) -> None:
        while True:
            match self.status:
                case "IDLE":
                    if self.queues:
                        self.set_status("WAITING")
                    else:
                        sleep(3)

                case "WAITING":
                    if not self.queues:
                        self.set_status("IDLE")

                    self.dump_queues()
                    self.run_queues()

                case "STOPPING":
                    while len(threading.enumerate()) != 1 and self.shared.workers_len() != 0:
                        sleep(1)
                    else:
                        exit(0)
