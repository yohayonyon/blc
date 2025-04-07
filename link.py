from enum import Enum


class LinkStatus(Enum):
    NOT_VISITED = -1
    VISITED = 0
    NO_SUCH_DOMAIN = 1
    NO_SUCH_PAGE = 2
    HTTP_INSTEAD_OF_HTTPS = 3
    OTHER_ERROR = 4


class Link:
    def __init__(self, url, depth, first_found_on, status=LinkStatus.NOT_VISITED, error=''):
        self.url = url
        self.depth = depth
        self.first_found_on = first_found_on
        self.status = status
        self.error = error

    def __eq__(self, other):
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        link_str = f'{self.status.name.lower():20}, depth = {self.depth}: {self.first_found_on} ==> {self.url}'
        if self.status == LinkStatus.OTHER_ERROR:
            link_str += f', error: {self.error}'
        return link_str
