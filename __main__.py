from ArgsParser import parse_args
from cli import cli
from SharedState import SharedState
from Recoder import Recoder
from daemon import DaemonContext

def main() -> None:
    args = parse_args()

    if args["cmd"] == "daemon" and args["action"] == "run":
        shared = SharedState(args["state"])
        with DaemonContext():
            Recoder(shared).run()
    else:
        cli(args)

if __name__ == "__main__":
    main()
