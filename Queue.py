import os
from json import dump
from RecodeHandler import RecodeHandler

class Queue:

    status = "INIT"
    queue = {}

    def __init__(self, queue_path, queue_tune, queue_preset) -> None:
        self.queue_path = queue_path
        self.queue_tune = queue_tune
        self.queue_preset = queue_preset

        self.next_item = 1
        self.items_done = 0

        self.populate()
        self.status = "WAITING"

    def populate(self) -> None:
        scan = os.scandir(self.queue_path)
        dirs = []
        files = []

        for obj in scan:
            if obj.is_dir():
                dirs.append(obj)
            elif obj.name[-4:] in [".mkv", ".mp4"] and obj.name[:7] != "RECODE_":
                files.append(obj)

        while dirs:
            for directory in dirs:
                scan = os.scandir(directory.path)
                for obj in scan:
                    if obj.is_dir():
                        dirs.append(obj)
                    elif obj.name[-4:] in [".mkv", ".mp4"] and obj.name[:7] != "RECODE_":
                        files.append(obj)
                dirs.remove(directory)

        for index, file in enumerate(files):
            self.queue[index+1] = {
                "status": "WAITING",
                "path": file.path,
                "name": file.name,
                "size": file.stat().st_size,
                    }
        self.item_count = len(self.queue)


    def set_exit_status(self) -> None:
        failed = 0
        for item in self.queue:
            if self.queue[item]["status"] == "FAILED":
                failed += 1
        if failed == 0:
            self.status = "SUCCESS"
        elif failed == self.item_count:
            self.status = "FAILED"
        else:
            self.status = "WARNING"

    def run_next(self) -> None:
        current_item = self.queue[self.next_item]
        output_path = os.path.join(os.path.dirname(current_item["path"]), f"RECODE_{current_item['name']}")
        self.status = "RECODING"
        current_item["status"] = "RECODING"


        recode = RecodeHandler(current_item, self.queue_tune, self.queue_preset)
        recode.run()

        if recode.command_output.returncode == 0:
            os.replace(output_path, current_item["path"])
            current_item["status"] = "SUCCESS"
        else:
            os.remove(output_path)
            current_item["status"] = "FAILED"
            current_item["error"] = recode.command_output.stderr
            current_item["exit_code"] = recode.command_output.returncode

        self.items_done += 1

        if self.items_done == self.item_count:
            self.set_exit_status()
        else:
            self.next_item += 1
            self.status = "WAITING"

    def snapshot(self) -> dict:
        return {
            "status": self.status,
            "item_count": self.item_count,
            "items_done": self.items_done,
            "items_remaining": self.item_count - self.items_done,
            "items": self.queue,
        }


