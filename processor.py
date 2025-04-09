from abc import ABC, abstractmethod
from typing import Any


class Processor(ABC):
    """Abstract base class for processing tasks."""

    @abstractmethod
    def process(self, task: Any) -> list[Any]:
        """
        Process a task and return a list of new tasks.

        Args:
            task: The task to process.

        Returns:
            A list of new tasks.
        """
        pass

    @abstractmethod
    def finalize(self) -> None:
        """
        Finalize the processor (e.g., cleanup or reporting).
        """
        pass

    @abstractmethod
    def initiate(self) -> None:
        """
        Initiate processing
        """
        pass
