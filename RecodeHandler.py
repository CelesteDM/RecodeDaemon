import subprocess
import os

class RecodeHandler():

    def __init__(self, entry: os.DirEntry, tunning: str, preset: str):

        self.entry = entry
        self.audio = self.get_channels(self.entry.path, "audio")
        self.subs = self.get_channels(self.entry.path, "subtitles")
        self.preset = preset
        self.tunning = tunning
        self.output = os.path.join(os.path.dirname(self.entry.path), f"RECODE_{self.entry.name}")

    def get_channels(self, file: str, channel: str) -> dict:

        # Returns a dictionary of {stream_index: channel_lang} or a {0: -int} in case of error
        # The value channel_lang could be empty in case it doesnt exists

        if channel not in ["audio", "subtitles"]:
            return {0: -1}
        else:
            channel = channel[0]

        pairs = {}
        output = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=index:stream_tags=language", "-select_streams", channel, "-of", "csv=p=0", file], capture_output=True, shell=False, text=True)

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

    def run(self):

        cmd_root = ["ffmpeg", "-nostdin", "-y", "-i", self.entry.path, "-map", "0:v"]
        cmd_audio_mapping, cmd_subtitles_mapping = ["-map", "0:a"], ["-map", "0:s"]
        cmd_video_settings = ["-c:v", "libx265", "-preset", self.preset, "-tune", self.tunning]
        cmd_audio_settings = ["-c:a", "aac", "-b:a", "192k", "-ac", "2"]
        cmd_tail = ["-disposition:s:0", "default", "-disposition:s:1", "0", "-c:s", "copy", "-c:t", "copy" ]

        if self.audio.get(0) != -1:
            cmd_audio_mapping = []
            for stream in self.audio:
                match self.audio.get(stream):
                    case "jpn":
                        cmd_audio_mapping += ["-map", "0:a:m:language:jpn:?"]
                    case "eng":
                        cmd_audio_mapping += ["-map", "0:a:m:language:eng:?"]
                    case "spa":
                        cmd_audio_mapping += ["-map", "0:a:m:language:spa:?"]

        if self.subs.get(0) != -1:
            cmd_subtitles_mapping = []
            for stream in self.subs:
                match self.subs.get(stream):
                    case "spa":
                        cmd_subtitles_mapping += ["-map", "0:s:m:language:spa:?"]
                    case "eng":
                        cmd_subtitles_mapping += ["-map", "0:s:m:language:eng:?"]
                    case "jpn":
                        cmd_subtitles_mapping += ["-map", "0:s:m:language:jpn:?"]

        command = cmd_root + cmd_audio_mapping + cmd_subtitles_mapping + cmd_video_settings + cmd_audio_settings + cmd_tail + [self.output]
        self.command_output = subprocess.run(command, capture_output=True, shell=False, text=True)
