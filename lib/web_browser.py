#!/usr/bin/python3
# -*- coding: utf-8 -*-
from time import perf_counter

from util.logger import log
from playwright.sync_api import sync_playwright


class WebBrowser:

    def __init__(self, browser_dir: str, cookies=None, headless=True) -> None:
        if cookies is None:
            cookies = []
        self.browser_dir: str = browser_dir
        self.headless: bool = headless
        self.cookies: list[dict] = cookies
        self.network_events_urls: list[str] = []
        self.pw_instance = None
        self.browser = None
        self.page = None
        self.context = None

    def start(self) -> None:
        try:
            self.pw_instance = sync_playwright().start()
            self.browser = self.pw_instance.chromium.launch(
                headless=self.headless,
                executable_path=self.browser_dir,
                args=['--disable-blink-features=AutomationControlled',  # bypass bot detection
                      '--no-sandbox',
                      '--disable-setuid-sandbox',
                      '--disable-dev-shm-usage',
                      '--disable-accelerated-2d-canvas',
                      '--no-first-run',
                      '--no-zygote',
                      '--disable-gpu'
                      ])
        except Exception as e:
            log.error(f'Something went wrong while starting the browser: {e}')
            exit(1)

    def new_page(self) -> None:
        try:
            self.context = self.browser.new_context(
                viewport={'width': 1280, 'height': 1024}
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

    def load_js(self, time=0.5) -> None:
        start_time = perf_counter()
        while perf_counter() - start_time < time:
            self.page.wait_for_load_state("domcontentloaded")

    def quit_page(self) -> None:
        try:
            self.context.close()
            self.page.close()
        except Exception as e:
            log.error(f'Something went wrong while closing the page: {e}')

    def stop(self) -> None:
        try:
            self.browser.close()
            self.pw_instance.stop()
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
        return self.page.inner_html("html")

    def click(self, selector: str) -> None:
        self.page.click(selector)
