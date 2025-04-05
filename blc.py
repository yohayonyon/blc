import argparse
import sys

from loguru import logger

from broken_links_crawler import BrokenLinksCrawler


class BLC:
    def __init__(self):
        self.arguments = self.parse_arguments()

    def work(self, ):
        self.parse_arguments()
        self.set_log_level()

        report_types = ["human", "json"]
        report_names = [self.arguments.human_report, self.arguments.json_report]

        broken_links_crawler = BrokenLinksCrawler(target_url=self.arguments.url, report_types=report_types,
                                                  report_names=report_names, silent=self.arguments.silent,
                                                  crawlers_num=self.arguments.threads, max_depth=self.arguments.depth)
        broken_links_crawler.start()

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description="Crawl and find broken links on a website")

        # Positional arguments
        parser.add_argument("url", help="A website url")

        # Optional arguments
        parser.add_argument("-t", "--threads", type=int, default=-1, help="Num of threads to execute in parallel")
        parser.add_argument("-d", "--depth", type=int, default=-1, help="Crawling depth")
        parser.add_argument("-s", "--silent", action="store_true", help="Print nothing to screen")
        parser.add_argument("-hr", "--human_report", default="report.txt",
                            help="The name for a human readable report to generate")
        parser.add_argument("-jr", "--json_report", default="report.json",
                            help="The name for a json readable report to generate")
        parser.add_argument("-pm", "--prints_mode", choices=["regular", "silent"], default="regular",
                            help="What to print to screen during execution (regular, silent).")
        parser.add_argument("-l", "--log_level", choices=["none", "trace", "debug", "info", "success", "warning",
                                                          "error", "critical"],
                            default="none", help="How verbose you want the log to be [none, trace, debug, info, "
                                                 "success, warning, error, critical].")

        args = parser.parse_args()

        return args

    def set_log_level(self):
        # Configure loguru: include timestamp, level, and thread name (crawler ID)
        logger.remove()
        if self.arguments.log_level != "none":
            logger.add(
                sys.stdout,
                level=self.arguments.log_level.upper(),
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <1}</level> | "
                       "<cyan>{thread.name: <1}</cyan>:<cyan>{name: <1}</cyan>:<cyan>{function: <1}</cyan>:<cyan>{line: <1}</cyan> | "
                       "{message}"
            )


if __name__ == "__main__":
    blc = BLC()
    blc.work()
