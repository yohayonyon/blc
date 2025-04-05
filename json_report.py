import json
from datetime import datetime

from loguru import logger

from report import Report


class JsonReport(Report):
    def generate(self, report_file_name, links_list, execution_time, visited_urls_num, thread_num):
        """
        Generates a JSON report for a crawler run.

        Parameters:
            report_file_name (str): Path to the output JSON report file.
            links_list (List[Dict]): List of link information dictionaries.
            execution_time (float): Total time taken by the crawler (in seconds).
            visited_urls_num (int): Total number of visited URLs.
            thread_num (int): Number of threads used during crawling.
        """

        report = {
            "report_generated_at": datetime.utcnow().isoformat() + "Z",
            "execution_time_seconds": str(execution_time),
            "visited_urls": visited_urls_num,
            "threads_used": thread_num,
            "links": []
        }

        for link in links_list:
            report["links"].append({
                "url": link.url,
                "depth": link.depth,
                "appeared_in": link.appeared_in,
                "status": link.status.name.lower(),
                "error": link.error
            })

        with open(report_file_name, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)

        logger.info(f"A JSON report written to: {report_file_name}")
