
from datetime import datetime
from typing import List
import html
import tzlocal

from link import Link
from report import Report


class HtmlReport(Report):
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
        generated_at = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        return self._generate_html(target_url, broken_links, fetch_error_links,
                                   execution_time, visited_urls_num, thread_num, generated_at)

    @staticmethod
    def _generate_html(target_url, broken_links, fetch_error_links,
                       execution_time, visited_urls_num, thread_num, generated_at) -> str:
        def table(title, links, show_status, show_error):
            header = "<tr><th>#</th><th>URL</th><th>Depth</th><th>Appeared In</th>"
            if show_status:
                header += "<th>Status</th>"
            if show_error:
                header += "<th>Error</th>"
            header += "</tr>\n"

            rows = []
            for i, link in enumerate(links, 1):
                row = f"<tr><td>{i}</td><td>{link.url}</td><td>{link.depth}</td><td>{link.first_found_on}</td>"
                if show_status:
                    row += f"<td>{link.status.name.lower()}</td>"
                if show_error:
                    row += f"<td>{link.error}</td>"
                row += "</tr>"
                rows.append(row)

            return f"<h2>{title}</h2><table border='1'>\n<thead>{header}</thead><tbody>\n" + "\n".join(rows) + "\n</tbody></table>"

        report = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Broken Links Report</title></head><body>
<h1>Broken Links Crawler Report</h1>
<p><strong>Generated at:</strong> {generated_at}</p>
<p><strong>Execution Time:</strong> {execution_time}</p>
<p><strong>Target URL:</strong> {target_url}</p>
<p><strong>Visited URLs:</strong> {visited_urls_num}</p>
<p><strong>Broken URLs:</strong> {len(broken_links)}</p>
<p><strong>Fetch Error URLs:</strong> {len(fetch_error_links)}</p>
<p><strong>Threads Used:</strong> {thread_num}</p>
{table("Broken URLs", broken_links, show_status=True, show_error=False)}
{table("Fetch Error URLs", fetch_error_links, show_status=False, show_error=True)}
</body></html>"""
        return report
