import sys
import os
import pickle
from time import sleep
import threading
import socket
import json
from Queue import Queue
from SharedState import SharedState

class Daemon:
    queues: list[Queue] = []
    requests: list[dict] = []
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

                case "new_queue":
                    # response = self.create_queue(request)
                    response = {"error": "not implemented"}

                case "history":
                    response = self.shared.read_history()

                case _:
                    response = {"error": "unknown command"}

            conn.sendall((json.dumps(response) + "\n").encode())

        except Exception as e:
            conn.sendall(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def dump_history(self, queue) -> None:
        with open(self.history_path, 'wb') as history_file:
            pickle.dump(queue.snapshot(), history_file)

    def set_status(self, status: str) -> None:
        self.status = status
        self.shared.update(status=status)

    def dump_queues(self) -> None:
        snapshot = {}
        with open(self.queues_path, 'wb') as queue_file:
            for index, item in enumerate(self.queues):
                snapshot[index] = item.snapshot()
                pickle.dump(snapshot[index], queue_file)
        self.shared.update(queues=snapshot)

    def load_queues(self) -> None:
        if not os.access(self.queues_path, os.F_OK):
            return
        queues = []
        len = os.path.getsize(self.queues_path)
        with open(self.queues_path, 'rb') as state_file:
            while state_file.tell() < len:
                snapshot = pickle.load(state_file)
                new_queue = Queue(self.shared)
                new_queue.restore(snapshot)
                queues.append(new_queue)
        if queues:
            self.queues = queues

    def parse_queue(self, queue_file) -> None:
        params = ["","",bool]
        with open(queue_file, 'r') as data:
            for _ in range(len(params)):
                line = data.readline()
                if ':' in line:
                    tokens = line.split(':')
                    match tokens[0]:
                        case "path":
                            params[0] = tokens[1].rstrip()
                        case "preset":
                            params[1] = tokens[1].rstrip()
                        case "is_animation":
                            if tokens[1].rstrip() == "True":
                                params[2] = bool(1)
                            else: 
                                params[2] = bool(0)

            new_queue = Queue(self.shared, queue_path=params[0], queue_preset=params[1], is_animation=params[2])
            new_queue.populate()
            self.queues.append(new_queue)

        os.remove(queue_file)
        self.dump_queues()

    def check_next(self) -> None:
        for obj in os.scandir(self.state_dir):
            if obj.name[-6:] == ".queue":
                self.parse_queue(obj.path)

    def run_queues(self) -> None:
        queue_list = self.queues
        for active_queue in queue_list:
            self.shared.update(active_queue=active_queue.snapshot())
            while active_queue.status not in ["SUCCESS", "FAILED", "WARNING"]:
                self.active_worker = threading.Thread(target=active_queue.run_next, daemon=False)
                self.active_worker.start()
                self.set_status("RECODING")

                while self.active_worker.is_alive():
                    self.shared.update(active_queue=active_queue.snapshot())
                    self.dump_queues()
                    sleep(1)

                self.active_worker = None
                self.shared.update(active_queue={})
                self.set_status("WAITING")
                self.dump_queues()

            self.dump_history(active_queue)
            self.queues.remove(active_queue)
            self.dump_queues()

    def run(self) -> None:
        while True:
            match self.status:
                case "IDLE":
                    self.check_next()

                    if self.queues:
                        self.set_status("WAITING")
                    else:
                        sleep(3)

                case "WAITING":
                    self.dump_queues()
                    self.run_queues()

                    if not self.queues:
                        self.set_status("IDLE")

                case "STOPPING":
                    while len(threading.enumerate()) != 1 and self.shared.workers_len() != 0:
                        sleep(1)
                    else:
                        exit(0)
