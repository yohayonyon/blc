import os
import threading
from urllib.parse import urlparse, quote, urlunparse
from typing import List, Optional

import certifi
import requests
import urllib3
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from link import Link, LinkStatus
from processor import Processor


def retry_if_not_404(exception: Exception) -> bool:
    """Retry if the exception is a request exception but not a 404 error."""
    return isinstance(exception, requests.exceptions.RequestException) and (
        not (hasattr(exception.response, "status_code") and exception.response.status_code == 404)
    )


def normalize_url(url: str) -> str:
    """Normalize and encode a URL."""
    parsed = urlparse(url)
    netloc = parsed.netloc.encode('idna').decode('ascii')
    path = quote(parsed.path)
    query = quote(parsed.query, safe='=&')
    return urlunparse((parsed.scheme, netloc, path, parsed.params, query, parsed.fragment))


class Crawler(Processor):
    """Crawler class that processes and extracts links from HTML pages."""

    session = requests.Session()

    def __init__(self, target_url: str, broken_links: List[Link], broken_links_lock: threading.Lock, max_depth: int):
        """
        Initialize the crawler.

        Args:
            target_url: Root URL to crawl.
            broken_links: Shared list to store broken links.
            broken_links_lock: Thread-safe lock for the broken links list.
            max_depth: Max crawl depth allowed.
        """
        self.target_url = normalize_url(target_url)
        self.broken_links = broken_links
        self.broken_links_lock = broken_links_lock
        self.max_depth = max_depth

    def add_error_to_report(self, link: Link, error_type: LinkStatus, error: str = '') -> None:
        """Set error info for a link and add it to the broken links report."""
        link.status = error_type
        link.error = error
        log_fn = logger.error if error_type == LinkStatus.OTHER_ERROR else logger.debug
        log_fn(f'Adding to broken links - {link.url}')
        with self.broken_links_lock:
            self.broken_links.append(link)

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=5, min=4, max=5),
        retry=retry_if_exception(retry_if_not_404)
    )
    def fetch_url(self, link: Link) -> Optional[requests.Response]:
        """
        Fetch a page and handle SSL, errors, redirects, and filtering.

        Args:
            link: The Link to fetch.

        Returns:
            A requests.Response object or None.
        """
        url = link.url

        try:
            try:
                verify = certifi.where()
                response = self.session.head(url, verify=verify, timeout=10)
                response.raise_for_status()
                logger.debug(f'Successfully (status {response.status_code}) fetched header with SSL verification: {url}')
            except requests.exceptions.SSLError as ssl_err:
                logger.warning(f"SSL verification failed for {url}, retrying without verification: {ssl_err}")
                try:
                    verify = False
                    response = self.session.head(url, verify=verify, timeout=10)
                    response.raise_for_status()
                    logger.debug(f"Successfully (status {response.status_code}) fetched header without SSL verification: {url}")
                except requests.exceptions.SSLError as ssl_err:
                    self.add_error_to_report(link, LinkStatus.OTHER_ERROR, f"SSL fallback also failed: {ssl_err}")
                    return None

            if response.status_code == 404:
                self.add_error_to_report(link, LinkStatus.NO_SUCH_PAGE)
                return None

            if link.url.startswith("http://") and response.url.startswith("https://"):
                self.add_error_to_report(link, LinkStatus.HTTP_INSTEAD_OF_HTTPS)

            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("text/html"):
                logger.debug(f"Skipping {url} due to non-HTML content type: {content_type}")
                return None

            if not link.url.startswith(self.target_url):
                logger.debug(f'{link.url} is outside of {self.target_url}, skipping.')
                return None

            if link.depth == self.max_depth:
                logger.debug(f'Depth limit reached for {link.url}')
                return None

            response = self.session.get(url, verify=verify)
            response.raise_for_status()
            logger.debug(f'Page request successful - {response.status_code}')
            return response

        except requests.exceptions.RetryError as e:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))
        except requests.exceptions.HTTPError as e:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, f"HTTPError: {e.response.status_code} - {e.response.reason}")
        except requests.exceptions.Timeout:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, "TimeoutError: Request took too long.")
        except requests.exceptions.ConnectionError as e:
            no_domain_str = {
                "nt": "[Errno 11001] getaddrinfo failed",
                "posix": "[Errno -2] Name or service not known"
            }.get(os.name, "")
            if no_domain_str in str(e.args[0].reason):
                self.add_error_to_report(link, LinkStatus.NO_SUCH_DOMAIN)
            else:
                self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))
        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response and e.response.status_code == 404:
                self.add_error_to_report(link, LinkStatus.NO_SUCH_PAGE)
            else:
                self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))

        return None

    def process(self, task: Link) -> List[Link]:
        """
        Process a link and return new links to crawl.

        Args:
            task: The link to process.

        Returns:
            A list of discovered links.
        """
        logger.debug(f'Handling {str(task)}')
        response = self.fetch_url(task)
        return self.parse_and_get_links(response, task) if response else []

    def parse_and_get_links(self, response: requests.Response, current_link: Link) -> List[Link]:
        """
        Extract links from a page.

        Args:
            response: Fetched HTML response.
            current_link: The link being processed.

        Returns:
            A list of new Link objects.
        """
        logger.debug(f'Parsing {current_link.url}')
        soup = BeautifulSoup(response.content, "html.parser", from_encoding="iso-8859-1")
        found_links: List[Link] = []

        for link_element in soup.find_all("a", href=True):
            url = requests.compat.urljoin(self.target_url, link_element["href"])
            if not url.startswith('http'):
                logger.debug(f'Ignoring {url}')
                continue
            url = normalize_url(url)

            if url.startswith(f'{current_link.url}#'):
                logger.debug('Section on the same page found.')
                found_links.append(Link(url, self.max_depth, current_link.url))
            elif url.startswith(self.target_url):
                logger.debug('Internal link found.')
                found_links.append(Link(url, current_link.depth + 1, current_link.url))
            else:
                logger.debug('External link found.')
                found_links.append(Link(url, self.max_depth, current_link.url))

        logger.debug(f'Finished parsing. {len(found_links)} links were found.')
        return found_links

    def finalize(self) -> None:
        """Finalize processing (no-op for now)."""
        pass
