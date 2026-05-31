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

def print_status(message={}) -> None:
    global TERM_WIDTH, PREV_ANSWER
    width = TERM_WIDTH
    message = PREV_ANSWER if not message else message
    system("clear")
    active_queue = "None" if not message["active_queue"] else message["active_queue"]
    var_len = len(message["status"]) + len(active_queue)

    # Header
    print("┌" + "─"*(width-2) + "┐")
    print("│" + " "*(width-2) + "│")
    print(f"│ Daemon status: {message["status"]}{" "*(width - var_len - 33)}Active queue: {active_queue} │")
    print("│" + " "*(width-2) + "│")
    print("├" + "─"*(width-2) + "┤")
    
    # Body
    spacing = int((width-2)/5)
    diff = width - ((spacing*5)+2)
    columns = "│" + "{:^{spacing}}"*5 + " "*diff + "│"

    v = ["ID", "STATUS", "ITEMS", "REMAINING", "FINISHED"]
    print(columns.format(v[0], v[1], v[2], v[3], v[4], spacing=spacing))
    print("├" + "┄"*(width-2) + "┤")

    # Per queue values
    for queue_id in message["queues"]:
        queue = message["queues"][queue_id]
        v = [queue["queue_id"], queue["status"].lower(), queue["item_count"], queue["items_remaining"], queue["items_done"]]
        print(columns.format(v[0], v[1], v[2], v[3], v[4], spacing=spacing))

        # Active queue files
        if queue["queue_id"] == message["active_queue"]:

            line = "│" + "{:^{spacing}}"*5 + " "*diff + "│"

            for item_id in iter(queue["items"]):
                item = queue["items"][item_id]

                char = "└" if int(item_id) == len(queue["items"]) else "├"
                print(line.format(char, item["status"].lower(), item["name"], f"Size: {item["size"]//(1024**2)}M", "", spacing=spacing))

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
    width, _ = get_terminal_size()

    conn = skt_connect(args["port"])
    if conn:
        answer = skt_communicate(conn, dumps(args))
    else:
        answer = {}

    i = False
    for queue_id in answer["queues"]:
        queue = answer["queues"][queue_id]

        if i:
            print("\n\n\n")
        else:
            i = True

        print(f"Queue ID: {queue_id}")
        print(f"Status: {queue['status']}")

        print()
        print(f"Items Done: {queue['items_done']}/{queue['item_count']}")

        for item_num in queue["items"]:
            item = queue["items"][item_num]
            print(f"Name: {item['name']} | Status: {item['status']} | size: {item['size']//(1024**2)}M")
            print(f"Full path: {item['path']}")
            print()

        print("Queue config:")
        print(f"Animation: {queue['config']['is_animation']}")
        print(f"Preset: {queue['config']['preset']}")
        print(f"Backup path: {queue['config']['backup_path']}")


