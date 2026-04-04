import socket
import json
import sys

def send_command(cmd):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect("./var/run/recode.sock")

    request = json.dumps({"cmd": cmd})
    client.sendall(request.encode())

    response = client.recv(4096)
    print(json.loads(response.decode()))

    client.close()

if __name__ == "__main__":
    send_command(sys.argv[1])
