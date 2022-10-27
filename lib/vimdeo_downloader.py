#!/usr/bin/env python
# Downloads the video and audio streams from the master json url and recombines
# it into a single file
from __future__ import print_function
import requests
import base64
from tqdm import tqdm
import subprocess as sp
import os
import distutils.core
from urllib.parse import urljoin

from util.logger import log

class VimdeoFetcher:
    
    def __init__(self, master_json_url: str, filename: str):
        self.BASE_DIR = os.path.dirname(os.path.realpath(__file__))
        self.OUTPUT_DIR = os.path.join(self.BASE_DIR, "../output")
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

    def _fetch_data(self, url):
        resp = requests.get(url)
        if resp.status_code != 200:
            log.error('HTTP error (' + str(resp.status_code) + '): ' + resp.content)
            return None, None
        content = resp.json()
        base_url = os.path.dirname(url)
        return base_url, content

    def download(self):
        if(self.content is None or self.base_url is None):
            log.warning("The content or the base url is None... Aborting")
            return
        
        if self._download_video(self.base_url, self.content['video']):
            if self._download_audio(self.base_url, self.content['audio']):
                self._merge_audio_video()

    def _download_video(self, base_url, content):
        """Downloads the video portion of the content into the self.INSTANCE_TMP folder"""
        result = True
        heights = [(i, d['height']) for (i, d) in enumerate(content)]
        idx, _ = max(heights, key=lambda t: t[1])
        video = content[idx]
        video_base_url = urljoin(base_url, video['base_url'])

        filename = f"{self.INSTANCE_TMP}-tmp.mp4"

        video_file = open(filename, 'wb')

        init_segment = base64.b64decode(video['init_segment'])
        video_file.write(init_segment)

        for segment in tqdm(video['segments'], colour="green", desc=f"video"):
            segment_url = urljoin(video_base_url, segment['url'])
            resp = requests.get(segment_url)
            if resp.status_code != 200:
                log.error('HTTP error (' + str(resp.status_code) + '): ' + resp.content)
                result = False
            video_file.write(resp.content)
            segment_url = video_base_url + segment['url']
            resp = requests.get(segment_url, stream=True)
            if resp.status_code != 200:
                log.failure(f'Failed to download video segment {resp.status_code}')
                print(segment_url)
                result = False
                break
            for chunk in resp:
                video_file.write(chunk)

        video_file.flush()
        video_file.close()
        return result


    def _download_audio(self, base_url, content):
        """Downloads the video portion of the content into the self.INSTANCE_TMP folder"""
        result = True
        audio = content[0]
        audio_base_url = urljoin(base_url, audio['base_url'])

        filename = f"{self.INSTANCE_TMP}-tmp.mp3"
        audio_file = open(filename, 'wb')

        init_segment = base64.b64decode(audio['init_segment'])
        audio_file.write(init_segment)

        for segment in tqdm(audio['segments'], colour="blue", desc=f"audio"):
            segment_url = audio_base_url + segment['url']
            resp = requests.get(segment_url, stream=True)
            if resp.status_code != 200:
                log.failure(f'Failed to download audio segment {resp.status_code}')
                print(segment_url)
                result = False
                break
            for chunk in resp:
                audio_file.write(chunk)

        audio_file.flush()
        audio_file.close()
        return result

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
