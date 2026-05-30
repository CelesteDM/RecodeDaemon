import argparse

def parse_args() -> dict:
    parser = argparse.ArgumentParser(
                # prog="Recoder",
                # usage=None,
                description="Daemon and cli tool to recode series for streaming services",
                # epilog=None,
                add_help=True,
                allow_abbrev=True,
                exit_on_error=True)
    parser.add_argument("-p", "--port", default="5300", type=int, help="Set the daemon socket port [default=5300]")

    subparsers = parser.add_subparsers(required=True)


    #---------------------------------------------------------------------------------

    # Daemon subcommand
    daemon_parser = subparsers.add_parser("daemon", description="Daemon management.", help="daemon help")
    daemon_parser.set_defaults(cmd="daemon")
    daemon_subparsers = daemon_parser.add_subparsers(required=True)

    # Daemon run subcommand
    daemon_run_parser = daemon_subparsers.add_parser("run", description="Run the recoder daemon.", help="daemon run help")
    daemon_run_parser.set_defaults(action="run")
    daemon_run_parser.add_argument("--state", default="$XDG_STATE_HOME/recoder", help="Set the daemon state directory. Expands environment variables")
    daemon_run_parser.add_argument("-d", "--daemon", action="store_true", help="Run the daemon as a background process")

    # Daemon stop subcommand
    daemon_stop_parser = daemon_subparsers.add_parser("stop", description="Stop the recoder daemon.", help="daemon stop help")
    daemon_stop_parser.set_defaults(action="stop")

    #---------------------------------------------------------------------------------

    # Status subcommand
    status_parser = subparsers.add_parser("status", description="Get the daemon and queues status.", help="status help")
    status_parser.set_defaults(cmd="status")

    #---------------------------------------------------------------------------------

    # Queue subcommand
    queue_parser = subparsers.add_parser("queue", description="Queue management.", help="queue managing help")
    queue_parser.set_defaults(cmd="queue")
    queue_subparsers = queue_parser.add_subparsers(required=True)

    # Queue create subcommand
    queue_create_parser = queue_subparsers.add_parser("create", description="Create recoding queues.", help="queue creation help")
    queue_create_parser.set_defaults(action="create")
    queue_create_parser.add_argument("path", action="extend", nargs="+", type=str, help="Path or paths to the file or directory to be recoded")
    queue_create_parser.add_argument("-r", "--recursive", action="store_true", help="Use recursive search on the specified directories paths")
    queue_create_parser.add_argument("-b", "--backup-path", default="", help="Directory path where backup of files will be stored, if left empty or unspecified the files will be overwritten without backup")
    queue_create_parser.add_argument("-a", "--animation", action="store_true", help="Tunes the H265 encoder for better results on animation cartoons")
    queue_create_parser.add_argument("-p", "--preset", choices=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"], default="medium", help="H264 encoder preset speed, slower options provide better compression. If you are looking for small file size, use the slowest preset that you have patience for")

    # Queue list subcommand
    queue_list_parser = queue_subparsers.add_parser("list", description="Show information on existing and completed queues.", help="queue listing help")
    queue_list_parser.set_defaults(action="list")
    queue_list_parser.add_argument("-q", "--quiet", action="store_true", help="Print only queue information, ommitting its files")
    queue_list_parser.add_argument("-a", "--all", action="store_true", help="Print both loaded queues and completed queues")
    queue_list_parser.add_argument("-c", "--completed", action="store_true", help="Print only the history of completed queues")
    queue_list_parser.add_argument("-s", "--stats", action="store_true", help="Print stats about file size and recode time")

    # Queue delete subcommand
    queue_delete_parser = queue_subparsers.add_parser("delete", description="Delete existing queues.", help="queue deleting help")
    queue_delete_parser.set_defaults(action="delete")
    queue_delete_parser.add_argument("-i", "--queue-id", action="extend", nargs="+", type=str, help="List of queue ids to be deleted")

    # Queue pause subcommand
    queue_pause_parser = queue_subparsers.add_parser("pause", description="Pause the active queue.")
    queue_pause_parser.set_defaults(action="pause")

    # Queue resume subcommand
    queue_resume_parser = queue_subparsers.add_parser("resume", description="Resume the active queue.")
    queue_resume_parser.set_defaults(action="resume")

    #---------------------------------------------------------------------------------

    return vars(parser.parse_args())
