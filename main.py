#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from tqdm import tqdm
import argparse
from time import sleep

from lib.web_browser import WebBrowser
from util.logger import log
from env import COOKIES, BROWSER_DIR, DOWNLOAD_DIR
from lib.vimeo_downloader import VimeoFetcher


def fetch_init_segments(website_urls: list[str], cookies: list[dict]) -> list:
    log.debug("Initializing web browser")
    browser = WebBrowser(BROWSER_DIR, cookies=cookies, headless=False)
    browser.start()
    browser.new_page()
    log.info("Web browser initialized")

    pages: list[dict] = []

    for url in website_urls:
        videos_of_page = {"name": f"{url.split('/')[-1]}", "urls": []}
        videos_init_segments = []
        log.info(f"Fetching videos of {url}")
        browser.goto(url)
        vimeo_tags = browser.page.query_selector_all(
            "a[href*='vimeo'], iframe[src*='vimeo'], div.playlist-track")
        log.info(f'Found {len(vimeo_tags)} vimeo videos')
        log.info('Clicking on each video to trigger request')
        for vimeo_tag in tqdm(vimeo_tags):
            vimeo_tag.hover()
            vimeo_tag.click()
            browser.load_js(1)
        log.info("Looking network events...")
        start = perf_counter()
        while len(videos_init_segments) != len(vimeo_tags) and perf_counter() - start < 10:
            videos_init_segments = [url for url in browser.network_events_urls if "master.json" in url]
            browser.load_js()
        log.info(f'Found {len(videos_init_segments)} init segments')
        if len(videos_init_segments) == len(vimeo_tags):
            log.success('All init segments have been found')
        else:
            log.warning('Maybe not all init segments have been found')

        videos_of_page["urls"] = videos_init_segments
        pages.append(videos_of_page)
    sleep(60)
    browser.stop()
    save2Json(pages)
    return pages


def save2Json(pages: list[dict]):
    import json
    with open("output.json", "w") as f:
        json.dump(pages, f, indent=4)


def download_videos(page_name: list[str], master_json_urls: list):
    log.info(f"Downloading {len(master_json_urls)} videos... from {page_name}")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(VimeoFetcher(url, f'{page_name}-{i + 1}', DOWNLOAD_DIR).download) for i, url in
                   enumerate(master_json_urls)]
        for future in futures:
            future.result()
        executor.shutdown()


def run(input_list: list[str]):
    pages = fetch_init_segments(input_list, COOKIES)
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
            if urls:
                urls = [urls[i:i + 20] for i in range(0, len(urls), 20)]
                for split_urls in urls:
                    run(split_urls)
        except FileNotFoundError:
            log.error(f'File {args.file} not found')
    elif args.url:
        run([args.url])
    else:
        print("No argument provided")
        print("Use -h or --help for help")
        exit(1)
