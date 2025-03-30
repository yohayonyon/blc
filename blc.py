import argparse
import time
from loguru import logger
from crawlers_manager import CrawlesManager


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

    arguments.url = "https://webee.technion.ac.il/~ayellet/"
    arguments.threads = 5
    arguments.depth = 5


    start_time = time.time()

    cm = CrawlesManager(target_url=arguments.url, workers_num=arguments.threads, depth=arguments.depth)
    cm.run()

    logger.info(f' it took {(time.time() - start_time):.2f}')


