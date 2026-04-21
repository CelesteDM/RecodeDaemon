import socket
import json
import os.path
import pickle
from struct import unpack

class cli():

    def __init__(self, args):
        self.args = args
        self.send_command()

    def send_command(self) -> int:
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            conn.connect(os.path.expandvars("$XDG_STATE_HOME/recoder/recode.sock"))
        except ConnectionRefusedError:
            print("Socket not responding, is the daemon running?")
            exit(2)

        request = json.dumps(self.args)
        conn.sendall(request.encode())

        response_size = unpack('>I', conn.recv(4))[0]
        response = b""
        reamining_payload_size = response_size
        while reamining_payload_size > 0:
            response += conn.recv(reamining_payload_size)
            reamining_payload_size = response_size - len(response)
        answer = json.loads(response.decode())
        for key in answer:
            print(f"{key}: {answer[key]}")

        conn.close()
        if answer["status"] == "error":
            exit(1)
        else:
            exit(0)
