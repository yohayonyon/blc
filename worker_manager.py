import queue
import threading

from loguru import logger


class WorkerManager:
    def __init__(self, first_task, processor, threads_num, repeat_task=True):
        self.first_task = first_task

        self.processor = processor
        self.threads_num = threads_num

        self.repeat_task = repeat_task
        self.threads = []

        self.task_queue = queue.Queue()
        if not repeat_task:
            self.all_tasks_to_process = set([first_task])
            self.all_tasks_to_process_lock = threading.Lock()

    def worker(self):
        logger.debug(f"Starting")
        while True:
            task = self.task_queue.get()  # Block until an item is available.
            if task is None:
                self.task_queue.task_done()
                break

            try:
                new_tasks = self.processor.process(task)
            except Exception as e:
                logger.error(f"Error: {e}")
                self.task_queue.task_done()
                continue

            if not self.repeat_task:
                for task in new_tasks:
                    with self.all_tasks_to_process_lock:
                        if task in self.all_tasks_to_process:
                            continue
                        self.all_tasks_to_process.add(task)
                    self.task_queue.put(task)
            else:
                self.task_queue.put(task)

            self.task_queue.task_done()

        self.processor.finalize()

        logger.debug(f"Finished")

    def start(self):
        logger.debug("Work is starting.")
        self.task_queue.put(self.first_task)
        for i in range(self.threads_num):
            t = threading.Thread(target=self.worker, name=f"Worker-{i + 1}")
            t.start()
            self.threads.append(t)

    def end(self):
        self.task_queue.join()
        for _ in range(self.threads_num):
            self.task_queue.put(None)
        for t in self.threads:
            t.join()
        logger.info(f"{len(self.all_tasks_to_process)} tasks were processed.")

    def get_tasks_num(self):
        return len(self.all_tasks_to_process)
