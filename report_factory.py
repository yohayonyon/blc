import enum

from HtmlReport import HtmlReport
from human_report import HumanReport
from json_report import JsonReport
from report import Report


class ReportType(enum.Enum):
    HUMAN = "human"
    JSON = "json"
    HTML = "html"


class ReportFactory:
    """Factory for creating report instances based on type."""

    @staticmethod
    def create_report(report_type: str) -> Report:
        """
        Create a report object.

        Args:
            report_type: Type of report ("human" or "json").

        Returns:
            A report instance.
        """
        match report_type:
            case ReportType.HUMAN.value:
                return HumanReport()
            case ReportType.JSON.value:
                return JsonReport()
            case ReportType.HTML.value:
                return HtmlReport()
