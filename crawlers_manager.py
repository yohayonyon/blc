import threading

import requests
from loguru import logger

from crawler import Crawler
from link import Link


class CrawlesManager:

    def __init__(self, target_url, workers_num, depth, links_to_visit, broken_links):

        self.target_url = target_url
        self.workers_num = workers_num
        self.depth = depth
        self.links_to_visit = links_to_visit
        self.broken_links = broken_links

        self.links_to_visit.put(Link(target_url, 0, 'user'))

        self.session = requests.Session()

        self.url_queue_full_event = threading.Event()

        self.crawlers = [
            Crawler(target_url, i, links_to_visit, broken_links, self.url_queue_full_event, self.session, depth)
            for i in range(workers_num)]

        logger.info(f"crawlers num - {workers_num}, max depth -  {depth}")

    def run(self):
        # specify the number of threads to use
        threads = []

        # start worker threads
        for crawler in self.crawlers:
            thread = threading.Thread(target=crawler.crawl)
            threads.append(thread)

        for thread in threads:
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()
        # todo - why not as expected?
        logger.info(f"Fetched {self.links_to_visit.get_handled_num()} pages.")
        logger.info(f'Found {len(self.broken_links)} broken links.')
