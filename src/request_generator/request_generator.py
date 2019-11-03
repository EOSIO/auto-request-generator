import threading
from multiprocessing import Process, Queue, Lock
import time
from datetime import datetime
import queue

# This class will create the specified number of requests per second for the
# specified duration provided that we don't run out of available threads. That
# will happen if the workers take too long or there are too many of them per
# batch for the system to handle.

class RequestGenerator():
    def __init__(self, rps, duration, function, arg_dict, name='0', audit_file=None):
        self.rps = rps
        self.duration = duration
        self.function = function
        self.arg_dict = arg_dict
        self.name = name
        self.audit_file = audit_file

    def run(self, output_file=None):
        result_queue = Queue()
        thread_driver = WorkerThreadDriver(self.name, self.rps, self.duration, result_queue, self.function, self.arg_dict, audit_file=self.audit_file)
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

        if self.audit_file:
            thread_driver.audit(output_file=self.audit_file)

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

class AuditRecord():
    def __init__(self, worker_num, timestamp, duration):
        self.worker_num = worker_num
        self.timestamp = timestamp
        self.duration = duration

    def __str__(self):
        time_in_ms = int(self.duration*1000)
        return f'[{self.worker_num}] {str(self.timestamp)} ({time_in_ms}ms)\n'


class WorkerThreadDriver(threading.Thread):
    def __init__(self, driver_id, workers, duration, result_queue, function, arg_dict, audit_file=None):
        threading.Thread.__init__(self)
        self.driver_id = driver_id
        self.workers = workers
        self.duration = duration
        self.result_queue = result_queue
        self.worker_processes = []
        self.worker_num = -1
        self.stopped = threading.Event()
        self.function = function
        self.arg_dict = arg_dict
        self.lock = Lock()
        self.audit_file = audit_file
        if self.audit_file:
            self.audit_queue = Queue()

    def start_batch(self):
        timestamp = datetime.now()
        start = time.perf_counter()
        try:
            for i in range(self.workers):
                with self.lock:
                    ts = datetime.now()
                    p_start = time.perf_counter()
                    self.worker_num += 1
                    w = Worker(self.driver_id, self.worker_num, self.result_queue, self.function, self.arg_dict)
                    p = Process(target=w.run, args=())
                    p.start()
                    self.worker_processes.append(p)
                    p_end = time.perf_counter()
                    if self.audit_file:
                        self.audit_queue.put(AuditRecord(self.worker_num, ts, p_end-p_start))
        except RuntimeError:
            print(f'Unable to create enough worker threads! (threading.active_count:{threading.active_count()})')
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

    def audit(self, output_file='audit.log'):
        workers = []
        while (True):
            try:
                workers.append(str(self.audit_queue.get(True, 1)))
            except queue.Empty:
                break

        w = open(output_file,'w')
        w.writelines(workers)
        w.close()


class Worker():
    def __init__(self, driver_id, thread_id, result_queue, function, arg_dict):
        self.result_queue = result_queue
        self.function = function
        self.arg_dict = arg_dict
        self.arg_dict['driver_id'] = driver_id
        self.arg_dict['thread_id'] = thread_id

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
        return Result(f'id:{args["driver_id"]}_{args["thread_id"]}', 200, 0)

    rps = 2
    duration = 2
    args= {'sleeptime': 1.5}
    reqgen = RequestGenerator(rps, duration, mock, args)
    num_requests = reqgen.run()
    print(f'num_requests: {num_requests}')


