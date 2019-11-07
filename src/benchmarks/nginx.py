import http.cookiejar
import requests
import time
import os

from request_generator import request_generator
from request_generator import request_builder

class NginxGet:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.threads = int(self.config['threads'])
        self.req = request_builder.RequestBuilder(
                self.config['endpoint'],
                method='GET',
                user_agent='reqgen',
            )
        self.args = {
            'req': self.req,
        }


    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, self.threads, nginx_get, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')


def nginx_get(args):
    req = args['req']
    sess = requests.session()
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
