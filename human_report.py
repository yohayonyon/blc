from datetime import datetime
from typing import List

import tzlocal
from loguru import logger

from link import Link
from report import Report


class HumanReport(Report):
    """Generates a human-readable text report from crawled link data."""

    def generate(
            self,
            target_url: str,
            links_list: List[Link],
            execution_time: str,
            visited_urls_num: int,
            thread_num: int
    ) -> None:
        """
        Generate a plain text report.

        Args:
            target_url: The site that was crawled.
            links_list: List of Link objects.
            execution_time: A string of the execution time.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.
        """
        local_time = datetime.now(tzlocal.get_localzone())
        formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        report = "Crawler Report\n"
        report += "=" * 60 + "\n"
        report += f"Generated at     : {formatted_time}\n"
        report += f"Execution Time   : {execution_time}\n"
        report += f"target URL       : {target_url}\n"
        report += f"Visited URLs     : {visited_urls_num}\n"
        report += f"Broken URLs      : {len(links_list)}\n"
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
