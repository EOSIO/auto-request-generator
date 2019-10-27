import threading
import time
import queue
import datetime

from helpers import DotDict

# This class will create the specified number of requests per second for the
# specified duration provided that we don't run out of available threads. That
# will happen if the work that the worker thread is doing takes too long or
# there are too many workers in each batch for the system to handle.

class WorkerThreadDriver(threading.Thread):
    def __init__(self, driver_id, workers, duration, result_queue):
        threading.Thread.__init__(self)
        self.driver_id = driver_id
        self.workers = workers
        self.duration = duration
        self.result_queue = result_queue
        self.threads = []
        self.thread_counter = 0
        self.stopped = threading.Event()

    def start_batch(self):
        try:
            for i in range(self.workers):
                    thread = WorkerThread(self.driver_id, self.thread_counter, self.result_queue)
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
            print(f'active_threads:{threading.active_count()}')
            batch_thread = threading.Thread(target=self.start_batch, args=())
            batch_thread.start()


class WorkerThread(threading.Thread):
    def __init__(self, driver_id, thread_id, result_queue):
        threading.Thread.__init__(self)
        self.driver_id = driver_id
        self.thread_id = thread_id
        self.result_queue = result_queue

    def run(self):
        try:
            start = time.perf_counter()

            # Now fire off our request!
            # resp = sess.request(
            #     job.method,
            #     job.url,
            #     params=job.params,
            #     data=job.data,
            #     headers=job.headers,
            #     files=upload_files,
            #     auth=auth,
            #     cookies=job.cookiejar,
            #     verify=not job.insecure

            # )
            # resp.raise_for_status()

            time.sleep(0.5)
            elapsed = time.perf_counter() - start

            self.result_queue.put(DotDict({
                'url':  f'id:{self.driver_id}_{self.thread_id}',
                'code': 200,
                'time': elapsed,
                'size': 0
            }))

        # Catch any errors here, be they client-side errors (i.e.
        # a mal-formed url passed to the requests module) or server
        # side errors
        except Exception as e:
            # try:
            #     err_code = resp.status_code
            # except:
            #     err_code = 400
            err_code = 400

            elapsed = time.perf_counter() - start
            self.result_queue.put(DotDict({
                'url': f'id:{self.driver_id}_{self.thread_id}',
                'code': err_code,
                'time': elapsed,
                'size': 0,
                'error': e
            }))

if __name__ == "__main__":
    duration = 10
    workers = 7000
    result_queue = queue.Queue()
    thread_driver = WorkerThreadDriver(0, workers, duration, result_queue)
    thread_driver.start()
    thread_driver.join()

    num_requests = 0
    while (True):
        try:
            result = result_queue.get(True, 1)
            num_requests += 1

            # print("Timestamp: {}, Code: {}, Size: {}, Time: {:d}ms, URL: {}".format(
            #         str(datetime.datetime.now()),
            #         result.code,
            #         result.size,
            #         int(result.time*1000),
            #         result.url)
            #     )

        except queue.Empty:
            break

    print(f'num_requests: {num_requests}')


