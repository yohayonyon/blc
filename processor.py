from abc import ABC, abstractmethod


class Processor(ABC):
    @abstractmethod
    def process(self, task):
        pass

    @abstractmethod
    def finalize(self):
        pass
