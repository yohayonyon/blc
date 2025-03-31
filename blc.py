import argparse
import time

from loguru import logger

from broken_links_crawler import BrokenLinksCrawler


def parse_arguments():
    parser = argparse.ArgumentParser(description="Crawl and find broken links on a website")

    # Positional arguments
    parser.add_argument("url", help="A website url")

    # Optional arguments
    parser.add_argument("-t", "--threads", type=int, default=4, help="Num of threads to execute in parallel")
    parser.add_argument("-d", "--depth", type=int, default=5, help="Crawling depth")
    parser.add_argument("-r", "--report", choices=["json", "human"], default="human",
                        help="The type of report to generate (json, human).")
    parser.add_argument("-pm", "--prints_mode", choices=["regular", "silent"], default="regular",
                        help="What to print to screen during execution (regular, silent).")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    arguments = parse_arguments()

    # target_urls = ["https://webee.technion.ac.il/~ayellet/",
    #                "https://cgm.technion.ac.il/",
    #                "https://ece.technion.ac.il/"]

    arguments.url = "https://ece.technion.ac.il/"
    arguments.threads = 50
    arguments.depth = 3

    start_time = time.time()

    blc = BrokenLinksCrawler(target_url=arguments.url, workers_num=arguments.threads, depth=arguments.depth)
    blc.start()

    logger.info(f' it took {(time.time() - start_time):.2f}')
