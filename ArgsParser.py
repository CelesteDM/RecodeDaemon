import argparse
from re import sub
import sys

parser = argparse.ArgumentParser(
            # prog="Recoder",
            # usage=None,
            description="Daemon and cli tool to recode series for streaming services",
            # epilog=None,
            add_help=True,
            allow_abbrev=True,
            exit_on_error=True)

subparsers = parser.add_subparsers()


#---------------------------------------------------------------------------------

# Daemon subcommand
daemon_parser = subparsers.add_parser("daemon", description="Run the recoder daemon.", help="daemon help")
daemon_parser.add_argument("--state", default="$XDG_STATE_HOME/recoder", help="Set the daemon state directory. Expands environment variables")
daemon_parser.add_argument("--socket", default="/tmp/recoder.sock", help="Set the daemon socket path.")

#---------------------------------------------------------------------------------

# Status subcommand
status_parser = subparsers.add_parser("status", description="Get the daemon and queues status.", help="status help")

#---------------------------------------------------------------------------------

# Queue subcommand
queue_parser = subparsers.add_parser("queue", description="Queue management.", help="queue managing help")
queue_subparsers = queue_parser.add_subparsers()

# Queue create subcommand
queue_create_parser = queue_subparsers.add_parser("create", description="Create recoding queues.", help="queue creation help")
queue_create_parser.add_argument("path", action="extend", nargs="+", type=str, help="Path or paths to the file or directory to be recoded")
queue_create_parser.add_argument("-r", "--recursive", action="store_true", help="Use recursive search on the specified directories paths")
queue_create_parser.add_argument("-a", "--animation", action="store_true", help="Tunes the H265 encoder for better results on animation cartoons")
queue_create_parser.add_argument("-p", "--preset", choices=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"], default="medium", help="H264 encoder preset speed, slower options provide better compression. If you are looking for small file size, use the slowest preset that you have patience for")

# Queue list subcommand
queue_list_parser = queue_subparsers.add_parser("list", description="Show information on existing and completed queues.", help="queue listing help")
queue_list_parser.add_argument("-q", "--quiet", action="store_true", help="Print only queue information, ommitting its files")
queue_list_parser.add_argument("-a", "--all", action="store_true", help="Print both loaded queues and completed queues")
queue_list_parser.add_argument("-c", "--completed", action="store_true", help="Print only the history of completed queues")
queue_list_parser.add_argument("-s", "--stats", action="store_true", help="Print stats about file size and recode time")

#---------------------------------------------------------------------------------

parser.parse_args(sys.argv[1:])
