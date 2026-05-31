import socket
import json
from struct import unpack, pack

def skt_connect(port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect(("127.0.0.1", port))
    except ConnectionRefusedError:
        return None
    return conn

def skt_communicate(conn, message) -> dict:
    data = message.encode()
    conn.sendall(pack('>I', len(data)))
    conn.sendall(data)
    conn.shutdown(socket.SHUT_WR)

    response_size = unpack('>I', conn.recv(4))[0]
    response = b""
    reamining_payload_size = response_size
    while reamining_payload_size > 0:
        response += conn.recv(reamining_payload_size)
        reamining_payload_size = response_size - len(response)

    conn.close()
    return json.loads(response.decode())
