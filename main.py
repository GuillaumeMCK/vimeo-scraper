#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import Cookie
from time import perf_counter
from tqdm import tqdm
import argparse


from lib.web_browser import WebBowser
from util.logger import log
from env import COOKIE
from lib.vimdeo_downloader import VimdeoFetcher


def fetch_init_segments(website_urls: str, cookie: Cookie) -> list:
    try:
        log.debug("Initializing web browser")
        browser = WebBowser(cookies=COOKIE, headless=True)
        browser.start()
        browser.new_page()
        log.info("Web browser initialized")
    except Exception as e:
        log.error(f'Something went wrong while initializing the browser: {e}')
        exit(1)

    pages = []
    videos_of_page = {"name": "", "urls": []}

    for url in website_urls:
        videos_of_page = {"name": f"{url.split('/')[-1]}", "urls": []}
        browser.goto(url)
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
        
        videos_of_page["urls"] = videos_init_segments
        pages.append(videos_of_page)
        
    browser.stop()
    return pages

def download_videos(page_name:str, master_json_urls: list):
    log.info(f"Downloading {len(master_json_urls)} videos...")
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(VimdeoFetcher(url, f'{page_name}_{i+1}').download) for i,url in enumerate(master_json_urls)]
        for future in futures: future.result()
        executor.shutdown()
    
        
def run(input_list: str):
    pages = fetch_init_segments(input_list, COOKIE)
    for page in pages:
        download_videos(page["name"], page["urls"])
        

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Download videos from a list of urls')
    arg_parser.add_argument('-f', '--file', help='A file containing urls')
    arg_parser.add_argument('-u', '--url', help='A single url')
    args = arg_parser.parse_args()

    if args.file:
        try:
            with open(args.file) as f:
                urls = f.read().splitlines()
            run(urls)
        except FileNotFoundError:
            log.error(f'File {args.file} not found')
    elif args.url:
        run([args.url])
    else:
        print("No argument provided")
        print("Use -h or --help for help")
        exit(1)