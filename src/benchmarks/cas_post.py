import requests
import time
from datetime import datetime
import os

from request_generator import request_generator
from request_generator import request_builder

class CASPost:
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

        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.req = request_builder.RequestBuilder(
                endpoint,
                params={},
                data=None,
                cookiejarfile=f'/assets/cookies-{self.config["cluster"]}.txt',
                auth=None,
                method='POST',
                user_agent='reqgen',
                auth_type='basic',
                headers={},
                files=[], # this will get filled by the workers
                insecure=False,
                nokeepalive=False,
                http2=False
            )
        self.args = {
            'req': self.req,
            'payload_size': self.config['payload_size'],
            'file_path': '/assets/'
        }

    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, cas_post, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')

def cas_post(args):

    filename = os.path.join(args['file_path'], f'{args["driver_id"]}_{args["thread_id"]}.jpg')
    with open(filename, 'wb') as new_file:
        new_file.write(os.urandom(args['payload_size']))

    start = time.perf_counter()
    timestamp = datetime.datetime.now()
    req = args['req']
    sess = requests.session()
    resp = sess.request(
        req.method,
        req.url,
        params=req.params,
        data=req.data,
        headers=req.headers,
        files=[('filename', filename)],
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify
    )
    resp.raise_for_status()
    elapsed = time.perf_counter() - start

    os.remove(filename)

    return request_generator.Result(req.url, resp.status_code, len(resp.content), timestamp=timestamp, elapsed_time=elapsed)
