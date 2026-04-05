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
                print("Restoring queue with this snapshot:")
                print(snapshot)
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
        self.dump_queues("New queue added from .queue file")

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
                self.shared.append_thread(self.active_worker)
                self.active_worker.start()
                self.set_status("RECODING")

                while self.active_worker.is_alive():
                    self.shared.update(active_queue=active_queue.snapshot())
                    self.dump_queues("Update during recoding")
                    sleep(1)

                self.shared.remove_thread(self.active_worker)
                self.active_worker = None
                self.shared.update(active_queue={})
                self.set_status("WAITING")
                self.dump_queues("Update after recoding")

            self.dump_history(active_queue)
            self.queues.remove(active_queue)
            self.dump_queues("Update after finishing all queues")

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
                    self.dump_queues("Update before recoding")
                    self.run_queues()

                    if not self.queues:
                        self.set_status("IDLE")

                case "STOPPING":
                    pass

                    # TO-DO:
                    # Stop worker on Queue class and set to interrumped
                    # Stop the SocketHandler
                    # Wait for all the treads/workers to stop (check the ammount of them on SharedState)
                    # |-> Only one thread will stay, the daemon one.
                    # On the start script, only create one thread for the Daemon with darmon=True and exit


    # GENERAL TO-DO:
    # Move the SocketHandler to the Daemon class
    # Implement https://peps.python.org/pep-3143/
    # Finish the ArgsParser and cli interface
