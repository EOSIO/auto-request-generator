import requests
import time
import datetime
import os
import uuid
import random

from request_generator import request_generator
from request_generator import request_builder

class PrivateSigningPostTransaction:
    def __init__(self, logger, config, name):
        self.logger = logger
        self.config = config
        self.name = name

    def init_test(self):
        ready = self.config.get('endpoint').replace('/blockchain/transact', '/ready')
        self.logger.debug(ready)
        while True:
            try:
                self.logger.info('Trying Private Signing Service API...')
                r = requests.get(ready, timeout=5)
                if r.status_code == 200:
                    self.logger.info('Got 200 from ready endpoint')
                    break
            except Exception:
                self.logger.error('Private Signing API isnt ready yet')
                time.sleep(1)

        endpoint = self.config.get('endpoint')
        jwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImludGVybmFsX3NlcnZpY2UiLCJzZXJ2aWNlTmFtZSI6ImIxLWFwaS1ncmFwaHFsLXByaXZhdGUtaWRlbnRpdHkiLCJpYXQiOjE1MTYyMzkwMjJ9.C8SqnTnkTaa6wSGFC1mWX_DCTG41rO_ifRu4MnU_Pls'
        self.data = {}
        self.rps = int(self.config['rps'])
        self.duration = int(self.config['duration'])
        self.threads = int(self.config['threads'])
        self.adapter = requests.adapters.HTTPAdapter(pool_connections=self.threads, pool_maxsize=self.threads*10)
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
                  'Content-Type': 'application/json',
                  'Authorization': f'Bearer {jwt}'
                },
                files=[], # this will get filled by the workers
                insecure=False,
                nokeepalive=False,
                http2=False
            )
        self.args = {
            'req': self.req,
            'query': self.data,
            'adapter': self.adapter,
        }

    def run_test(self, output_file):
        self.logger.debug('starting test')
        reqgen = request_generator.RequestGenerator(self.rps, self.duration, self.threads, private_signing_post_transaction, self.args, name=self.name)
        num_requests = reqgen.run(output_file=output_file)
        self.logger.debug('finished test')
        self.logger.info(f'Sent {num_requests} requests')

def private_signing_post_transaction(args):
    json_data = {
      "transaction": {
        "actions": [
          {
            "account": "signup.b1",
            "name": "cnfrmphone",
            "authorization": [
              {
                "actor": "signup.b1",
                "permission": "active",
              }
            ],
            "data": {
              "reference": random.randint(0,1000000),
            }
          }
        ]
      }
    }
    start = time.perf_counter()
    timestamp = datetime.datetime.now()
    req = args['req']
    sess = requests.session()
    sess.mount('http://', args['adapter'])
    resp = sess.request(
        req.method,
        req.url,
        params=req.params,
        json=json_data,
        headers=req.headers,
        files=None,
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify,
        timeout=5
    )
    resp.raise_for_status()
    elapsed = time.perf_counter() - start

    return request_generator.Result(req.url, resp.status_code, len(resp.content), timestamp=timestamp, elapsed_time=elapsed)
