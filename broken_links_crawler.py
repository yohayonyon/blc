import threading
from datetime import datetime
from time import sleep
from typing import List

from loguru import logger

from crawler import Crawler
from email_report_sender import EmailReportSender, EmailMode
from link import Link, LinkStatus
from report_factory import ReportFactory, ReportType
from worker_manager import WorkerManager


def get_email_modes():
    return [mode.value for mode in EmailMode]


def get_report_types():
    return [t.value for t in ReportType]


class EmailParams:
    def __init__(self, email_mode, email_to, email_type, report_types, report_names):
        self.sender = None
        self.mode = None
        self.report_type = None

        if email_to:
            self.sender = EmailReportSender(email_to, email_type)
            self.mode = email_mode
            self.report_type = email_type
            if email_type not in report_types:
                report_types.append(email_type)
                report_names.append(f"report.{email_type}")
                logger.info(f"Adding {email_type} report to the list of reports to generate.")


class BrokenLinksCrawler:
    DEFAULT_THREADS_NUM = 25

    def __init__(
        self,
        target_url: str,
        report_types: List[str],
        report_names: List[str],
        silent: bool,
        crawlers_num: int,
        max_depth: int,
        email_mode: EmailMode,
        email_to: str,
        email_type: ReportType,
        test_mode: bool = False
    ):
        self.email_params = EmailParams(email_mode, email_to, email_type, report_types, report_names)

        self.target_url = target_url
        self.crawlers_num = crawlers_num if crawlers_num != -1 else self.DEFAULT_THREADS_NUM
        self.max_depth = max_depth if max_depth != -1 else float("inf")

        self.broken_links: List[Link] = []
        self.broken_links_lock = threading.Lock()
        self.crawler = Crawler(self.target_url, self.broken_links, self.broken_links_lock, self.max_depth)

        self.report_types = report_types
        self.report_names = report_names
        self.silent = silent

        self.start_time = datetime.now()
        self.stop_live_display = False

        first_link = Link(self.target_url, 0, 'target_url', LinkStatus.NOT_VISITED)
        self.crawlers_manager = WorkerManager(
            first_task=first_link,
            processor=self.crawler,
            repeat_task=False,
            threads_num=self.crawlers_num
        )

        self.test_mode = test_mode

    def start(self) -> None:
        self.crawlers_manager.start()

        if not self.silent:
            display_thread = threading.Thread(target=self.live_display)
            display_thread.start()

        self.crawlers_manager.end()

        if not self.silent:
            self.stop_live_display = True
            display_thread.join()

        if self.test_mode:
            logger.critical(
                f"{self.target_url},{self.crawlers_num},{self.get_time_delta()},{len(self.broken_links)},"
                f"{self.crawlers_manager.get_processed_num()},{self.crawlers_manager.get_tasks_num()}")
        else:
            self.generate_reports_and_email()

            msg = (
                f"Execution Time: {self.get_time_delta()}  |  "
                f"Broken URLs/Visited URLs/Found URLs: {len(self.broken_links)}/"
                f"{self.crawlers_manager.get_processed_num()}/{self.crawlers_manager.get_tasks_num()}"
            )
            logger.info(f"{msg}")

    def get_time_delta(self) -> str:
        """
        Calculate and format elapsed time since start.

        Returns:
            Formatted time string in HH:MM:SS.ss format.
        """
        delta = datetime.now() - self.start_time
        total_seconds = delta.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{total_seconds:.2f}" if self.test_mode else f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"

    def print_status(self, header):
        msg = (
            f"{header}"
            f"Execution Time: {self.get_time_delta()}  |  "
            f"Broken URLs/Visited URLs/Found URLs: {len(self.broken_links)}/"
            f"{self.crawlers_manager.get_processed_num()}/{self.crawlers_manager.get_tasks_num()}"
        )
        print(f"\r{msg}", end='', flush=True)

    def live_display(self) -> None:
        """Continuously display crawler progress in the console."""
        header = f"TEST_MODE  |  {self.target_url}  |  {self.crawlers_num} threads  |  " if self.test_mode else ""

        try:
            while not self.stop_live_display:
                self.print_status(header)
                sleep(0.1)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")

        self.print_status(header)
        print()

    def generate_reports_and_email(self):
        execution_time = self.get_time_delta()
        visited_urls_num = self.crawlers_manager.get_tasks_num()

        for report_type, report_name in zip(self.report_types, self.report_names):
            report = ReportFactory.create_report(report_type)
            with open(report_name, "w") as f:
                report_body = report.generate(self.target_url, self.broken_links, execution_time, visited_urls_num,
                                              self.crawlers_num)
                f.write(report_body)
            logger.info(f"Report {report_name} generated.")

            if self.email_params.sender and ((self.email_params.mode == "errors" and self.broken_links)
                                             or self.email_params.mode == "always") and self.email_params.report_type == report_type:
                self.email_params.sender.send_email_report(report_name)
