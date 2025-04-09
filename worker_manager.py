import queue
import threading
from typing import Any

from loguru import logger


class WorkerManager:
    """Manages a pool of threads to process tasks concurrently."""

    def __init__(self, first_task: Any, processor: Any, threads_num: int, repeat_task: bool = True):
        """
        Initialize the worker manager.

        Args:
            first_task: The initial task to start with.
            processor: An object with a `process(task)` method.
            threads_num: Number of worker threads.
            repeat_task: Whether to repeatedly reprocess the same tasks.
        """
        self.first_task = first_task
        self.processor = processor
        self.threads_num = threads_num
        self.repeat_task = repeat_task
        self.threads: list[threading.Thread] = []
        self.task_queue: queue.Queue = queue.Queue()

        if not repeat_task:
            self.all_tasks_to_process: set = {first_task}
            self.all_tasks_to_process_lock = threading.Lock()

        self.processed_counter: int = 0
        self.processed_counter_lock = threading.Lock()

    def worker(self) -> None:
        """Thread function for processing tasks from the queue."""
        logger.debug("Starting")
        self.processor.initiate()

        while True:
            task = self.task_queue.get()
            if task is None:
                self.task_queue.task_done()
                break

            try:
                new_tasks = self.processor.process(task)
                with self.processed_counter_lock:
                    self.processed_counter += 1
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
        logger.debug("Finished")

    def start(self) -> None:
        """Start the worker threads and add the first task to the queue."""
        logger.debug("Work is starting.")
        self.task_queue.put(self.first_task)
        for i in range(self.threads_num):
            t = threading.Thread(target=self.worker, name=f"Worker-{i + 1}")
            t.start()
            self.threads.append(t)

    def end(self) -> None:
        """Wait for all tasks to finish and join all threads."""
        self.task_queue.join()
        for _ in range(self.threads_num):
            self.task_queue.put(None)
        for t in self.threads:
            t.join()
        logger.info(f"{len(self.all_tasks_to_process)} tasks were processed.")

    def get_tasks_num(self) -> int:
        """Return the number of unique tasks seen."""
        with self.all_tasks_to_process_lock:
            return len(self.all_tasks_to_process)

    def get_processed_num(self) -> int:
        """Return the number of tasks that have been processed."""
        with self.processed_counter_lock:
            return self.processed_counter
