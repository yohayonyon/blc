import json
from datetime import datetime
from typing import List

from loguru import logger
from report import Report
from link import Link


class JsonReport(Report):
    """Generates a JSON report from crawled link data."""

    def generate(
        self,
        report_file_name: str,
        links_list: List[Link],
        execution_time: float,
        visited_urls_num: int,
        thread_num: int
    ) -> None:
        """
        Generate a JSON report file.

        Args:
            report_file_name: Output JSON file name.
            links_list: List of Link objects.
            execution_time: Total crawl time in seconds.
            visited_urls_num: Number of URLs visited.
            thread_num: Number of threads used.
        """
        report = {
            "report_generated_at": datetime.utcnow().isoformat() + "Z",
            "execution_time_seconds": execution_time,
            "visited_urls": visited_urls_num,
            "threads_used": thread_num,
            "links": []
        }

        for link in links_list:
            report["links"].append({
                "url": link.url,
                "depth": link.depth,
                "appeared_in": link.first_found_on,
                "status": link.status.name.lower(),
                "error": link.error
            })

        with open(report_file_name, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)

        logger.info(f"A JSON report written to: {report_file_name}")
