import os
import threading
import time
from datetime import datetime

import requests

from crawler import Crawler
from email_report_sender import EmailReportSender
from link import Link, LinkStatus
from report_factory import ReportGenerator
from worker_manager import WorkerManager


class BrokenLinksCrawler:
    EMAIL_SENDER = 'blc@blc.org'
    EMAIL_PASSWORD = 'abcdefgh'

    def __init__(self, target_url, report_types, report_names, silent, crawlers_num, max_depth, email_report, email_to):
        self.target_url = target_url if target_url[-1] == '/' else f'{target_url}/'
        self.crawlers_num = crawlers_num if crawlers_num != -1 else os.cpu_count()
        self.max_depth = max_depth if max_depth != -1 else float("inf")
        self.email_report = email_report
        self.email_to = email_to

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

        execution_time = self.get_time_delta()

        visited_urls_num = self.crawlers_manager.get_tasks_num()
        for report_type, report_name in zip(self.report_types, self.report_names):
            report = ReportGenerator.create_report(report_type)
            report.generate(report_name, self.broken_links, execution_time, visited_urls_num, self.crawlers_num)

        if (self.email_report == "errors" and len(self.broken_links) > 0) or self.email_report == "always":
            email_sender = EmailReportSender(self.EMAIL_SENDER, self.EMAIL_PASSWORD, self.email_to)
            email_sender.generate_and_send(self.email_report, self.broken_links, execution_time,
                                           self.crawlers_manager.get_tasks_num(), self.crawlers_num)

    def get_time_delta(self):
        delta = datetime.now() - self.start_time
        total_seconds = delta.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"

    def live_display(self):
        try:
            while not self.stop_live_display:
                msg = f"Execution Time: {self.get_time_delta()}  |  " \
                      f"Broken URLs/Visited URLs/Found URLs: {len(self.broken_links)}/{self.crawlers_manager.get_visited_num()}/{self.crawlers_manager.get_tasks_num()}"
                print(f"\r{msg}", end='', flush=True)

                time.sleep(0.1)  # Simulate some work

            print()  # Move to next line after done

        except KeyboardInterrupt:
            print("\nInterrupted by user.")
