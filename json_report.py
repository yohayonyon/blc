import json
from datetime import datetime, timezone
from typing import List

from loguru import logger
from report import Report
from link import Link


class JsonReport(Report):
    """Generates a JSON report from crawled link data."""

    def generate(
        self,
        target_url: str,
        links_list: List[Link],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> str | None:
        """
        Generate a JSON report file.

        Args:
            target_url: The site that was crawled.
            links_list: List of Link objects.
            execution_time: TA string of total crawl time.
            visited_urls_num: Number of URLs visited.
            thread_num: Number of threads used.
        """
        report = {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_time_seconds": execution_time,
            "target_url": target_url,
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

        logger.info(f"A JSON report was generated.")

        return json.dumps(report, indent=4)
