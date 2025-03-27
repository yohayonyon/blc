import time
from loguru import logger
from crawlers_manager import CrawlesManager

target_url = "https://www.scrapingcourse.com/ecommerce/"
for num_workers in range(4, 5):
    start_time = time.time()

    cm = CrawlesManager(target_url=target_url)     #, workers_num=4, max_crawl=20)
    cm.run()

    logger.info(f' it took {(time.time() - start_time):.2f}')
