from abc import ABC, abstractmethod
from typing import Any


class Report(ABC):
    """Abstract base class for all report types."""

    @abstractmethod
    def generate(
            self,
            target_url: str,
            broken_links: list[Any],
            other_error_links: list[Any],
            execution_time: str,
            visited_urls_num: int,
            thread_num: int
    ) -> str:
        pass
