from datetime import datetime
from typing import List
import json
from loguru import logger
from link import Link


class EmailReportSender:
    """Handles generation and sending of crawler reports via email."""

    def __init__(self, config_path: str, recipient: str):
        """
        Initialize the email sender from a config file.

        Args:
            config_path: Path to a JSON config file with email credentials.
            recipient: Recipient email address.
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.sender = config.get("EMAIL_SENDER")
        self.password = config.get("EMAIL_PASSWORD")
        self.smtp_address = config.get("SMTP_ADDRESS")
        self.smtp_port = config.get("SMTP_PORT")
        self.recipient = recipient

    def generate_and_send(
        self,
        report_file_name: str,
        links_list: List[Link],
        execution_time: str,
        visited_urls_num: int,
        thread_num: int
    ) -> None:
        """
        Generate the email report and send it.

        Args:
            report_file_name: Report file name (unused, for future use).
            links_list: List of Link objects.
            execution_time: Time taken by crawler.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.
        """
        email_body = self.generate_email_body(
            report_file_name, links_list, execution_time, visited_urls_num, thread_num
        )
        self.send_email_report(self.sender, self.password, email_body)

    def send_email_report(self, email: str, password: str, report_text: str) -> None:
        """
        Send the report via SMTP.

        Args:
            email: Sender email.
            password: Sender password.
            report_text: Plain text report content.
        """
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(report_text)
        msg['Subject'] = "Broken Links Crawler Report"
        msg['From'] = self.sender
        msg['To'] = self.recipient

        with smtplib.SMTP(self.smtp_address, self.smtp_port) as server:
            server.starttls()
            server.login(email, password)
            server.send_message(msg)

        logger.debug("Email sent.")

    @staticmethod
    def generate_email_body(
        report_file_name: str,
        links_list: List[Link],
        execution_time: float,
        visited_urls_num: int,
        thread_num: int
    ) -> str:
        """
        Generate a plain-text crawler report for email.

        Args:
            report_file_name: File to save report (currently unused).
            links_list: List of Link objects.
            execution_time: Time taken by crawler.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.

        Returns:
            str: The full plain-text report as a string.
        """
        lines = [
            "Subject: Crawler Report", "", "Crawler Report", "=" * 60,
            f"Generated at     : {datetime.utcnow().isoformat()}Z",
            f"Execution Time   : {execution_time}",
            f"Visited URLs     : {visited_urls_num}",
            f"Threads Used     : {thread_num}",
            "=" * 60, "", "Discovered Links:", "-" * 60
        ]

        for i, link in enumerate(links_list, start=1):
            lines += [
                f"[{i}] URL        : {link.url}",
                f"     Depth       : {link.depth}",
                f"     Appeared In : {link.first_found_on}",
                f"     Status      : {link.status.name.lower()}",
                f"     Error       : {link.error}",
                "-" * 60
            ]

        return "\n".join(lines)
