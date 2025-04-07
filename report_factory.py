from human_report import HumanReport
from json_report import JsonReport
from report import Report


class ReportGenerator:
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
            case "human":
                return HumanReport()
            case "json":
                return JsonReport()
