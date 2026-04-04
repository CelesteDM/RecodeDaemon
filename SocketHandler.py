import os
import socket
import threading
import json

class SocketHandler:
    socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def __init__(self, shared) -> None:
        self.shared = shared
        self.state_dir = shared.state_dir

        if os.path.exists("./var/run/recode.sock"):
            os.remove("./var/run/recode.sock")

        self.socket.bind("./var/run/recode.sock")
        self.socket.listen()

    def create_queue(self, request) -> str:
        return "Not implemented"

    def handle_client(self, conn, shared) -> None:
        try:
            data = conn.recv(4096)

            if not data:
                return

            request = json.loads(data.decode())

            match request["cmd"]:
                case "status":
                    response = shared.snapshot()

                case "new_queue":
                    response = self.create_queue(request)

                case _:
                    response = {"error": "unknown command"}

            conn.sendall((json.dumps(response) + "\n").encode())

        except Exception as e:
            conn.sendall(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def run(self) -> None:

        while True:
            conn, _ = self.socket.accept()

            threading.Thread(
                target=self.handle_client,
                args=(conn, self.shared),
                daemon=True
            ).start()

