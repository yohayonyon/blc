from enum import Enum
from typing import Any


class LinkStatus(Enum):
    """Enumeration of link statuses."""
    NOT_VISITED = -1
    VISITED = 0
    NO_SUCH_DOMAIN = 1
    NO_SUCH_PAGE = 2
    HTTP_INSTEAD_OF_HTTPS = 3
    OTHER_ERROR = 4


class Link:
    """Represents a link with metadata and status."""

    def __init__(
        self,
        url: str,
        depth: int,
        first_found_on: str,
        status: LinkStatus = LinkStatus.NOT_VISITED,
        error: str = ''
    ):
        """
        Initialize a Link object.

        Args:
            url: The URL of the link.
            depth: Depth level in the crawl.
            first_found_on: URL where this link was first found.
            status: Status of the link.
            error: Error message if any.
        """
        self.url = url
        self.depth = depth
        self.first_found_on = first_found_on
        self.status = status
        self.error = error

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Link) and self.url == other.url

    def __hash__(self) -> int:
        return hash(self.url)

    def __str__(self) -> str:
        link_str = f'{self.status.name.lower():20}, depth = {self.depth}: {self.first_found_on} ==> {self.url}'
        if self.status == LinkStatus.OTHER_ERROR:
            link_str += f', error: {self.error}'
        return link_str
