from .argsParser import parse_args
from .sharedState import SharedState
from .recoder import Recoder
from .status import status_loop, list_queues
from .lib import *
from daemon import DaemonContext

def main() -> None:
    args = parse_args()

    if args["cmd"] == "daemon" and args["action"] == "run":
        shared = SharedState(normalize_path(args["state"]))
        if args["daemon"]:
            with DaemonContext():
                print("status: done")
                Recoder(shared, args["port"]).run()
        else:
            recoder = Recoder(shared, args["port"])
            try:
                recoder.run()
            except KeyboardInterrupt:
                recoder.terminate()
                exit(0)

    elif args["cmd"] == "status":
        if args["raw"]:
            conn = skt_connect(args["port"])
            if not conn:
                print("Socket not responding, is the daemon running?")
                exit(2)
            message = json.dumps(args)
            answer = skt_communicate(conn, message)
            print(answer)
            exit(0)

        else:
            status_loop(args["port"])
            exit(0)

    elif args["cmd"] == "queue" and args["action"] == "list":
            list_queues(args)
            exit(0)

    else:
        # Normalize paths
        # Needs to be done here to ensure relative paths are handled correctly
        if args["cmd"] == "queue" and args["action"] == "create":
            args["backup_path"] = normalize_path(args["backup_path"])
            args["output_path"] = normalize_path(args["output_path"])
            args["path"] = [normalize_path(p) for p in args["path"]]

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
