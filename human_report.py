from collections import defaultdict

from loguru import logger

from report import Report


class HumanReport(Report):

    def generate(self, file_name, links, execution_time, visited_urls_num, thread_num):
        counters = defaultdict(int)

        with open(file_name, 'w') as report:
            # Header
            report.write("Broken Links Crawler Report\n")
            report.write("===========================\n")
            report.write("\n")

            # Body
            report.write("The broken links\n")
            report.write("-----------------\n")
            for i, link in enumerate(links):
                report.write(f'({i + 1}) {link}\n')
                counters[link.status] += 1

            # Footer
            report.write("\n")
            report.write("Summary\n")
            report.write("-------\n")
            report.write(f"The execution took {execution_time}.\n")
            report.write(f"{visited_urls_num} URLs were visited by {thread_num} threads.\n")
            report.write(f"The following errors were found:\n")
            for i, link_status in enumerate(counters):
                report.write(f"({i + 1}) {counters[link_status]} URLs with status {link_status.name.lower()}\n")

            logger.info(f"A textual report written to: {file_name}")
