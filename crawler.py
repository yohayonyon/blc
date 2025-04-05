import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from link import Link, LinkStatus
from processor import Processor


def retry_if_not_404(exception):
    """Retry if the exception is a request exception but not a 404 error."""
    return isinstance(exception, requests.exceptions.RequestException) and (
        not (hasattr(exception.response, "status_code") and exception.response.status_code == 404)
    )


class Crawler(Processor):
    def __init__(self, target_url, broken_links, broken_links_lock, session, max_depth):

        self.target_url = target_url
        self.broken_links = broken_links
        self.broken_links_lock = broken_links_lock
        self.session = session
        self.max_depth = max_depth

    def add_error_to_report(self, link, error_type, error=''):
        link.status = error_type
        link.error = error
        if error_type == LinkStatus.OTHER_ERROR:
            logger.error(f'Adding to broken links - {link.url}')
        else:
            logger.debug(f'Adding to broken links - {link.url}')
        with self.broken_links_lock:
            self.broken_links.append(link)

    # implement a request retry
    # todo - fix timeout error, catch and handle max retries (sometimes it works manually. check why)
    # todo handle Hebrew links https://ece.technion.ac.il/wp-content/uploads/2022/12/%D7%9C%D7%95%D7%97-%D7%A7%D7%99%D7%A8-2022-23.pdf
    @retry(
        stop=stop_after_attempt(4),  # max retries
        wait=wait_exponential(multiplier=5, min=4, max=5),  # exponential backoff
        retry=retry_if_exception(retry_if_not_404)
    )
    def fetch_url(self, link):
        url = link.url

        try:
            # 1st get header
            response = self.session.head(url, allow_redirects=True, timeout=5)
            logger.debug(f'Header request status - {response.status_code}')

            if response.status_code == 404:
                self.add_error_to_report(link, LinkStatus.NO_SUCH_PAGE)
                return None

            # Document http instead of https and continue crawling
            if link.url.startswith("http://") and response.url.startswith("https://"):
                self.add_error_to_report(link, LinkStatus.HTTP_INSTEAD_HTTPS)

            # Don't fetch non text/html pages
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("text/html"):
                logger.debug(f"skipping fetching the page {url} since Content-Type is "
                             f"{content_type}")
                return None

            # Don't fetch pages under other domain
            if not link.url.startswith(self.target_url):
                logger.debug(f'{link.url} is not under {self.target_url}, so not fetching and parsing page.')
                return None

            # Don't fetch pages is their depth is maximal
            if link.depth == self.max_depth:
                logger.debug(f'The depth of {link.url} is maximal, so the page itself will not be fetched and '
                             f'parsed.')
                return None

            # fetch the page
            response = self.session.get(url)
            response.raise_for_status()  # Raise error for 4xx/5xx
            logger.debug(f'Page request successful - {response.status_code}')

        except requests.exceptions.RetryError as e:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))
            return None
        except requests.exceptions.HTTPError as e:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR,
                                     f"HTTPError: {e.response.status_code} - {e.response.reason}")
            return None
        except requests.exceptions.Timeout as e:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, f"TimeoutError: Request took too long.")
            return None
        except requests.exceptions.ConnectionError as e:
            if "[Errno 11001] getaddrinfo failed" in str(e.args[0].reason):
                self.add_error_to_report(link, LinkStatus.NO_SUCH_DOMAIN)
            else:
                self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))
            return None
        except requests.exceptions.RequestException as e:
            if e.response.status_code == 404:
                self.add_error_to_report(link, LinkStatus.NO_SUCH_PAGE)
            else:
                self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))
            return None

        return response

    def process(self, task):
        current_link = task

        # request the target URL
        logger.debug(f'Handling {str(current_link)}')
        response = self.fetch_url(current_link)

        new_links = []
        if response is not None:
            new_links = self.parse_and_get_links(response, current_link)

        return new_links

    def parse_and_get_links(self, response, current_link):
        logger.debug(f'Parsing {current_link.url}')
        soup = BeautifulSoup(response.content, "html.parser", from_encoding="iso-8859-1")

        # collect all the links
        found_links = []
        for link_element in soup.find_all("a", href=True):
            url = link_element["href"]

            # alink to section in the same page - ignore
            if url.startswith('#'):
                continue

            # if relative address make absolute
            url = requests.compat.urljoin(self.target_url, url)

            # a non URL link - ignore
            if not url.startswith('http'):
                logger.debug(f'Ignoring {url}')
                continue

            # a link under the target URL - a new full crawl destination
            if url.startswith(self.target_url):
                found_links.append(Link(url, current_link.depth + 1, current_link.url))
            # a link not under the target URL - check it and stop crawling
            else:
                found_links.append(Link(url, self.max_depth, current_link.url))

        logger.debug(f'Finished parsing. {len(found_links)} links were found.')
        return found_links

    def finalize(self):
        pass
