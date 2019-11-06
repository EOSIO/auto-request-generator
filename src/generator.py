#!/usr/bin/env python3

import json
import logging
import os
import redis
import requests
import subprocess
import sys
import time

from benchmarks.nginx import NginxGet
from benchmarks.cas_post import CASPost
from benchmarks.cas_get import CASGet
from benchmarks.public_api_get_categories import PublicApiGetCategories
from benchmarks.private_api_get_username import PrivateApiGetUsername
from benchmarks.hooyu_get import HooyuGet
from benchmarks.private_signing_post_transaction import PrivateSigningPostTransaction

def setup_logging(logging_level='debug'):
    log_level = logging.INFO if logging_level == 'info' else logging.DEBUG if logging_level == 'debug' else logging.ERROR
    logger = logging.getLogger('generator')
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger

def main():
    name = os.environ.get('NAME')
    redis_ip = os.environ.get('REDIS_IP')
    logger = setup_logging()

    redis_ = None
    retry = 0
    while True:
        try:
            redis_ = redis.Redis(host=redis_ip, port=6379, db=0)
            redis_.set('foo', 'bar')
            break
        except Exception as e:
            logger.error(f'failed to connect to redis: {e}')
            retry += 1
            if retry > 5:
                raise
            time.sleep(retry)

    config = redis_.get(name)
    logger.info('Waiting for config...')
    while not config:
        config = redis_.get(name)
        time.sleep(1)
    logger.info(f'Got config: {config}')
    config = json.loads(config)

    benchmark = config['benchmark']
    if benchmark == 'nginx-get':
        benchmark_obj = NginxGet(logger, config, name)
    elif benchmark == 'cas-post':
        benchmark_obj = CASPost(logger, config, name)
    elif benchmark == 'cas-get':
        benchmark_obj = CASGet(logger, config, name)
    elif benchmark == 'public-api-get-categories':
        benchmark_obj = PublicApiGetCategories(logger, config, name)
    elif benchmark == 'private-api-get-username':
        benchmark_obj = PrivateApiGetUsername(logger, config, name)
    elif benchmark == 'hooyu-get':
        benchmark_obj = HooyuGet(logger, config, name)
    elif benchmark == 'private-signing-post-transaction':
        benchmark_obj = PrivateSigningPostTransaction(logger, config, name)
    else:
        logger.error(f'Benchmark {benchmark} not supported')
        sys.exit(1)

    benchmark_obj.init_test()

    redis_.pubsub()
    redis_.publish('generator.finished.setup', name)

    runtest_pubsub = redis_.pubsub()
    runtest_pubsub.subscribe('generator.start.test')

    while True:
        msg = runtest_pubsub.get_message()
        if msg and msg.get('type') == 'message':
            data = msg.get('data').decode('utf-8')
            logger.info(f'received data {data}')
            break

    benchmark_obj.run_test('output.log')

    redis_.pubsub()
    redis_.publish('generator.finished.test', name)

if __name__ == '__main__':
    main()
