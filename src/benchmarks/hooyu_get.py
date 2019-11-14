
import requests
import time
import datetime
import os
import uuid
import json

from request_generator import request_generator
from request_generator import request_builder

class HooyuGet:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        ready = self.config.get('endpoint').replace('status', 'ready')
        self.logger.debug(ready)
        while True:
            try:
                self.logger.info('Trying Hooyu...')
                r = requests.get(ready, timeout=5)
                if r.status_code == 200:
                    self.logger.info('Got 200 from ready endpoint')
                    break
            except Exception:
                self.logger.error('Hooyu isnt ready yet')
                time.sleep(1)

        endpoint = self.config.get('endpoint')
        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.threads = int(self.config['threads'])
        self.adapter = requests.adapters.HTTPAdapter(pool_connections=self.threads, pool_maxsize=self.threads*10)
        self.req = request_builder.RequestBuilder(
                endpoint,
                cookiejarfile=f'/assets/cookies-{self.config["cluster"]}.txt',
                method='GET',
                user_agent='reqgen',
                auth_type='basic',
            )
        self.args = {
            'req': self.req,
            'adapter': self.adapter,
        }

    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, self.threads, hooyu_get, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')

def hooyu_get(args):
    req = args['req']
    sess = requests.session()
    sess.mount('http://', args['adapter'])
    resp = sess.request(
        req.method,
        req.url,
        params=req.params,
        json=req.data,
        headers=req.headers,
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify
    )
    return request_generator.Result(req.url, resp.status_code, len(resp.content))
