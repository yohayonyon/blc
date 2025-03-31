import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from link import Link, LinkStatus


def retry_if_not_404(exception):
    """Retry if the exception is a request exception but not a 404 error."""
    return isinstance(exception, requests.exceptions.RequestException) and (
        not (hasattr(exception.response, "status_code") and exception.response.status_code == 404)
    )


class Crawler:
    def __init__(self, target_url, crawler_id, url_queue, broken_links, url_queue_full_event, session, max_depth):

        self.target_url = target_url
        self.crawler_id = crawler_id
        self.url_queue = url_queue
        self.broken_links = broken_links
        self.url_queue_full_event = url_queue_full_event
        self.session = session
        self.max_depth = max_depth

        self.crawl_count = 0

    def is_valid_content_type(self, url):
        try:
            response = self.session.head(url, allow_redirects=True, timeout=5)
            content_type = response.headers.get("Content-Type", "")

            # Allow only text-based responses
            if content_type.startswith("text/html"):
                return True
            else:
                logger.debug(f"Skipping {url}, Content-Type: {content_type}")
                return False
        except requests.RequestException as e:
            logger.error(f"Error checking {url}: {e}")
            return False

    # implement a request retry
    # todo - fix timeout error, catch and handle max retries (sometimes it works manually. check why)
    # todo handle Hebrew links https://ece.technion.ac.il/wp-content/uploads/2022/12/%D7%9C%D7%95%D7%97-%D7%A7%D7%99%D7%A8-2022-23.pdf
    @retry(
        stop=stop_after_attempt(4),  # max retries
        wait=wait_exponential(multiplier=5, min=4, max=5),  # exponential backoff
        retry=retry_if_exception(retry_if_not_404)
    )
    def fetch_url(self, url):
        if self.is_valid_content_type(url):
            response = self.session.get(url)
            response.raise_for_status()
            return response
        return None

    def crawl(self):

        logger.debug(f'Crawler {self.crawler_id} started.')

        if self.crawler_id != 0:
            self.url_queue_full_event.wait()

        while not self.url_queue.empty():

            current_link = self.url_queue.get()

            if current_link.depth >= self.max_depth:
                continue

            # request the target URL
            logger.debug(f'Crawler {self.crawler_id}: depth - {current_link.depth}, url - {current_link.absolute_url}')
            try:
                response = self.fetch_url(current_link.absolute_url)
            except requests.exceptions.RequestException as e:
                if e.response.status_code == 404:
                    logger.debug(f'Crawler {self.crawler_id}: 404 - {current_link.absolute_url} referenced from '
                                 f'{current_link.appeared_in}')
                    current_link.status = LinkStatus.NOT_FOUND
                    self.broken_links.put(current_link)
                    break

            if response is not None:

                if current_link.absolute_url.startswith("http://") and response.url.startswith("https://"):
                    logger.debug(f'Crawler {self.crawler_id}: HTTP_INSTEAD_HTTPS - {current_link.absolute_url} '
                                 f'referenced from {current_link.appeared_in}')
                    current_link.status = LinkStatus.HTTP_INSTEAD_HTTPS
                    self.broken_links.put(current_link)
                    break

                # parse the HTML
                soup = BeautifulSoup(response.content, "html.parser", from_encoding="iso-8859-1")

                # collect all the links
                for link_element in soup.find_all("a", href=True):
                    url = link_element["href"]

                    # check if the URL is absolute or relative
                    if not url.startswith("http"):
                        absolute_url = requests.compat.urljoin(self.target_url, url)
                    else:
                        absolute_url = url

                    if absolute_url.startswith(self.target_url):
                        self.url_queue.put(Link(absolute_url, current_link.depth + 1, current_link.absolute_url))
                    else:
                        self.url_queue.put(Link(absolute_url, self.max_depth, current_link.absolute_url))

                        if not self.url_queue_full_event.is_set():
                            logger.debug(f'Crawler {self.crawler_id} setting url_queue_full_event.')
                            self.url_queue_full_event.set()

            if not self.url_queue_full_event.is_set():  # and this_crawler_count == self.workers_num:
                logger.debug(f'Crawler {self.crawler_id} setting url_queue_full_event.')
                self.url_queue_full_event.set()

        logger.debug(f'Crawler {self.crawler_id} finished.')
