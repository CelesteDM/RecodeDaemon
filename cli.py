import socket
import json
from struct import unpack, pack

class cli():

    def __init__(self, args):
        self.args = args

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect(("127.0.0.1", self.args["port"]))
        except ConnectionRefusedError:
            print("Socket not responding, is the daemon running?")
            exit(2)

        message = json.dumps(self.args)
        self.socket_send(conn, message)

        answer = self.socket_receive(conn)
        answer = json.loads(answer)
        for key in answer:
            print(f"{key}: {answer[key]}")

        conn.close()
        if answer["status"] == "error":
            exit(1)
        else:
            exit(0)

    def socket_send(self, conn, message) -> None:
        data = message.encode()
        conn.sendall(pack('>I', len(data)))
        conn.sendall(data)
        conn.shutdown(socket.SHUT_WR)

    def socket_receive(self, conn) -> str:
        response_size = unpack('>I', conn.recv(4))[0]
        response = b""
        reamining_payload_size = response_size
        while reamining_payload_size > 0:
            response += conn.recv(reamining_payload_size)
            reamining_payload_size = response_size - len(response)
        return response.decode()
