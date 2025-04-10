import html
from datetime import datetime
from typing import Any, List

import tzlocal

from link import Link  # Assuming Link has: url, depth, first_found_on, status, error
from report import Report  # Adjust if Report is defined elsewhere


class HtmlReport(Report):
    """Generates a crawler report in HTML format."""

    def generate(
            self,
            target_url: str,
            links: List[Any],
            execution_time: str,
            visited_urls_num: int,
            thread_num: int
    ) -> str:
        """
        Generate an HTML report and save it to a file.

        Args:
            target_url: The site that was crawled.
            links: List of Link objects.
            execution_time: Time taken to run the crawler.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.
        """
        local_time = datetime.now(tzlocal.get_localzone())
        formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        return self._build_html(target_url, links, execution_time, visited_urls_num, thread_num, formatted_time)

    @staticmethod
    def _build_html(
            target_url: str,
            links: List[Link],
            execution_time: str,
            visited_urls_num: int,
            thread_num: int,
            generated_at: str
    ) -> str:
        """Build the full HTML content as a string."""
        escaped_target_url = html.escape(target_url)
        target_url_link = f'<a href="{escaped_target_url}" target="_blank" rel="noopener noreferrer">{escaped_target_url}</a>'

        header = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Broken Links Crawler Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        h1 {{
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
            vertical-align: top;
            overflow-wrap: break-word;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .meta {{
            margin-bottom: 20px;
        }}

        .col-num {{ width: 4ch; }}
        .col-url {{ max-width: 300px; word-break: break-word; }}
        .col-depth {{ width: 6ch; }}
        .col-status {{ width: 21ch; }}
        .col-error {{ width: 24ch; }}
    </style>
</head>
<body>
    <h1>Broken Links Crawler Report</h1>
    <div class="meta">
        <p><strong>Generated at:</strong> {generated_at}</p>
        <p><strong>Execution Time:</strong> {execution_time}</p>
        <p><strong>Target Url:</strong> {target_url_link}</p>
        <p><strong>Visited URLs:</strong> {visited_urls_num}</p>
        <p><strong>Broken URLs:</strong> {len(links)}</p>
        <p><strong>Threads Used:</strong> {thread_num}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th class="col-num">#</th>
                <th class="col-url">URL</th>
                <th class="col-depth">Depth</th>
                <th>Appeared In</th>
                <th class="col-status">Status</th>
                <th class="col-error">Error</th>
            </tr>
        </thead>
        <tbody>
"""

        rows = ""
        for idx, link in enumerate(links, start=1):
            escaped_url = html.escape(link.url)
            hyperlink = f'<a href="{escaped_url}" target="_blank" rel="noopener noreferrer">{escaped_url}</a>'

            escaped_appeared_in = html.escape(link.first_found_on)
            appeared_link = f'<a href="{escaped_appeared_in}" target="_blank" rel="noopener noreferrer">{escaped_appeared_in}</a>'

            rows += f"""<tr>
                <td class="col-num">{idx}</td>
                <td class="col-url">{hyperlink}</td>
                <td class="col-depth">{link.depth}</td>
                <td>{appeared_link}</td>
                <td class="col-status">{html.escape(link.status.name.lower())}</td>
                <td class="col-error">{html.escape(str(link.error))}</td>
            </tr>
"""

        footer = """
        </tbody>
    </table>
</body>
</html>
"""
        return header + rows + footer
