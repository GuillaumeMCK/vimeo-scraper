#!/usr/bin/env python3
from http.cookiejar import Cookie
import pprint
from time import perf_counter

from lib.web_browser import web_browser
from util.logger import log
from util.config_file_handler import get_config
from env import COOKIE
import lib.video_fetcher as vf

from time import sleep
from tqdm import tqdm

DL_DIR: str = get_config("dir")
MAX_DL_AT_TIME: int = int(get_config("threads_count"))

def run(input_list: str):
    init_segment_fetcher(input_list)

def init_segment_fetcher(urls):
    # 1. Init web browser
    try:
        log.debug("Initializing web browser")
        browser = web_browser(cookies=COOKIE, headless=True)
        browser.start()
        browser.new_page()
        log.info("Web browser initialized")
    except Exception as e:
        log.error(f'Something went wrong while initializing the browser: {e}')
        exit(1)
    # 2. Loop through the list of urls 
    for url in urls:
        # 2.1. Go to the url
        browser.goto(url)
        # 2.2. scraper tag of vimeo videos
        vimeo_tags = browser.page.query_selector_all("a[href*='vimeo'], iframe[src*='vimeo']")
        log.info(f'Found {len(vimeo_tags)} vimeo videos')
        log.info('Clicking on each video to trigger request')
        for vimeo_tag in tqdm(vimeo_tags):
            vimeo_tag.click()
        log.info("Looking network events...")
        start = perf_counter()
        videos_init_segments = []
        while(len(videos_init_segments) != len(vimeo_tags) and perf_counter() - start < 20):
            videos_init_segments = [url for url in browser.network_events_urls if "master.json" in url]
            browser.load_js()
        log.info(f'Found {len(videos_init_segments)} init segments')
        if (len(videos_init_segments) == len(vimeo_tags)):
            log.success('All init segments have been found')
        else:
            log.warning('Maybe not all init segments have been found')
            log.debug(f'Found {len(videos_init_segments)} init segments but {len(vimeo_tags)} vimeo videos : {videos_init_segments}')
        
    browser.stop()

if __name__ == '__main__':
    urls = ["https://www.gamecodeur.fr/game-guide-aventure/"]
    urls = ["https://www.gamecodeur.fr/liste-ateliers/atelier-tetris-love2d/"]
    # run(urls)
    init_segment_url = "https://153vod-adaptive.akamaized.net/exp=1666831583~acl=%2F97acade8-cf64-4341-8b72-3cdc4857dc08%2F%2A~hmac=c06aaedff67c6530d06647e402749f8fd92f42df8eb14c43ac468a3e96c0d7b6/97acade8-cf64-4341-8b72-3cdc4857dc08/sep/video/57d97d2b,68dd1aab,e438aab0,56d1aa96/master.json?base64_init=1"
    
    
    #  git command to remove one file by name
    # $ git rm