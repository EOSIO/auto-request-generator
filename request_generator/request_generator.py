import threading
import time
import queue
import datetime

# This class will create the specified number of requests per second for the
# specified duration provided that we don't run out of available threads. That
# will happen if the workers take too long or there are too many of them per
# batch for the system to handle.

class RequestGenerator():
    def __init__(self, rps, duration, function, arg_dict):
        self.rps = rps
        self.duration = duration
        self.function = function
        self.arg_dict = arg_dict

    def run(self, output_file='output.log'):
        result_queue = queue.Queue()
        thread_driver = WorkerThreadDriver(0, self.rps, self.duration, result_queue, self.function, self.arg_dict)
        thread_driver.start()
        thread_driver.join()

        num_requests = 0
        while (True):
            try:
                result = result_queue.get(True, 1)
                num_requests += 1
                print(result)

            except queue.Empty:
                break

        return num_requests

class Result():
    def __init__(self, url, ret_code, ret_size, timestamp=datetime.datetime.now(), elapsed_time=0, e=None):
        self.timestamp = timestamp
        self.url = url
        self.code = ret_code
        self.time = elapsed_time
        self.size = ret_size
        self.error = e

    def __str__(self):
        time_in_ms = int(self.time*1000)
        if self.error is not None:
            return f'Timestamp: {str(self.timestamp)}, Code: {self.code}, Size: {self.size}, Time: {time_in_ms}ms, URL: {self.url}, Error: {self.error}'
        else:
            return f'Timestamp: {str(self.timestamp)}, Code: {self.code}, Size: {self.size}, Time: {time_in_ms}ms, URL: {self.url}'

class WorkerThreadDriver(threading.Thread):
    def __init__(self, driver_id, workers, duration, result_queue, function, arg_dict):
        threading.Thread.__init__(self)
        self.driver_id = driver_id
        self.workers = workers
        self.duration = duration
        self.result_queue = result_queue
        self.threads = []
        self.thread_counter = 0
        self.stopped = threading.Event()
        self.function = function
        self.arg_dict = arg_dict

    def start_batch(self):
        try:
            for i in range(self.workers):
                    thread = WorkerThread(self.driver_id, self.thread_counter, self.result_queue, self.function, self.arg_dict)
                    thread.start()
                    self.threads.append(thread)
                    self.thread_counter += 1
        except RuntimeError:
            print(f'Unable to create enough worker threads! (threading.active_count:{threading.active_count()})')

    def stop_test(self):
        self.stopped.set()
        for thread in self.threads:
            thread.join()

    def run(self):

        test_timer = threading.Timer(self.duration+1, self.stop_test)
        test_timer.start()

        while not self.stopped.wait(1.0):
            batch_thread = threading.Thread(target=self.start_batch, args=())
            batch_thread.start()


class WorkerThread(threading.Thread):
    def __init__(self, driver_id, thread_id, result_queue, function, arg_dict):
        threading.Thread.__init__(self)
        self.driver_id = driver_id
        self.thread_id = thread_id
        self.result_queue = result_queue
        self.function = function
        self.arg_dict = arg_dict

    def run(self):
        start = time.perf_counter()
        try:
            result = self.function(self.driver_id, self.thread_id, self.arg_dict)
            elapsed = time.perf_counter() - start
            result.time = elapsed
            self.result_queue.put(result)
        except Exception as e:
            elapsed = time.perf_counter() - start
            self.result_queue.put(Result(f'id:{self.driver_id}_{self.thread_id}', 400, 0, e=e))

if __name__ == "__main__":

    # Demonstrate how to use these classes

    def mock(driver_id, thread_id, args):
        print(args)
        time.sleep(args['sleeptime'])
        return Result(f'id:{driver_id}_{thread_id}', 200, 0)

    rps = 1
    duration = 1
    args= {'sleeptime': 1.5}
    reqgen = RequestGenerator(rps, duration, mock, args)
    num_requests = reqgen.run()
    print(f'num_requests: {num_requests}')


