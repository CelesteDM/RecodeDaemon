from .argsParser import parse_args
from .sharedState import SharedState
from .recoder import Recoder
from .status import status_loop
from .lib import *
from daemon import DaemonContext

def main() -> None:
    args = parse_args()

    if args["cmd"] == "daemon" and args["action"] == "run":
        shared = SharedState(args["state"])
        if args["daemon"]:
            with DaemonContext():
                print("status: done")
                Recoder(shared, args["port"]).run()
        else:
            Recoder(shared, args["port"]).run()

    elif args["cmd"] == "status":
        status_loop(args["port"])
        exit(0)

    else:
        conn = skt_connect(args["port"])
        if not conn:
            print("Socket not responding, is the daemon running?")
            exit(2)
        message = json.dumps(args)

        answer = skt_communicate(conn, message)
        for key in answer:
            print(f"{key}: {answer[key]}")

        if answer["status"] == "error":
            exit(1)
        else:
            exit(0)
