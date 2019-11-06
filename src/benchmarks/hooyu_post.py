import requests
import time
import datetime
import os
import uuid

from request_generator import request_generator
from request_generator import request_builder

class HooyuPost:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        ready = self.config.get('endpoint').replace('files', 'ready')
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
        self.req = request_builder.RequestBuilder(
                endpoint,
                params={},
                data=None,
                auth=None,
                method='POST',
                user_agent='reqgen',
                auth_type='basic',
                headers={},
                insecure=False,
                nokeepalive=False,
                http2=False
            )
        self.args = {
            'req': self.req
        }

    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, hooyu_post, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')

def hooyu_post(args):


    start = time.perf_counter()
    timestamp = datetime.datetime.now()

    address = {
            'address1': "address1",
            'address2': "address2",
            'city': "someCity",
            'postcode': "1234",
            'country': "US"
    }

    kyc ={
        'kyc_confirmed': True,
        'kyc_status': "completed",
        'full_name': "User Full Name",
        'country': "us",
        'date_of_birth': "01/01/01",
        'address': address
    }


    req = args['req']
    sess = requests.session()
    resp = sess.request(
        req.method,
        req.url,
        params=req.params,
        data=kyc,
        headers=req.headers,
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify
    )
    resp.raise_for_status()
    elapsed = time.perf_counter() - start


    return request_generator.Result(req.url, resp.status_code, len(resp.content), timestamp=timestamp, elapsed_time=elapsed)
