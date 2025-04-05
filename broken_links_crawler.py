import os
import threading
import time
from datetime import datetime

import requests

from crawler import Crawler
from link import Link, LinkStatus
from report_factory import ReportGenerator
from worker_manager import WorkerManager


class BrokenLinksCrawler:
    def __init__(self, target_url, report_types, report_names, silent, crawlers_num, max_depth=-1):
        self.target_url = target_url if target_url[-1] == '/' else f'{target_url}/'
        self.crawlers_num = crawlers_num if crawlers_num != -1 else os.cpu_count()
        self.max_depth = max_depth if max_depth != -1 else float("inf")

        self.session = requests.Session()
        self.broken_links = []
        self.broken_links_lock = threading.Lock()

        self.crawler = Crawler(target_url, self.broken_links, self.broken_links_lock, session=self.session,
                               max_depth=self.max_depth)

        self.report_types = report_types
        self.report_names = report_names
        self.silent = silent

        self.start_time = datetime.now()

        self.stop_live_display = False

        first_link = Link(self.target_url, 0, 'target_url', LinkStatus.NOT_VISITED)
        self.crawlers_manager = WorkerManager(first_task=first_link, processor=self.crawler, repeat_task=False,
                                              threads_num=self.crawlers_num)

    def start(self):
        self.crawlers_manager.start()

        if not self.silent:
            display_thread = threading.Thread(target=self.live_display)
            display_thread.start()

        self.crawlers_manager.end()

        if not self.silent:
            self.stop_live_display = True
            display_thread.join()

        execution_time = datetime.now() - self.start_time
        visited_urls_num = self.crawlers_manager.get_tasks_num()
        for report_type, report_name in zip(self.report_types, self.report_names):
            report = ReportGenerator.create_report(report_type)
            report.generate(report_name, self.broken_links, execution_time, visited_urls_num, self.crawlers_num)

    def live_display(self):
        start_time = time.time()

        try:
            while not self.stop_live_display:
                elapsed = time.time() - start_time
                msg = f"Execution Time: {elapsed:.1f}s | Visited URLs: {self.crawlers_manager.get_tasks_num()} | " \
                      f"Broken URLs Found: {len(self.broken_links)}"
                print(f"\r{msg}", end='', flush=True)

                time.sleep(0.1)  # Simulate some work

            print()  # Move to next line after done

        except KeyboardInterrupt:
            print("\nInterrupted by user.")

        a = 3


"""
import time

for i in reversed(range(11)):
    print(f"\rCountdown: {i} seconds remaining", end='', flush=True)
    time.sleep(1)

print("\nDone!")
"""
