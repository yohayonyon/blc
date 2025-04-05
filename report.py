from abc import ABC, abstractmethod


class Report(ABC):

    @abstractmethod
    def generate(self, file_name, links, execution_time, visited_urls_num, thread_num):
        pass
