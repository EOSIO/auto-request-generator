import http.cookiejar
import requests
import time
import os
import datetime
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from request_generator import request_generator
from request_generator import request_builder

class Frontend:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        status = f'{self.config.get("endpoint")}/status'
        self.logger.debug(status)
        while True:
            try:
                self.logger.info('Trying b1-frontend...')
                r = requests.get(status, timeout=5)
                if r.status_code == 200:
                    self.logger.info('Got 200 from status endpoint')
                    break
            except Exception:
                self.logger.error('b1-frontend isnt ready yet')
                time.sleep(1)

        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.threads = int(self.config['threads'])
        self.adapter = requests.adapters.HTTPAdapter(pool_connections=self.threads, pool_maxsize=self.threads*10)

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--no-sandbox")
        chromeOptions.add_argument("--disable-setuid-sandbox")
        chromeOptions.add_argument("--remote-debugging-port=9222")
        chromeOptions.add_argument("--disable-dev-shm-using")
        chromeOptions.add_argument("--disable-extensions")
        chromeOptions.add_argument("--disable-gpu")
        chromeOptions.add_argument("--headless")
        self.browser = webdriver.Chrome(options=chromeOptions)

        self.args = {
            'browser': self.browser,
            'url': self.config['endpoint'],
        }


    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, self.threads, frontend_get_posts, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')


def frontend_get_posts(args):
    browser = args['browser']

    start = time.perf_counter()
    timestamp = datetime.datetime.now()
    browser.get(args['url'])
    elapsed = time.perf_counter() - start
    time.sleep(3)

    soup = BeautifulSoup(browser.page_source,'html.parser')
    results = soup.findAll('div', {'class': re.compile('^post-feed-entry')})
    if len(results) > 1:
        status_code = 200
        error = None
    else:
        status_code = 400
        error = 'No posts found'

    return request_generator.Result(args['url'], status_code, len(browser.page_source), timestamp=timestamp, elapsed_time=elapsed, e=error)
