#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tokenize import String
from util.config_file_handler import get_config
from time import sleep

from playwright.sync_api import sync_playwright
from psutil import process_iter
# import logger from util.logger import log
from util.logger import log


class web_browser():

    def __init__(self, cookies = [], headless=True) -> None:
        self.network_events_urls = []
        self.cookies = cookies
        self.headless = headless

    def start(self) -> None:
        try:
            self.playwright_instance = sync_playwright().start()
            self.browser = self.playwright_instance.chromium.launch(
                headless=self.headless,
                executable_path=get_config("chrome_directory"),
                args=['--disable-blink-features=AutomationControlled',  # bypass bot detection
                      '--no-sandbox',
                      '--disable-setuid-sandbox',
                      '--disable-dev-shm-usage',
                      '--disable-accelerated-2d-canvas',
                      '--no-first-run',
                      '--no-zygote',
                      '--disable-gpu'])
            
        except Exception as e:
            log.error(f'Something went wrong while starting the browser: {e}')
            exit(1)

    def new_page(self) -> str:
        try:
            self.context = self.browser.new_context(
                viewport={ 'width': 1280, 'height': 1024 }
            )
            self.page = self.context.new_page()
            self.context.add_cookies(self.cookies)
            self.page.on('request', lambda req: self.network_events_urls.append(req.url))
            self.page.on('response', lambda res: self.network_events_urls.append(res.url))
                
            self.page = self.context.new_page()
            self.page.on("response", lambda response: self.network_events_urls.append(response.url))
        except Exception as e:
            log.error(f'Something went wrong while creating a new page: {e}')

    def goto(self, url: str) -> None:
        try:
            self.network_events_urls = []
            self.page.goto(url, wait_until="domcontentloaded")
        except Exception as e:
            log.error(f'Something went wrong while going to {url}: {e}')

    def load_js(self) -> None:
        try:
            self.page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            log.error(f'Something went wrong while loading JS: {e}')

    def quit_page(self) -> None:
        try:
            self.context.close()
            self.page.close()
        except Exception as e:
            log.error(f'Something went wrong while closing the page: {e}')

    def stop(self) -> None:
        try:
            self.browser.close()
            self.playwright_instance.stop()
        except Exception as e:
            log.error(f'Something went wrong while stopping the browser: {e}')

    def get_scan_screenshot(self) -> None:
        try:
            element_handle = self.page.wait_for_selector("#image")
            return element_handle.screenshot()
        except Exception as e:
            log.error(f'Something went wrong while getting the scan screenshot: {e}')

    def take_scan_screenshot(self, full_path: str) -> None:
        element_handle = self.page.query_selector("#image")
        element_handle.screenshot(path=full_path)

    def get_html(self) -> str:
        return self.page.content()
    
    def click(self, selector: str) -> None:
        self.page.click(selector)
        
    def get_xpath(self, selector: str) -> str:
        return self.page.query_selector(selector).xpath()