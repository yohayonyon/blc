import os
from urllib.parse import urlparse, quote, urlunparse

import certifi
import requests
import urllib3
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from link import Link, LinkStatus
from processor import Processor


def retry_if_not_404(exception):
    """Retry if the exception is a request exception but not a 404 error."""
    return isinstance(exception, requests.exceptions.RequestException) and (
        not (hasattr(exception.response, "status_code") and exception.response.status_code == 404)
    )


def normalize_url(url):
    parsed = urlparse(url)
    # Encode the domain name using idna
    netloc = parsed.netloc.encode('idna').decode('ascii')
    # Percent-encode the path and query
    path = quote(parsed.path)
    query = quote(parsed.query, safe='=&')
    # Reconstruct the URL
    return urlunparse((parsed.scheme, netloc, path, parsed.params, query, parsed.fragment))


class Crawler(Processor):
    session = requests.Session()

    def __init__(self, target_url, broken_links, broken_links_lock, max_depth):
        self.target_url = normalize_url(target_url)
        self.broken_links = broken_links
        self.broken_links_lock = broken_links_lock
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

        # todo
        # Read robots.txt and decide if to continue
        # robots = RobotsTxtHandler(url, user_agent="MyCrawlerBot")
        # if not robots.can_fetch(url):
        #     self.add_error_to_report(link, LinkStatus.OTHER_ERROR, "Cannot fetch according to robots.txt")
        #     return None
        #
        # # todo
        # if os.name == "Linux":
        #     verify = "/etc/ssl/certs/ca-certificates.crt"
        # else:
        #     verify = certifi.where()

        try:
            # 1st get header
            # === Attempt 1: Normal SSL Verification ===
            try:
                verify = certifi.where()
                response = self.session.head(url, verify=verify, timeout=10)
                response.raise_for_status()
                logger.debug(
                    f'Successfully (status {response.status_code}) fetched header with SSL verification: {url}')

            # === SSL Error: Retry with verify=False ===
            except requests.exceptions.SSLError as ssl_err:
                logger.warning(f"SSL verification failed for {url}, retrying without verification: {ssl_err}")
                try:
                    verify = False
                    response = self.session.head(url, verify=verify, timeout=10)
                    response.raise_for_status()
                    logger.debug(
                        f"Successfully (status {response.status_code}) fetched header without SSL verification: {url}")
                except requests.exceptions.SSLError as ssl_err:
                    self.add_error_to_report(link, LinkStatus.OTHER_ERROR, f"SSL fallback also failed: {ssl_err}")

            if response.status_code == 404:
                self.add_error_to_report(link, LinkStatus.NO_SUCH_PAGE)
                return None

            # Document http instead of https and continue crawling
            if link.url.startswith("http://") and response.url.startswith("https://"):
                self.add_error_to_report(link, LinkStatus.HTTP_INSTEAD_OF_HTTPS)

            # Don't fetch non text/html pages
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("text/html"):
                logger.debug(f"Skipping {url} due to non-HTML content type: {content_type}")
                return None

            # Don't fetch pages under other domain
            if not link.url.startswith(self.target_url):
                logger.debug(f'{link.url} is outside of {self.target_url}, skipping.')
                return None

            # Don't fetch pages is their depth is maximal
            if link.depth == self.max_depth:
                logger.debug(f'Depth limit reached for {link.url}')
                return None

            # fetch the page
            response = self.session.get(url, verify=verify)
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
            if os.name == "nt":
                no_domain_windows_string = "[Errno 11001] getaddrinfo failed"
            elif os.name == "posix":
                no_domain_windows_string = "[Errno -2] Name or service not known"
            else:
                no_domain_windows_string = ""
            if no_domain_windows_string in str(e.args[0].reason):
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

        found_links = []
        for link_element in soup.find_all("a", href=True):
            url = link_element["href"]
            url = requests.compat.urljoin(self.target_url, url)

            # a non URL link - ignore
            if not url.startswith('http'):
                logger.debug(f'Ignoring {url}')
                continue

            url = normalize_url(url)

            if url.startswith(f'{current_link.url}#'):
                logger.debug(f'A new link - other section on the same page was found, so check it and stop.')
                found_links.append(Link(url, self.max_depth, current_link.url))
            if url.startswith(self.target_url):
                logger.debug(f'A new link to crawl')
                found_links.append(Link(url, current_link.depth + 1, current_link.url))
            else:
                logger.debug(f'A new link - not under the target domain, so check it and stop.')
                found_links.append(Link(url, self.max_depth, current_link.url))

        logger.debug(f'Finished parsing. {len(found_links)} links were found.')
        return found_links

    def finalize(self):
        pass
