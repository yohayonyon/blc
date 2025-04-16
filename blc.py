import argparse
import sys
from report_factory import ReportType

from loguru import logger
from broken_links_crawler import BrokenLinksCrawler, get_email_modes, get_report_types


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments as a namespace.
    """
    parser = argparse.ArgumentParser(description="Crawl and find broken links on a website")

    parser.add_argument("url", help="A website URL to crawl")
    parser.add_argument("-t", "--threads", type=int, default=-1, help="Number of threads to execute in parallel")
    parser.add_argument("-d", "--depth", type=int, default=-1, help="Maximum crawl depth")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress live terminal output")
    parser.add_argument("-v", "--log_verbosity",
                        choices=["none", "trace", "debug", "info", "success", "warning", "error", "critical"],
                        default="none", help="Log verbosity level")
    parser.add_argument("--log_file", default="blc.log", help="Change the log file name from blc.log")
    parser.add_argument("--text_report", default="report.txt",
                        help="Change the text report file name from report.txt")
    parser.add_argument("--json_report", default="report.json",
                        help="Change the json report file name from report.json")
    parser.add_argument("--html_report", default="report.html",
                        help="Change the html report file name from report.html")
    parser.add_argument("--log_display", action="store_true",
                        help="If set log will be printed also to stdout")
    parser.add_argument("--email_to", type=str, help="Destination email address for sending report")
    parser.add_argument( "--email_mode", choices=get_email_modes(), default="always",
                         help="When to send the report via email")
    parser.add_argument("--email_type", choices=get_report_types(), default="html",
                         help="What type of report to send via email")
    parser.add_argument("--email_config", type=str, default="email_config.json",
                        help="Path to the email configuration JSON file.")
    parser.add_argument("--test_mode", action="store_true",
                        help="If set, all log prints will be removed for a special log print.")

    return parser.parse_args()


def set_log_level(log_level: str, file_name: str, log_to_screen: bool, test_mode: bool) -> None:
    """
    Set the log level and output destination.

    Args:
        log_level: Logging level string.
        file_name: File to write logs to.
        log_to_screen: Whether to log to the terminal.
        test_mode: Special log format for testing.
    """
    logger.remove()
    if test_mode:
        logger.add(
            file_name,
            level="CRITICAL",
            format="{message}"
        )
        return
    if log_level != "none":
        if log_to_screen:
            logger.add(
                sys.stdout,
                level=log_level.upper(),
                format=(
                    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                    "<level>{level:<1}</level> | "
                    "<cyan>{thread.name:<1}</cyan>:<cyan>{name:<1}</cyan>:"
                    "<cyan>{function:<1}</cyan>:<cyan>{line:<1}</cyan> | {message}"
                )
            )
    logger.add(
        file_name,
        level=log_level.upper() if log_level != "none" else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level:<1}</level> | "
            "<cyan>{thread.name:<1}</cyan>:<cyan>{name:<1}</cyan>:"
            "<cyan>{function:<1}</cyan>:<cyan>{line:<1}</cyan> | {message}"
        )
    )


def main() -> None:
    """Entry point for the CLI application."""
    args = parse_arguments()

    set_log_level(args.log_verbosity, args.log_file, args.log_display, args.test_mode)

    report_types = get_report_types()
    report_names = [args.text_report, args.json_report, args.html_report]

    crawler = BrokenLinksCrawler(
        target_url=args.url,
        report_types=report_types,
        report_names=report_names,
        silent=True if args.log_display else args.silent,
        crawlers_num=args.threads,
        max_depth=args.depth,
        email_mode=args.email_mode,
        email_to=args.email_to,
        email_type=args.email_type,
        test_mode=args.test_mode
    )
    crawler.start()


if __name__ == "__main__":
    main()
