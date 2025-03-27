import requests
from bs4 import BeautifulSoup
from queue import Queue
from tenacity import retry, stop_after_attempt, wait_exponential
import threading
from loguru import logger


class CrawlesManager:

    def __init__(self, target_url, workers_num=4, max_crawl=5):

        self.url_queue = Queue()
        self.url_queue.put(target_url)
        self.target_url = target_url

        self.max_crawl = max_crawl
        self.crawl_count = 0

        self.workers_num = workers_num

        # define a thread-safe set for visited URLs
        self.visited_urls = set()
        self.visited_lock = threading.Lock()

        self.session = requests.Session()

        self.first_crawler_lock = threading.Lock()

        logger.info(f"{workers_num} crawlers will fetch {max_crawl} pages each.")

    def run(self):
        # specify the number of threads to use
        threads = []

        # start worker threads
        for i in range(self.workers_num):
            thread = threading.Thread(target=self.crawler, args=(i, ))
            threads.append(thread)

        for thread in threads:
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()

    # implement a request retry
    @retry(
        stop=stop_after_attempt(4),  # max retries
        wait=wait_exponential(multiplier=5, min=4, max=5),  # exponential backoff
    )
    def fetch_url(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        return response

    def crawler(self, crawler_id):

        logger.debug(f'Crawler {crawler_id} started.')

        self.first_crawler_lock.acquire()

        logger.trace("1")
        while not self.url_queue.empty() and self.crawl_count < self.max_crawl:

            # update the priority queue
            if not self.url_queue.empty():
                current_url = self.url_queue.get()
            else:
                break

            with self.visited_lock:
                if current_url in self.visited_urls:
                    continue

                # add the current URL to the URL set
                self.visited_urls.add(current_url)

            # request the target URL
            logger.debug(f'Crawler {crawler_id} is fetching {current_url}')
            response = self.fetch_url(current_url)

            # parse the HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # collect all the links
            new_links_cnt = 0
            for link_element in soup.find_all("a", href=True):
                url = link_element["href"]

                # check if the URL is absolute or relative
                if not url.startswith("http"):
                    absolute_url = requests.compat.urljoin(self.target_url, url)
                else:
                    absolute_url = url

                if absolute_url.startswith(self.target_url):
                    with self.visited_lock:
                        # ensure the crawled link belongs to the target domain and hasn't been visited
                        if absolute_url not in self.visited_urls:
                            self.url_queue.put(absolute_url)

                            if self.first_crawler_lock.locked():   # and this_crawler_count == self.workers_num:
                                logger.debug(f'Crawler {crawler_id} releasing first_crawler_lock.')
                                self.first_crawler_lock.release()

                            new_links_cnt += 1

            if self.first_crawler_lock.locked():    # and this_crawler_count < self.workers_num:
                logger.debug(f'Crawler {crawler_id} releasing first_crawler_lock.')
                self.first_crawler_lock.release()

            # update the crawl count
            self.crawl_count += 1
            # this_crawler_count += 1

        logger.debug(f'Crawler {crawler_id} finished.')
