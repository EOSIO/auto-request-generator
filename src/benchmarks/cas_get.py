import http.cookiejar
import requests
import time
import os

from request_generator import request_generator
from request_generator import request_builder

class CASGet:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

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
        cookiejarfile = f'/assets/cookies-{self.config["cluster"]}.txt'
        if self.name.startswith('generator-1'):
            image_hash = self.upload_file(endpoint, cookiejarfile)
        self.logger.debug(image_hash)

        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.req = request_builder.RequestBuilder(
                os.path.join(endpoint, image_hash),
                params={},
                data=None,
                cookiejarfile=cookiejarfile,
                auth=None,
                method='GET',
                user_agent='reqgen',
                auth_type='basic',
                headers={},
                files=[],
                insecure=False,
                nokeepalive=False,
                http2=False
            )
        self.args = {
            'req': self.req,
        }

    def upload_file(self, endpoint, cookiejarfile):
        cj = http.cookiejar.MozillaCookieJar(cookiejarfile)
        cj.load()
        files = {'filename': open('/assets/test.jpg', 'rb')}
        r = requests.post(endpoint, files=files, cookies=cj)

        return r.text

    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, cas_get, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')


def cas_get(args):

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
        verify=req.verify
    )
    resp.raise_for_status()

    return request_generator.Result(req.url, resp.status_code, len(resp.content))
