
import html
from datetime import datetime
from typing import Any, List

import tzlocal

from link import Link
from report import Report


class HtmlReport(Report):
    def generate(
        self,
        target_url: str,
        broken_links: list[Any],
        fetch_error_links: list[Any],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> str:
        local_time = datetime.now(tzlocal.get_localzone())
        formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        return self._build_html(target_url, broken_links, fetch_error_links, execution_time, visited_urls_num,
                                thread_num, formatted_time)

    @staticmethod
    def _build_html(
        target_url: str,
        broken_links: List[Link],
        fetch_error_links: List[Link],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int,
        generated_at: str
    ) -> str:
        def render_table(links, title, show_status, show_error):
            headers = "<th>#</th><th>URL</th><th>Depth</th><th>Appeared In</th>"
            if show_status:
                headers += "<th>Status</th>"
            if show_error:
                headers += "<th>Error</th>"

            rows = ""
            for idx, link in enumerate(links, 1):
                row = "<tr><td>{}</td>".format(idx)
                row += "<td><a href='{0}' target='_blank'>{0}</a></td>".format(html.escape(link.url))
                row += "<td>{}</td>".format(link.depth)
                row += "<td><a href='{0}' target='_blank'>{0}</a></td>".format(html.escape(link.first_found_on))
                if show_status:
                    row += "<td>{}</td>".format(html.escape(link.status.name.lower()))
                if show_error:
                    row += "<td>{}</td>".format(html.escape(str(link.error)))
                row += "</tr>"
                rows += row

            return "<h2>{}</h2><table class='styled-table'><thead><tr>{}</tr></thead><tbody>{}</tbody></table>".format(title, headers, rows)

        html_report = """<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Broken Links Crawler Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f6f8;
            padding: 40px;
            color: #333;
        }
        h1, h2 {
            color: #2c3e50;
        }
        .styled-table {
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
            width: 100%; table-layout: auto;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .styled-table thead tr {
            background-color: #009879;
            color: #ffffff;
            text-align: left;
        }
        .styled-table th,
        .styled-table td {
            padding: 12px 15px;
            word-wrap: break-word;
        }
        .styled-table tbody tr {
            border-bottom: 1px solid #dddddd;
        }
        .styled-table tbody tr:nth-of-type(even) {
            background-color: #f3f3f3;
        }
        .styled-table tbody tr:last-of-type {
            border-bottom: 2px solid #009879;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .meta {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .meta p {
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <h1>Broken Links Crawler Report</h1>
    <div class='meta'>
        <p><strong>Generated at:</strong> """ + generated_at + """</p>
        <p><strong>Execution Time:</strong> """ + execution_time + """</p>
        <p><strong>Target URL:</strong> <a href='""" + html.escape(target_url) + """' target='_blank'>""" + html.escape(target_url) + """</a></p>
        <p><strong>Visited URLs:</strong> """ + str(visited_urls_num) + """</p>
        <p><strong>Broken URLs:</strong> """ + str(len(broken_links)) + """</p>
        <p><strong>Fetch Error URLs:</strong> """ + str(len(fetch_error_links)) + """</p>
        <p><strong>Threads Used:</strong> """ + str(thread_num) + """</p>
    </div>
""" + render_table(broken_links, "Broken URLs", show_status=True, show_error=False) + render_table(fetch_error_links, "Fetch Error URLs", show_status=False, show_error=True) + """
</body>
</html>"""
        return html_report
