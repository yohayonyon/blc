import json
import os
import platform
import threading
import time
from collections import defaultdict
from typing import List, Optional
from urllib.parse import urlparse, quote, urlunparse
from urllib.robotparser import RobotFileParser

import requests
import urllib3
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from link import Link, LinkStatus
from processor import Processor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def retry_if_not_404(exception: Exception) -> bool:
    return isinstance(exception, requests.exceptions.RequestException) and (
        not (hasattr(exception.response, "status_code") and exception.response.status_code == 404)
    )


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    netloc = parsed.netloc.encode('idna').decode('ascii')
    path = quote(parsed.path)
    query = quote(parsed.query, safe='=&')
    return urlunparse((parsed.scheme, netloc, path, parsed.params, query, parsed.fragment))


class Crawler(Processor):
    def __init__(self, target_url: str, max_depth: int):
        self.target_url = normalize_url(target_url)
        self.max_depth = max_depth
        self.sessions = dict()
        self.non_crawling_domains = self._load_non_crawling_domains()
        self.domain_last_access = dict()
        self.crawl_delays = dict()
        self.robots_parsers = dict()
        self.domain_locks = defaultdict(threading.Lock)
        self.broken_links = []
        self.broken_links_lock = threading.Lock()
        self.other_error_links = []
        self.other_error_links_lock = threading.Lock()

    @staticmethod
    def _load_non_crawling_domains():
        try:
            with open('non_crawling_urls.json', 'r') as f:
                data = json.load(f)
                return set(data.get('domains', []))
        except Exception as e:
            logger.warning(f"Could not load non-crawling domains list: {e}")
            return set()

    def _is_known_non_crawling(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            return any(domain in hostname for domain in self.non_crawling_domains)
        except Exception as e:
            logger.debug(f"Error parsing URL in _is_known_non_crawling: {e}")
            return False

    def _get_robots_parser(self, domain: str) -> RobotFileParser:
        if domain in self.robots_parsers:
            return self.robots_parsers[domain]

        robots_url = f"https://{domain}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
            self.robots_parsers[domain] = parser
        except Exception as e:
            logger.debug(f"Could not read robots.txt for {domain}: {e}")
            parser = RobotFileParser()
            parser.parse("")  # Empty rules (allow all)
            self.robots_parsers[domain] = parser
        return parser

    def _get_crawl_delay(self, domain: str) -> float:
        if domain in self.crawl_delays:
            return self.crawl_delays[domain]

        parser = self._get_robots_parser(domain)
        delay = parser.crawl_delay("*")
        self.crawl_delays[domain] = delay if delay is not None else 0
        return self.crawl_delays[domain]

    def _respect_crawl_delay(self, domain: str):
        with self.domain_locks[domain]:
            delay = self._get_crawl_delay(domain)
            last_access = self.domain_last_access.get(domain, 0)
            now = time.time()
            wait_time = (last_access + delay) - now
            if wait_time > 0:
                logger.debug(f"[{domain}] Sleeping {wait_time:.2f}s due to crawl-delay of {delay}s")
                time.sleep(wait_time)
            self.domain_last_access[domain] = time.time()

    def add_error_to_report(self, link: Link, error_type: LinkStatus, error: str = '') -> None:
        link.status = error_type
        link.error = error
        log_fn = logger.error if error_type == LinkStatus.OTHER_ERROR else logger.debug
        log_fn(f'Adding to broken links - {link.url}')
        if error_type == LinkStatus.OTHER_ERROR:
            with self.other_error_links_lock:
                self.other_error_links.append(link)
        else:
            with self.broken_links_lock:
                self.broken_links.append(link)

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=5, min=4, max=5),
        retry=retry_if_exception(retry_if_not_404)
    )
    def fetch_url(self, link: Link, session) -> Optional[requests.Response]:
        url = link.url
        parsed = urlparse(url)
        domain = parsed.netloc
        self._respect_crawl_delay(domain)

        try:
            response = session.head(url, verify=False, allow_redirects=True, timeout=10)
            response.raise_for_status()
            logger.debug(f'Successfully (status {response.status_code}) fetched header: {url}')

            if url.startswith("http://") and response.url.startswith("https://"):
                self.add_error_to_report(link, LinkStatus.HTTP_INSTEAD_OF_HTTPS)

            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("text/html"):
                logger.debug(f"Skipping {url} due to non-HTML content type: {content_type}")
                return None

            if not link.url.startswith(self.target_url):
                logger.debug(f'{link.url} is outside of {self.target_url}, skipping.')
                return None

            if self._is_known_non_crawling(url):
                logger.debug(f'{link.url} is known as non-crawler friendly, skipping.')
                return None

            if link.depth == self.max_depth:
                logger.debug(f'Depth limit reached for {link.url}')
                return None

            response = session.get(url, verify=False)
            response.raise_for_status()
            logger.debug(f'Page request successful - {response.status_code}')
            return response

        except requests.exceptions.RetryError as e:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, str(e))
        except requests.exceptions.HTTPError as e:
            if hasattr(e, "response"):
                if e.response.status_code == 404:
                    self.add_error_to_report(link, LinkStatus.NO_SUCH_PAGE)
                else:
                    self.add_error_to_report(link, LinkStatus.OTHER_ERROR,
                                             f"HTTPError: {e.response.status_code} - {e.response.reason}")
        except requests.exceptions.Timeout:
            self.add_error_to_report(link, LinkStatus.OTHER_ERROR, "TimeoutError: Request took too long.")
        except requests.exceptions.ConnectionError as e:
            no_domain_str = {
                "nt": "[Errno 11001] getaddrinfo failed",  # Windows
                "posix": "[Errno -2] Name or service not known",  # Linux/macOS
                "java": "[Errno 7] nodename nor servname provided, or not known",  # Jython or Java environments
                "os2": "[Errno 1001] Host not found",  # OS/2
                "ce": "[Errno 11001] getaddrinfo failed",  # Windows CE
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
        logger.debug(f'Handling {str(task)}')
        session = self.sessions[threading.current_thread().name]
        response = self.fetch_url(task, session)
        return self.parse_and_get_links(response, task) if response else []

    def parse_and_get_links(self, response: requests.Response, current_link: Link) -> List[Link]:
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
                logger.debug(f'Section on the same page found: {url}')
                found_links.append(Link(url, self.max_depth, current_link.url))
            elif url.startswith(self.target_url):
                logger.debug(f'Internal link found: {url}')
                found_links.append(Link(url, current_link.depth + 1, current_link.url))
            else:
                logger.debug(f'External link found: {url}')
                found_links.append(Link(url, self.max_depth, current_link.url))

        logger.debug(f'Finished parsing. {len(found_links)} links were found.')
        return found_links

    def finalize(self) -> None:
        pass

    def initiate(self) -> None:
        system = platform.system()
        if system == "Windows":
            os_info = "Windows NT 10.0; Win64; x64"
        elif system == "Darwin":  # macOS
            os_info = "Macintosh; Intel Mac OS X 10_15_7"
        elif system == "Linux":
            os_info = "X11; Linux x86_64"
        else:
            os_info = "X11; Unknown OS"

        user_agent = (
            f"Mozilla/5.0 ({os_info}) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )

        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})
        self.sessions[threading.current_thread().name] = session
        logger.debug(f'Created session with User-Agent for {system}: {user_agent}')

    def get_broken_links(self):
        return self.broken_links

    def get_other_error_links(self):
        return self.other_error_links
