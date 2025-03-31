from enum import Enum


class LinkStatus(Enum):
    NOT_VISITED = -1
    VISITED = 0
    NOT_FOUND = 1
    HTTP_INSTEAD_HTTPS = 2


class Link:
    def __init__(self, absolute_url, depth, appeared_in, status=LinkStatus.NOT_VISITED):
        self.absolute_url = absolute_url
        self.depth = depth
        self.appeared_in = appeared_in
        self.status = status

    def __eq__(self, other):
        return self.absolute_url == other.absolute_url

    def __hash__(self):
        return hash(self.absolute_url)
