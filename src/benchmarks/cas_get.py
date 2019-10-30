import http.cookiejar
import os
import requests
import time

class CASGet:
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

    def init_test(self):
        ready = self.config.get('endpoint').replace('files', 'ready')
        self.logger.debug(ready)
        while True:
            try:
                self.logger.info('Trying CAS...')
                r = requests.get(ready, timeout=5)
                if r.status_code == 200:
                    self.logger.info('Got 200 from ready endpoint')
                    break
            except Exception:
                self.logger.error('CAS isnt ready yet')
                time.sleep(1)

        endpoint = self.config.get('endpoint')
        image_hash = self.upload_file(endpoint)
        self.logger.debug(image_hash)

        popen_args = [
            'mobbage',
            '-V', '-j',
            '-t', str(self.config['duration']),
            '-d', str(self.config['batch_delay']),
            '-c', f'/assets/cookies-{self.config["cluster"]}.txt',
            os.path.join(endpoint, image_hash),
        ]
        self.test_command = popen_args

    def upload_file(self, endpoint):
        cj = http.cookiejar.MozillaCookieJar('/assets/cookies.txt')
        cj.load()
        files = {'filename': open('/assets/test.jpg', 'rb')}
        r = requests.post(endpoint, files=files, cookies=cj)

        return r.text
