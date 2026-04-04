import os
from RecodeHandler import RecodeHandler

class Queue:

    queue: list[os.DirEntry] = []
    state = "INIT"
    results = {}
    item_count = 0

    def __init__(self, queue_path, queue_tune, queue_preset) -> None:
        self.queue_path = queue_path
        self.queue_tune = queue_tune
        self.queue_preset = queue_preset

        self.populate()
        self.state = "WAITING"

    def populate(self) -> None:
        scan = os.scandir(self.queue_path)
        dirs = []

        for obj in scan:
            if obj.is_dir():
                dirs.append(obj)
            elif obj.name[-4:] in [".mkv", ".mp4"] and obj.name[:7] != "RECODE_":
                self.queue.append(obj)

        while dirs:
            for directory in dirs:
                scan = os.scandir(directory.path)
                for obj in scan:
                    if obj.is_dir():
                        dirs.append(obj)
                    elif obj.name[-4:] in [".mkv", ".mp4"]:
                        self.queue.append(obj)
                dirs.remove(directory)

        self.item_count = len(self.queue)
        self.items_remaining = len(self.queue)


    def set_exit_status(self) -> None:
        lin = len(self.results)
        failed = 0
        for result in self.results:
            if self.results.get(result) == "FAILED":
                failed += 1
        if failed == 0:
            self.state = "SUCCESS"
        elif failed == lin:
            self.state = "FAILED"
        else:
            self.state = "WARNING"

    def run_next(self) -> None:
        self.state = "RECODING"
        recode = RecodeHandler(self.queue[0], self.queue_tune, self.queue_preset)
        recode.run()
        if recode.command_output.returncode == 0:
            self.results[recode] = "SUCCESS"
        else:
            self.results[recode] = "FAILED"
        self.queue.pop(0)
        self.items_remaining -= 1
        self.state = "WAITING"

    def snapshot(self) -> dict:
        return {
            "state": self.state,
            "item_count": self.item_count,
            "items_done": len(self.results),
            "items_remaining": self.items_remaining,
        }


