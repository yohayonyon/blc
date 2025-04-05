from human_report import HumanReport
from json_report import JsonReport


class ReportGenerator:
    @staticmethod
    def create_report(report_type):
        match report_type:
            case "human":
                return HumanReport()
            case "json":
                pass
                return JsonReport()
