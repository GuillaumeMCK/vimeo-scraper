#!/usr/bin/env python
import requests
import base64
from tqdm import tqdm
import subprocess as sp
import os
import distutils.core
from urllib.parse import urljoin
from glob import glob

from util.logger import log


class VimeoFetcher:

    def __init__(self, master_json_url: str, filename: str, output_dir=None):
        self.BASE_DIR = os.path.dirname(os.path.realpath(__file__))
        self.OUTPUT_DIR = output_dir if output_dir is not None else os.path.join(self.BASE_DIR, "../output")
        self.TMP_DIR = os.path.join(self.BASE_DIR, "../tmp")
        self.INSTANCE_TMP = os.path.join(self.TMP_DIR, filename)
        self.OS_WIN = True if os.name == "nt" else False

        self._init_dir()
        self._chk_ffmpeg()

        self.filename = filename
        self.base_url, self.content = self._fetch_data(master_json_url)

    def _init_dir(self):
        for path in (self.TMP_DIR, self.OUTPUT_DIR):
            if not os.path.exists(path):
                log.debug(f"Creating {path}...")
                os.makedirs(path)

    def _chk_ffmpeg(self):
        if self.OS_WIN:
            self.FFMPEG_BIN = 'ffmpeg.exe'
        else:
            try:
                self.FFMPEG_BIN = distutils.spawn.find_executable("ffmpeg")
            except AttributeError:
                self.FFMPEG_BIN = 'ffmpeg'

    def _fetch_data(url):
        resp = requests.get(url)
        if resp.status_code != 200:
            log.error('HTTP error (' + str(resp.status_code) + '): ' + resp.text)
            return None, None
        content = resp.json()
        base_url = os.path.dirname(url)
        return base_url, content

    def checkIfFileNameExist(self, filename: str):
        return glob(f"{self.OUTPUT_DIR}/{filename}*") != []

    def download(self):
        """Downloads the video and audio files and merges them into a single file"""
        if self.checkIfFileNameExist(self.filename):
            log.warning(f"File {self.filename} already exists, skipping...")
            return

        if self.content is None or self.base_url is None:
            log.warning("The content or the base url is None... Aborting")
            return

        if self._download_video(self.base_url, self.content['video']):
            if self._download_audio(self.base_url, self.content['audio']):
                self._merge_audio_video()
            else:
                log.error("Failed to download audio")
        else:
            log.error("Failed to download video")

    def _download_video(self, base_url, content):
        """Downloads the video portion of the content into the self.INSTANCE_TMP folder"""
        heights = [(i, d['height']) for (i, d) in enumerate(content)]
        idx, _ = max(heights, key=lambda t: t[1])
        video = content[idx]
        video_base_url = urljoin(base_url, video['base_url'])

        filename = f"{self.INSTANCE_TMP}-tmp.mp4"
        init_segment = base64.b64decode(video['init_segment'])
        return self._download_segments(filename, init_segment, video['segments'], video_base_url, colour="green",
                                       desc=f"video : {video_base_url[:50]}...")

    def _download_audio(self, base_url, content):
        """Downloads the video portion of the content into the self.INSTANCE_TMP folder"""
        audio = content[0]
        audio_base_url = urljoin(base_url, audio['base_url'])
        filename = f"{self.INSTANCE_TMP}-tmp.mp3"
        init_segment = base64.b64decode(audio['init_segment'])
        return self._download_segments(filename, init_segment, audio['segments'], audio_base_url, colour="blue",
                                       desc=f"audio : {audio_base_url[:50]}...")


    def _download_segments(filename: str, init_segment: bytes, segments: list, base_url: str, colour="green",
                           desc=""):
        """Downloads the segments into the given file"""
        with open(filename, 'wb') as f:
            f.write(init_segment)
            for segment in tqdm(segments, colour=colour, desc=desc):
                segment_url = base_url + segment['url']
                resp = requests.get(segment_url, stream=True)
                if resp.status_code != 200:
                    log.failure(f'Failed to download segment {resp.status_code} {segment_url}')
                    print(segment_url)
                    return False
                for chunk in resp:
                    f.write(chunk)
        return True

    def _merge_audio_video(self):
        """Merges the audio and video files into a single file"""
        audio_filename = os.path.join(self.TMP_DIR, f'{self.filename}-tmp.mp3')
        video_filename = os.path.join(self.TMP_DIR, f'{self.filename}-tmp.mp4')
        video_output_filename = os.path.join(self.OUTPUT_DIR, f'{self.filename}.mp4')
        command = [self.FFMPEG_BIN,
                   '-i', audio_filename,
                   '-i', video_filename,
                   '-acodec', 'copy',
                   '-vcodec', 'copy',
                   video_output_filename,
                   '-y',
                   '-loglevel', 'error']

        if self.OS_WIN:
            sp.call(command, shell=True)
        else:
            sp.call(command)

        os.remove(audio_filename)
        os.remove(video_filename)
