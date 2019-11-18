import itertools
import os
import threading
import time
from datetime import datetime, timedelta
import queue
import uuid

# This class will create the specified number of requests per second for the
# specified duration provided that we don't run out of available threads. That
# will happen if the workers take too long or there are too many of them per
# batch for the system to handle.

class RequestGenerator():
    def __init__(self, rps, duration, threads, function, arg_dict, name='0'):
        self.rps = rps
        self.duration = duration
        self.threads = threads
        self.function = function
        self.arg_dict = arg_dict
        self.name = name

    def run(self, output_file=None):
        result_queue = queue.Queue()
        thread_driver = WorkerThreadDriver(self.name, self.rps, self.threads, self.duration, result_queue, self.function, self.arg_dict)
        thread_driver.run()
        print('thread driver completed; collecting results')

        results = []
        while (True):
            try:
                results.append(str(result_queue.get(True, 1)))
            except queue.Empty:
                break

        print('generating output')
        if output_file:
            w = open(output_file,'w')
            w.writelines(results)
            w.close()
        else:
            print(''.join(results))

        return len(results)

class Result():
    def __init__(self, url, ret_code, ret_size, timestamp=None, elapsed_time=0, e=None):
        if timestamp is None:
            self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp
        self.url = url
        self.code = ret_code
        self.time = elapsed_time
        self.size = ret_size
        self.error = e

    def __str__(self):
        time_in_ms = int(self.time*1000)
        if self.error is not None:
            return f'Timestamp: {str(self.timestamp)}, Code: {self.code}, Size: {self.size}, Time: {time_in_ms}ms, URL: {self.url}, Error: {self.error.replace(',', '_')}\n'
        else:
            return f'Timestamp: {str(self.timestamp)}, Code: {self.code}, Size: {self.size}, Time: {time_in_ms}ms, URL: {self.url}\n'


class WorkerThreadDriver(object):
    def __init__(self, driver_id, rps, thread_count, duration, result_queue, function, arg_dict):
        self.rps = rps
        self.thread_count = thread_count
        self.duration = duration
        self.result_queue = result_queue
        self.workers = []
        self.function = function
        self.arg_dict = arg_dict

    def run(self):
        print(f'creating {self.thread_count} workers...')
        for i in range(self.thread_count):
            each_rps = self.rps / self.thread_count
            self.workers.append(Worker(i, self.thread_count, self.result_queue, self.function, self.arg_dict, self.duration, each_rps))

        print('starting workers...')
        for worker in self.workers:
            worker.start()

        print('joining all workers...')
        for worker in self.workers:
            worker.join()

        print('all workers joined')


class Worker(threading.Thread):
    def __init__(self, thread_id, generator_thread_count, result_queue, function, arg_dict, duration, rps):
        threading.Thread.__init__(self)

        print(f'initializing worker {thread_id}')
        self.thread_id = thread_id
        self.result_queue = result_queue
        self.function = function
        self.arg_dict = arg_dict
        self.duration = duration
        self.rps = rps

        generator_index = int(os.environ['INDEX']) - 1
        self.total_thread_count = int(os.environ['GENERATOR_COUNT']) * generator_thread_count
        self.global_thread_id = (generator_index * generator_thread_count) + thread_id

    def sleep_until(self, timestamp):
        diff = (timestamp - datetime.now()).total_seconds()
        if diff > 0:
            time.sleep(diff)

    def run(self):
        print(f'starting run: {self.rps} rps')

        sleep_length = 1 / self.rps
        start_offset = self.global_thread_id * (sleep_length / self.total_thread_count)

        test_start = datetime.now() + timedelta(seconds=start_offset)
        self.sleep_until(test_start)

        for i in itertools.count(1):
            start = time.perf_counter()
            try:
                result = self.function(self.arg_dict)
                elapsed = time.perf_counter() - start
                if result.time == 0:
                    result.time = elapsed
                self.result_queue.put(result)
            except Exception as e:
                elapsed = time.perf_counter() - start
                self.result_queue.put(Result('-', 400, 0, elapsed_time=elapsed, e=e))

            now = datetime.now()
            if (now - test_start).seconds >= self.duration:
                print('exiting worker process')
                break
            else:
                next_request = test_start + timedelta(seconds=(i * sleep_length))
                self.sleep_until(next_request)


if __name__ == "__main__":
    # Demonstrate how to use these classes
    def mock(args):
        print(args)
        time.sleep(args['sleeptime'])
        return Result(f'id:{uuid.uuid4()}', 200, 0)

    rps = 2
    duration = 2
    args= {'sleeptime': 1.5}
    reqgen = RequestGenerator(rps, duration, mock, args)
    num_requests = reqgen.run()
    print(f'num_requests: {num_requests}')


