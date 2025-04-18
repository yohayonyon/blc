
import json
from datetime import datetime, timezone
from typing import List

from loguru import logger

from link import Link
from report import Report


class JsonReport(Report):
    def generate(
            self,
            target_url: str,
            broken_links: List[Link],
            fetch_error_links: List[Link],
            execution_time: str,
            visited_urls_num: int,
            thread_num: int
    ) -> str | None:
        def serialize_link(link: Link, include_status=True, include_error=True) -> dict:
            result = {
                "url": link.url,
                "depth": link.depth,
                "appeared_in": link.first_found_on,
            }
            if include_status:
                result["status"] = link.status.name.lower()
            if include_error:
                result["error"] = link.error
            return result

        report = {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_time_seconds": execution_time,
            "target_url": target_url,
            "visited_urls": visited_urls_num,
            "threads_used": thread_num,
            "broken_links": [serialize_link(link, include_status=True, include_error=False) for link in broken_links],
            "fetch_errors": [serialize_link(link, include_status=False, include_error=True) for link in fetch_error_links]
        }

        logger.info("A JSON report was generated.")
        return json.dumps(report, indent=4)
