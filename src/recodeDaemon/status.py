from .lib import *
from time import sleep
import signal
from shutil import get_terminal_size
from os import system
from json import dumps

TERM_WIDTH = 0
PREV_ANSWER = {}

def update_term_size(sig_num=None, stack_frame=None) -> None:
    global TERM_WIDTH
    width, height = get_terminal_size()
    TERM_WIDTH = width
    print_status()

def format_size(bytes_: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if bytes_ < 1000 or unit == units[-1]:
            return f"{bytes_:.2f}{unit}"
        bytes_ /= 1000

def print_status(message={}) -> None:
    global TERM_WIDTH, PREV_ANSWER
    width = TERM_WIDTH
    message = PREV_ANSWER if not message else message
    system("clear")
    active_queue = "None" if not message["active_queue"] else message["active_queue"]
    var_len = len(message["status"]) + len(str(active_queue))

    # Header
    print("┌" + "─"*(width-2) + "┐")
    print("│" + " "*(width-2) + "│")
    print(f"│ Daemon status: {message["status"]}{" "*(width - var_len - 33)}Active queue: {active_queue} │")
    print("│" + " "*(width-2) + "│")
    print("├" + "─"*(width-2) + "┤")
    
    # Body
    v = ["ID", "NAME", "STATUS", "PROGRESS", "SIZE"]
    spacing = int((width-6)/(len(v)-1))
    diff = width - (spacing * (len(v)-1) + 2 + 4) # 2 are the box characters, and 4 the ID column spacing

    columns = "│" + "{:^4}" + "{:^{s}.{s}}"*(len(v)-1) + " "*diff + "│"

    print(columns.format(*v, s=spacing))
    print("├" + "┄"*(width-2) + "┤")

    # Per queue values
    indx, q_amm = 1, len(message["queues"])
    for queue_id in message["queues"]:
        queue = message["queues"][queue_id]

        if queue["queue_id"] == message["active_queue"] and indx > 1:
            print("├" + "┈"*(width-2) + "┤")

        queue_size = 0
        for item_id in iter(queue["items"]):
            queue_size += queue["items"][item_id]["size"]

        v = [str(queue["queue_id"]), queue["queue_name"], queue["status"].lower(), f"{queue['items_done']}/{queue['item_count']}", format_size(queue_size)]
        print(columns.format(*v, s=spacing))

        # Active queue files
        if queue["queue_id"] == message["active_queue"]:

            for item_id in iter(queue["items"]):
                item = queue["items"][item_id]
                item_progress = round(100 / item["frame_count"] * item["progress"])

                v = ["• ", item["name"], item["status"].lower(), f"{item_progress}%", format_size(item['size'])]

                if len(v[2]) > spacing:
                    v[2] = v[2][:spacing-1] + "…"
                print(columns.format(*v, s=spacing))

            if q_amm > indx:
                print("├" + "┈"*(width-2) + "┤")

        indx += 1

    print("└" + "─"*(width-2) + "┘")

def update_status():
    global PREV_ANSWER
    conn = skt_connect(SKT_PORT)
    if conn:
        answer = skt_communicate(conn, '{"cmd": "status"}')
    else:
        answer = {"status": "NOT RUNNING", "active_queue": "", "queues": {}}
    if answer != PREV_ANSWER:
        PREV_ANSWER = answer
        print_status(answer)

def status_loop(port):
    global SKT_PORT, TERM_WIDTH
    SKT_PORT = port
    try:
        print('\033[?25l', end="")
        signal.signal(signal.SIGWINCH, update_term_size)
        TERM_WIDTH, _ = get_terminal_size()
        while True:
            update_status()
            sleep(1)
    except KeyboardInterrupt:
        print('\033[?25h', end="")

def list_queues(args):
    conn = skt_connect(args["port"])
    if conn:
        answer = skt_communicate(conn, dumps(args))
    else:
        answer = {}

    i = False
    for queue_id in answer["queues"]:
        queue = answer["queues"][queue_id]

        queue_size = 0
        for item_id in iter(queue["items"]):
            queue_size += queue["items"][item_id]["size"]

        if i:
            print("\n\n\n")
        else:
            i = True

        print(f"Queue ID: {queue_id}")
        print(f"Queue name: {queue['queue_name']}")
        print(f"Status: {queue['status']}")
        print(f"Queue size: {format_size(queue_size)}")

        print()
        print(f"Items Done: {queue['items_done']}/{queue['item_count']}")

        for item_num in queue["items"]:
            item = queue["items"][item_num]
            print(f"Name: {item['name']} | Status: {item['status']} | size: {format_size(item['size'])}")
            print(f"Full path: {item['path']}")
            if item["error"]:
                print()
                print(f"Error log: (Exit code: {item['exit_code']})\n{item['error']}")
            print()

        print("Queue config:")
        print(f"Animation: {queue['config']['is_animation']}")
        print(f"Preset: {queue['config']['preset']}")
        print(f"Backup path: {queue['config']['backup_path']}")
        print(f"Ouput path: {queue['config']['output_path']}")
