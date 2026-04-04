import sys
import os
import pickle
from time import sleep
import threading
from Queue import Queue
from SharedState import SharedState

class Daemon:
    queues: list[Queue] = []
    status = ""

    def __init__(self, shared: SharedState) -> None:
        self.shared = shared
        self.state_dir = shared.state_dir
        self.queues_path = os.path.join(self.state_dir, "queues")
        self.history_path = os.path.join(self.state_dir, "history")

        self.init_state_dir()
        self.load_queues()
        self.set_status("WAITING")

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

    def dump_history(self, queue) -> None:
        with open(self.history_path, 'wb') as history_file:
            pickle.dump(queue.snapshot(), history_file)

    def set_status(self, status: str) -> None:
        self.status = status
        self.shared.update(status=status)

    def dump_queues(self, reason) -> None:
        print(f"Dump requested, reason: {reason}")
        snapshot = {}
        with open(self.queues_path, 'wb') as queue_file:
            for index, item in enumerate(self.queues):
                snapshot[index] = item.snapshot()
                print(f"Dumping: {item.snapshot()}")
                pickle.dump(item, queue_file)
        self.shared.update(queues=snapshot)

    def load_queues(self) -> None:
        if not os.access(self.queues_path, os.F_OK):
            return
        queues = []
        len = os.path.getsize(self.queues_path)
        with open(self.queues_path, 'rb') as state_file:
            while state_file.tell() < len:
                queues.append(pickle.load(state_file))
        if queues:
            self.queues = queues

    def parse_queue(self, queue_file) -> None:
        params = ["","",""]
        with open(queue_file, 'r') as data:
            for _ in range(len(params)):
                line = data.readline()
                if ':' in line:
                    tokens = line.split(':')
                    match tokens[0]:
                        case "path":
                            params[0] = tokens[1].rstrip()
                        case "tune":
                            params[1] = tokens[1].rstrip()
                        case "preset":
                            params[2] = tokens[1].rstrip()

            self.queues.append(Queue(params[0], params[1], params[2]))

        os.remove(queue_file)
        self.dump_queues("New queue added from .queue file")

    def check_next(self) -> None:
        for obj in os.scandir(self.state_dir):
            if obj.name[-6:] == ".queue":
                self.parse_queue(obj.path)

    def run_queues(self) -> None:
        queue_list = self.queues
        for active_queue in queue_list:
            self.shared.update(active_queue=active_queue.snapshot())
            while active_queue.status not in ["SUCCESS", "FAILED"]:
                self.active_worker = threading.Thread(target=active_queue.run_next, daemon=True)
                self.active_worker.start()

                while self.active_worker.is_alive():
                    self.shared.update(active_queue=active_queue.snapshot())
                    self.dump_queues("Update during recoding")
                    sleep(1)

                self.active_worker = None
                self.shared.update(active_queue={})
                self.dump_queues("Update after recoding")

            self.dump_history(active_queue)
            self.queues.remove(active_queue)
            self.dump_queues("Update after finishing all queues")

    def run(self) -> None:
        while True:
            match self.status:
                case "WAITING":
                    self.check_next()

                    if self.queues:
                        self.set_status("RECODING")
                    else:
                        sleep(3)

                case "RECODING":
                    self.dump_queues("Update before recoding")
                    self.run_queues()

                    if not self.queues:
                        self.set_status("WAITING")
