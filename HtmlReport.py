from typing import Any, List
from datetime import datetime
from report import Report  # Adjust if Report is defined elsewhere
from link import Link  # Assuming Link has: url, depth, first_found_on, status, error
import html


class HtmlReport(Report):
    """Generates a crawler report in HTML format."""

    def generate(
        self,
        links: List[Any],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> str:
        """
        Generate an HTML report and save it to a file.

        Args:
            links: List of Link objects.
            execution_time: Time taken to run the crawler.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.
        """
        return self._build_html(links, execution_time, visited_urls_num, thread_num)

    @staticmethod
    def _build_html(
        links: List[Link],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> str:
        """Build the full HTML content as a string."""
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
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
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
    </style>
</head>
<body>
    <h1>Broken Links Crawler Report</h1>
    <div class="meta">
        <p><strong>Generated at:</strong> {datetime.utcnow().isoformat()}Z</p>
        <p><strong>Execution Time:</strong> {execution_time}</p>
        <p><strong>Visited URLs:</strong> {visited_urls_num}</p>
        <p><strong>Threads Used:</strong> {thread_num}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>URL</th>
                <th>Depth</th>
                <th>Appeared In</th>
                <th>Status</th>
                <th>Error</th>
            </tr>
        </thead>
        <tbody>
"""

        rows = ""
        for idx, link in enumerate(links, start=1):
            rows += f"""<tr>
                <td>{idx}</td>
                <td>{html.escape(link.url)}</td>
                <td>{link.depth}</td>
                <td>{html.escape(link.first_found_on)}</td>
                <td>{html.escape(link.status.name.lower())}</td>
                <td>{html.escape(str(link.error))}</td>
            </tr>
"""

        footer = """
        </tbody>
    </table>
</body>
</html>
"""
        return header + rows + footer
