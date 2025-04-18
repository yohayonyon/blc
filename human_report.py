
from datetime import datetime
from typing import List

import tzlocal
from loguru import logger

from link import Link
from report import Report


class HumanReport(Report):
    def generate(
            self,
            target_url: str,
            broken_links: List[Link],
            fetch_error_links: List[Link],
            execution_time: str,
            visited_urls_num: int,
            thread_num: int
    ) -> str:
        local_time = datetime.now(tzlocal.get_localzone())
        formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        report = "Crawler Report\n"
        report += "=" * 60 + "\n"
        report += f"Generated at     : {formatted_time}\n"
        report += f"Execution Time   : {execution_time}\n"
        report += f"Target URL       : {target_url}\n"
        report += f"Visited URLs     : {visited_urls_num}\n"
        report += f"Broken URLs      : {len(broken_links)}\n"
        report += f"Fetch Error URLs : {len(fetch_error_links)}\n"
        report += f"Threads Used     : {thread_num}\n"
        report += "=" * 60 + "\n\n"

        def format_section(links: List[Link], title: str, include_status: bool, include_error: bool) -> str:
            section = f"{title}:\n" + "-" * 60 + "\n"
            for i, link in enumerate(links, start=1):
                section += f"[{i}] URL         : {link.url}\n"
                section += f"     Depth       : {link.depth}\n"
                section += f"     Appeared In : {link.first_found_on}\n"
                if include_status:
                    section += f"     Status      : {link.status.name.lower()}\n"
                if include_error:
                    section += f"     Error       : {link.error}\n"
                section += "-" * 60 + "\n"
            return section + "\n"

        report += format_section(broken_links, "Broken Links", True, False)
        report += format_section(fetch_error_links, "Fetch Error URLs", False, True)

        logger.info("Human-readable report was generated.")
        return report
