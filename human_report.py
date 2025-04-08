from datetime import datetime
from typing import List

from loguru import logger
from report import Report
from link import Link


class HumanReport(Report):
    """Generates a human-readable text report from crawled link data."""

    def generate(
        self,
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
        report = "Crawler Report\n"
        report += "=" * 60 + "\n"
        report += f"Generated at     : {datetime.utcnow().isoformat()}Z\n"
        report += f"Execution Time   : {execution_time}\n"
        report += f"Visited URLs     : {visited_urls_num}\n"
        report += f"Threads Used     : {thread_num}\n"
        report += "=" * 60 + "\n\n"
        report += "Discovered Links:\n"
        report += "-" * 60 + "\n"

        for i, link in enumerate(links_list, start=1):
            report += f"[{i}] URL         : {link.url}\n"
            report += f"     Depth       : {link.depth}\n"
            report += f"     Appeared In : {link.first_found_on}\n"
            report += f"     Status      : {link.status.name.lower()}\n"
            report += f"     Error       : {link.error}\n"
            report += "-" * 60 + "\n"

        logger.info(f"Human-readable report was generated.")

        return report
