import http.cookiejar
import requests
import time
import os

from request_generator import request_generator
from request_generator import request_builder

class Frontend:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        status = f'{self.config.get('endpoint')}/status'
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
        self.req = request_builder.RequestBuilder(
                self.config['endpoint'],
                method='GET',
                user_agent='reqgen',
            )
        self.args = {
            'req': self.req,
            'adapter': self.adapter,
        }


    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, self.threads, frontend_get_posts, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')


def frontend_get_posts(args):
    req = args['req']
    sess = requests.session()
    sess.mount('http://', args['adapter'])
    resp = sess.request(
        req.method,
        req.url,
        params=req.params,
        data=req.data,
        headers=req.headers,
        files=req.files,
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify,
        timeout=30
    )
    return request_generator.Result(req.url, resp.status_code, len(resp.content))
