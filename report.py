from abc import ABC, abstractmethod
from typing import Any


class Report(ABC):
    """Abstract base class for all report types."""

    @abstractmethod
    def generate(
        self,
        file_name: str,
        links: list[Any],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> None:
        """
        Generate a report and save it to a file.

        Args:
            file_name: Name of the output file.
            links: List of Link objects.
            execution_time: Time taken to run the crawler.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.
        """
        pass
