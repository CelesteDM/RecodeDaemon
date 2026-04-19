import socket
import json
import os.path

class cli():

    def __init__(self, args):
        self.args = args
        self.send_command()

    def run(self):
        pass

    def send_command(self):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(os.path.expandvars("$XDG_STATE_HOME/recoder/recode.sock"))

        request = json.dumps(self.args)
        client.sendall(request.encode())

        response = client.recv(4096)
        answer = json.loads(response.decode())
        for key in answer:
            print(f"{key}: {answer[key]}")

        client.close()
