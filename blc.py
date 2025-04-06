import argparse
import sys

from loguru import logger

from broken_links_crawler import BrokenLinksCrawler


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
    parser.add_argument("-l", "--log_level", choices=["none", "trace", "debug", "info", "success", "warning",
                                                      "error", "critical"],
                        default="none", help="How verbose you want the log to be [none, trace, debug, info, "
                                             "success, warning, error, critical].")
    parser.add_argument("-e", "--email_to", type=str, help="Destination email address to send the report to")
    parser.add_argument("-er", "--email_report", choices=["never", "errors", "always"], default="never",
                        help="Where to send the email report to [never, errors, or always]")

    args = parser.parse_args()

    return args


def set_log_level(log_level):
    # Configure loguru: include timestamp, level, and thread name (crawler ID)
    logger.remove()
    if log_level != "none":
        logger.add(
            sys.stdout,
            level=log_level.upper(),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <1}</level> | "
                   "<cyan>{thread.name: <1}</cyan>:<cyan>{name: <1}</cyan>:<cyan>{function: <1}</cyan>:<cyan>{line: <1}</cyan> | "
                   "{message}"
        )


def main():
    args = parse_arguments()
    if args.email_report != "never":
        if not args.email_to:
            print("You must specify --email_to if you want to send a report.")
            return

    set_log_level(args.log_level)

    report_types = ["human", "json"]
    report_names = [args.human_report, args.json_report]

    broken_links_crawler = BrokenLinksCrawler(target_url=args.url, report_types=report_types,
                                              report_names=report_names, silent=args.silent,
                                              crawlers_num=args.threads, max_depth=args.depth,
                                              email_report=args.email_report, email_to=args.email_to)
    broken_links_crawler.start()


if __name__ == "__main__":
    main()
