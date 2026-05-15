import os
import subprocess
import signal
from time import sleep
from shutil import copy
from SharedState import SharedState

class Queue:

    status = "INIT"
    queue = {}

    # Queues need to be able to be initiated without values so they can be later restored using the restore() function
    def __init__(self, shared: SharedState, queue_id="", queue_path=[], queue_preset="", is_animation=False, recursive=False, backup_path="") -> None:
        self.shared = shared

        self.queue_id = queue_id
        self.queue_path = queue_path
        self.queue_preset = queue_preset
        self.is_animation = is_animation
        self.recursive = recursive
        self.backup_path = backup_path

        self.next_item = 1
        self.items_done = 0

    def populate(self) -> None:
        for path in self.queue_path:
            scan = os.scandir(path)
            dirs = []
            files = []

            for obj in scan:
                if obj.is_dir() and obj not in dirs:
                    dirs.append(obj)
                elif obj.name[-4:] in [".mkv", ".mp4"] and obj.name[:7] != "RECODE_" and obj not in files:
                    files.append(obj)

            if self.recursive:
                while dirs:
                    scan = os.scandir(dirs[0].path)
                    for obj in scan:
                        if obj.is_dir() and obj not in dirs:
                            dirs.append(obj)
                        elif obj.name[-4:] in [".mkv", ".mp4"] and obj.name[:7] != "RECODE_" and obj not in files:
                            files.append(obj)
                    dirs.remove(dirs[0])

            for index, file in enumerate(files):
                self.queue[index+1] = {
                    "status": "WAITING",
                    "path": file.path,
                    "name": file.name,
                    "size": file.stat().st_size,
                        }
            self.item_count = len(self.queue)
            self.status = "WAITING"

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

    def get_channels(self, file_path: str, channel: str) -> dict:

        # Returns a dictionary of {stream_index: channel_lang} or a {0: -int} in case of error
        # The value channel_lang could be empty in case it doesnt exists

        if channel not in ["audio", "subtitles"]:
            return {0: -1}
        else:
            channel = channel[0]

        pairs = {}
        output = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=index:stream_tags=language", "-select_streams", channel, "-of", "csv=p=0", file_path], capture_output=True, shell=False, text=True)

        if output.returncode != 0:
            return {0: -1}

        if not output.stdout:
            return {0: -1}

        for line in output.stdout.split():
            if "," in line:
                values = line.split(",")
                pairs[values[0]] = values[1]
            else:
                pairs[line] = ""

        return pairs

    def get_process(self, file_path: str, output_path: str) -> subprocess.Popen:

        cmd_root = ["ffmpeg", "-v", "error", "-stats", "-nostdin", "-y", "-i", file_path, "-map", "0:v"]
        cmd_audio_mapping, cmd_subtitles_mapping = ["-map", "0:a"], ["-map", "0:s"]
        cmd_video_settings = ["-c:v", "libx265", "-preset", self.queue_preset, "-x265-params", "log-level=none"]
        cmd_audio_settings = ["-c:a", "aac", "-b:a", "192k", "-ac", "2"]
        cmd_tail = ["-disposition:s:0", "default", "-disposition:s:1", "0", "-c:s", "copy", "-c:t", "copy"]

        if self.is_animation:
            cmd_video_settings += ["-tune", "animation" ]

        audio_channels = self.get_channels(file_path, "audio")
        subtitles_channels = self.get_channels(file_path, "subtitles")

        if audio_channels.get(0) != -1:
            lang_audio_mapping = []
            for stream in audio_channels:
                match audio_channels.get(stream):
                    case "jpn":
                        lang_audio_mapping += ["-map", "0:a:m:language:jpn:?"]
                    case "eng":
                        lang_audio_mapping += ["-map", "0:a:m:language:eng:?"]
                    case "spa":
                        lang_audio_mapping += ["-map", "0:a:m:language:spa:?"]
            if lang_audio_mapping:
                cmd_audio_mapping = lang_audio_mapping

        if subtitles_channels.get(0) != -1:
            lang_subtitles_mapping = []
            for stream in subtitles_channels:
                match subtitles_channels.get(stream):
                    case "spa":
                        lang_subtitles_mapping += ["-map", "0:s:m:language:spa:?"]
                    case "eng":
                        lang_subtitles_mapping += ["-map", "0:s:m:language:eng:?"]
                    case "jpn":
                        lang_subtitles_mapping += ["-map", "0:s:m:language:jpn:?"]
            if lang_subtitles_mapping:
                cmd_subtitles_mapping = lang_subtitles_mapping

        command = cmd_root + cmd_audio_mapping + cmd_subtitles_mapping + cmd_video_settings + cmd_audio_settings + cmd_tail + [output_path]
        return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, shell=False, text=True)

    def run_next(self) -> None:
        current_item = None
        for index in self.queue:
            if self.queue[index]["status"] not in ["SUCCESS", "FAILED"]:
                current_item = self.queue[index]
                break
        if not current_item:
            self.set_exit_status()
        else:

            if self.backup_path:
                backup_path = os.path.join(self.backup_path, current_item['name'])
                if not os.path.exists(backup_path):
                    copy(current_item['path'], backup_path)

            output_path = os.path.join(os.path.dirname(current_item["path"]), f"RECODE_{current_item['name']}")
            proc = self.get_process(current_item["path"], output_path)
            self.shared.append_worker(proc)

            while proc.poll() is None:
                match self.shared.snapshot()["status"]:
                    case "RECODING":
                        if self.status != "RECODING":
                            self.status = "RECODING"
                            proc.send_signal(signal.SIGCONT)
                            current_item["status"] = "RECODING"
                        else:
                            try:
                                proc.communicate(1)
                            except subprocess.TimeoutExpired:
                                continue

                    case "PAUSED":
                        if self.status != "PAUSED":
                            current_item["status"] = "PAUSED"
                            self.status = "PAUSED"
                            proc.send_signal(signal.SIGSTOP)
                        sleep(1)

                    case "WAITING":
                        if self.status != "WAITING":
                            current_item["status"] = "WAITING"
                            self.status = "WAITING"
                        sleep(1)

                    case _:
                        proc.terminate()
                        current_item["status"] = "INTERRUPTED"

            self.shared.remove_worker(proc)

            # Steps after recoding depending on item status:
            if proc.returncode == 0:
                os.replace(output_path, current_item["path"])
                current_item["status"] = "SUCCESS"
                self.items_done += 1

            elif current_item["status"] != "INTERRUPTED":
                os.remove(output_path)
                current_item["status"] = "FAILED"
                current_item["error"] = proc.communicate()[1]
                current_item["exit_code"] = proc.returncode
                self.items_done += 1

            self.status = "WAITING"

    def snapshot(self) -> dict:
        return {
            "queue_id": self.queue_id,
            "status": self.status,
            "item_count": self.item_count,
            "items_done": self.items_done,
            "items_remaining": self.item_count - self.items_done,
            "items": self.queue,
            "config": {
                "preset": self.queue_preset,
                "is_animation": self.is_animation,
                "backup_path": self.backup_path,
            },
        }

    def restore(self, snapshot: dict):
        self.queue_id = snapshot["queue_id"]
        self.status = snapshot["status"]
        self.item_count = snapshot["item_count"]
        self.items_done = snapshot["items_done"]
        self.queue_preset = snapshot["config"]["preset"]
        self.is_animation = snapshot["config"]["is_animation"]
        self.backup_path = snapshot["config"]["backup_path"]
        for index in snapshot["items"]:
            self.queue[index] = {
                "status": snapshot["items"][index]["status"],
                "path": snapshot["items"][index]["path"],
                "name": snapshot["items"][index]["name"],
                "size": snapshot["items"][index]["size"],
                }
