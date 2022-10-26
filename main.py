#!/usr/bin/env python3
from http.cookiejar import Cookie
import pprint
from time import perf_counter

from lib.web_browser import web_browser
from util.logger import log
from util.config_file_handler import get_config
from env import COOKIE

from time import sleep
from tqdm import tqdm

DL_DIR: str = get_config("dir")
MAX_DL_AT_TIME: int = int(get_config("threads_count"))

def run(input_list: str):
    init_segment_fetcher(input_list)

def init_segment_fetcher(urls):
    # 1. Init web browser
    try:
        browser = web_browser(cookies=COOKIE, headless=True)
        browser.start()
        browser.new_page()
    except Exception as e:
        log.error(f'Something went wrong while initializing the browser: {e}')
        exit(1)
    # 2. Loop through the list of urls 
    for url in urls:
        # 2.1. Go to the url
        browser.goto(url)
        # 2.2. scraper tag of vimeo videos
        vimeo_tags = browser.page.query_selector_all("iframe[src*='vimeo']")
        log.info(f'Found {len(vimeo_tags)} vimeo videos')
        log.info('Hovering video to get the init segment url')
        # 2.3. Loop through the vimeo tags and click on them
        for vimeo_tag in tqdm(vimeo_tags):
            vimeo_tag.hover()
        # Get the url of the video init segment in the network events
        videos_init_segments = [url for url in browser.network_events_urls if "master.json" in url]
        log.info(f'Found {len(videos_init_segments)} init segments')
        if (len(videos_init_segments) == len(vimeo_tags)):
            log.success('All init segments have been found')
        else:
            log.warning('Some init segments are missing')
            pprint.pprint(videos_init_segments)
        
    browser.stop()

if __name__ == '__main__':
    urls = ["https://www.gamecodeur.fr/game-guide-aventure/"]
    run(urls)
    
    #  git command to remove one file by name
    # $ git rm