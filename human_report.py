from datetime import datetime

from loguru import logger

from report import Report


class HumanReport(Report):

    def generate(self, report_file_name, links_list, execution_time, visited_urls_num, thread_num):
        """
        Generates a human-readable plain text report for a crawler run.

        Parameters:
            report_file_name (str): Output text file path.
            links_list (List[Dict]): List of link info dictionaries.
            execution_time (float): Execution time in seconds.
            visited_urls_num (int): Number of visited URLs.
            thread_num (int): Number of threads used.
        """

        with open(report_file_name, 'w', encoding='utf-8') as f:
            f.write("Crawler Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated at     : {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Execution Time   : {execution_time}\n")
            f.write(f"Visited URLs     : {visited_urls_num}\n")
            f.write(f"Threads Used     : {thread_num}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Discovered Links:\n")
            f.write("-" * 60 + "\n")

            for i, link in enumerate(links_list, start=1):
                f.write(f"[{i}] URL         : {link.url}\n")
                f.write(f"     Depth       : {link.depth}\n")
                f.write(f"     Appeared In : {link.first_found_on}\n")
                f.write(f"     Status      : {link.status.name.lower()}\n")
                f.write(f"     Error       : {link.error}\n")
                f.write("-" * 60 + "\n")

        logger.debug(f"Human-readable report written to: {report_file_name}")
