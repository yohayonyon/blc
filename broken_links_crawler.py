from crawlers_manager import CrawlesManager
from subscripable_put_once_q import SubscripablePutOnceQ
from subscripable_put_q import SubscripablePutQ


class BrokenLinksCrawler:
    def __init__(self, target_url, workers_num, depth):
        if target_url[-1] == '/':
            self.target_url = target_url[:-1]
        else:
            self.target_url = target_url
        self.workers_num = workers_num
        self.depth = depth
        self.links_to_visit = SubscripablePutOnceQ()
        self.broken_links = SubscripablePutQ()

    def start(self):
        cm = CrawlesManager(self.target_url, self.workers_num, self.depth, self.links_to_visit, self.broken_links)
        cm.run()
