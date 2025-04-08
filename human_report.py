from datetime import datetime
from typing import List

from loguru import logger
from report import Report
from link import Link


class HumanReport(Report):
    """Generates a human-readable text report from crawled link data."""

    def generate(
        self,
        report_file_name: str,
        links_list: List[Link],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> None:
        """
        Generate a plain text report.

        Args:
            report_file_name: Output text file path.
            links_list: List of Link objects.
            execution_time: A string of the execution time.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.
        """
        with open(report_file_name, 'w', encoding='utf-8') as f:
            f.write("Crawler Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated at     : {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Execution Time   : {execution_time}\n")
            f.write(f"Visited URLs     : {visited_urls_num}\n")
            f.write(f"Threads Used     : {thread_num}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Discovered Links:\n")
            f.write("-" * 60 + "\n")

            for i, link in enumerate(links_list, start=1):
                f.write(f"[{i}] URL         : {link.url}\n")
                f.write(f"     Depth       : {link.depth}\n")
                f.write(f"     Appeared In : {link.first_found_on}\n")
                f.write(f"     Status      : {link.status.name.lower()}\n")
                f.write(f"     Error       : {link.error}\n")
                f.write("-" * 60 + "\n")

        logger.debug(f"Human-readable report written to: {report_file_name}")
