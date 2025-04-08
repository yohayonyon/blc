import os
import threading
from datetime import datetime
from typing import List

from loguru import logger

from crawler import Crawler
from email_report_sender import EmailReportSender, EmailMode
from link import Link, LinkStatus
from report_factory import ReportFactory, ReportType
from worker_manager import WorkerManager


def get_report_types():
    return [rt.value for rt in list(ReportType)]


def get_email_modes():
    return [em.value for em in list(EmailMode)]

class BrokenLinksCrawler:
    """Main class for running the broken links crawler and generating reports."""
    NUM_OF_THREADS_PER_CORE = 5
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
        email_type: ReportType
    ):
        """
        Initialize the BrokenLinksCrawler.

        Args:
            target_url: Root URL to crawl.
            report_types: List of report types to generate.
            report_names: Corresponding list of report file names.
            silent: Whether to disable live console display.
            crawlers_num: Number of crawler threads (-1 to auto-detect).
            max_depth: Maximum crawl depth (-1 for unlimited).
            email_mode: When to send email report ("always", "errors", or "never").
            email_to: Recipient email address.
        """
        self.email_sender, self.email_mode, self.email_type =  self.init_email_params(email_mode, email_to, email_type,
                                                                                      report_types, report_names)

        self.target_url = target_url
        self.crawlers_num = crawlers_num if crawlers_num != -1 else os.cpu_count() * self.NUM_OF_THREADS_PER_CORE
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

    @staticmethod
    def init_email_params(email_mode, email_to, email_type, report_types, report_names):
        if email_to:
            _email_sender = EmailReportSender(email_to, email_type)
            _email_mode = email_mode
            _email_type = email_type
            if email_type not in report_types:
                report_types.append(email_type)
                report_names.append(f"report.{email_type}")
                logger.info(f"Adding {email_type} report to the list of reports to generate.")
        else:
            _email_sender = None
            _email_mode = None
            _email_type = None
        return _email_sender, _email_mode, _email_type

    def start(self) -> None:
        """Start the crawling process and generate reports."""
        self.crawlers_manager.start()

        if not self.silent:
            display_thread = threading.Thread(target=self.live_display)
            display_thread.start()

        self.crawlers_manager.end()

        if not self.silent:
            self.stop_live_display = True
            display_thread.join()

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
        return f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"

    def live_display(self) -> None:
        """Continuously display crawler progress in the console."""
        try:
            while not self.stop_live_display:
                msg = (
                    f"Execution Time: {self.get_time_delta()}  |  "
                    f"Broken URLs/Visited URLs/Found URLs: {len(self.broken_links)}/"
                    f"{self.crawlers_manager.get_processed_num()}/{self.crawlers_manager.get_tasks_num()}"
                )
                print(f"\r{msg}", end='', flush=True)
            print()
        except KeyboardInterrupt:
            print("\nInterrupted by user.")

    def generate_reports_and_email(self):
        execution_time = self.get_time_delta()
        visited_urls_num = self.crawlers_manager.get_tasks_num()

        for report_type, report_name in zip(self.report_types, self.report_names):
            report = ReportFactory.create_report(report_type)
            with open(report_name, "w") as f:
                report_body = report.generate(self.broken_links, execution_time, visited_urls_num, self.crawlers_num)
                f.write(report_body)
            logger.info(f"Report {report_name} generated.")

            if self.email_sender and ((self.email_mode == "errors" and self.broken_links) or self.email_mode == "always") and self.email_type == report_type:
                self.email_sender.send_email_report(report_name)
