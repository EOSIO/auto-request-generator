import requests
import time
import datetime
import os
import uuid

from request_generator import request_generator
from request_generator import request_builder

class PublicApiGetCategories:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        ready = self.config.get('endpoint').replace('/graphql', '/ready')
        self.logger.debug(ready)
        while True:
            try:
                self.logger.info('Trying Public GraphQL API...')
                r = requests.get(ready, timeout=5)
                if r.status_code == 200:
                    self.logger.info('Got 200 from ready endpoint')
                    break
            except Exception:
                self.logger.error('Public API isnt ready yet')
                time.sleep(1)

        endpoint = self.config.get('endpoint')
        self.data = {
          "operationName":"Categories",
          "variables":{},
          "query":"query Categories {\n  categories {\n    category_id\n    name\n    __typename\n  }\n}\n"
        }
        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.req = request_builder.RequestBuilder(
                endpoint,
                params={},
                data=self.data,
                cookiejarfile=None,
                auth=None,
                method='POST',
                user_agent='reqgen',
                auth_type='basic',
                headers={
                  'Content-Type': 'application/json'
                },
                files=[], # this will get filled by the workers
                insecure=False,
                nokeepalive=False,
                http2=False
            )
        self.args = {
            'req': self.req,
            'query': self.data
        }

    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, public_api_get_categories, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')

def public_api_get_categories(args):

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
        files=None,
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify
    )
    resp.raise_for_status()
    elapsed = time.perf_counter() - start

    return request_generator.Result(req.url, resp.status_code, len(resp.content), timestamp=timestamp, elapsed_time=elapsed)
