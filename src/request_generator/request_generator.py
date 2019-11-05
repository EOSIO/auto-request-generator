import threading
from multiprocessing import Process, Queue, Lock
import time
from datetime import datetime
import queue
import uuid

# This class will create the specified number of requests per second for the
# specified duration provided that we don't run out of available threads. That
# will happen if the workers take too long or there are too many of them per
# batch for the system to handle.

class RequestGenerator():
    def __init__(self, rps, duration, function, arg_dict, name='0'):
        self.rps = rps
        self.duration = duration
        self.function = function
        self.arg_dict = arg_dict
        self.name = name

    def run(self, output_file=None):
        result_queue = Queue()
        thread_driver = WorkerThreadDriver(self.name, self.rps, self.duration, result_queue, self.function, self.arg_dict)
        thread_driver.start()
        thread_driver.join()

        results = []
        while (True):
            try:
                results.append(str(result_queue.get(True, 1)))
            except queue.Empty:
                break

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
            return f'Timestamp: {str(self.timestamp)}, Code: {self.code}, Size: {self.size}, Time: {time_in_ms}ms, URL: {self.url}, Error: {self.error}\n'
        else:
            return f'Timestamp: {str(self.timestamp)}, Code: {self.code}, Size: {self.size}, Time: {time_in_ms}ms, URL: {self.url}\n'


class WorkerThreadDriver(threading.Thread):
    def __init__(self, driver_id, workers, duration, result_queue, function, arg_dict):
        threading.Thread.__init__(self)
        self.workers = workers
        self.duration = duration
        self.result_queue = result_queue
        self.worker_processes = []
        self.stopped = threading.Event()
        self.function = function
        self.arg_dict = arg_dict
        self.lock = Lock()

    def start_batch(self):
        timestamp = datetime.now()
        start = time.perf_counter()
        for i in range(self.workers):
            with self.lock:
                w = Worker(self.result_queue, self.function, self.arg_dict)
                p = Process(target=w.run, args=())
                p.start()
                self.worker_processes.append(p)
        elapsed = time.perf_counter() - start
        print(f'{timestamp},{self.workers},{elapsed}')

    def stop_test(self):
        self.stopped.set()
        for worker in self.worker_processes:
            worker.join()

    def run(self):

        test_timer = threading.Timer(self.duration+1, self.stop_test)
        test_timer.start()

        while not self.stopped.wait(1.0):
            batch_thread = threading.Thread(target=self.start_batch, args=())
            batch_thread.start()


class Worker():
    def __init__(self, result_queue, function, arg_dict):
        self.result_queue = result_queue
        self.function = function
        self.arg_dict = arg_dict

    def run(self):
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


