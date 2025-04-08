import enum
from datetime import datetime
from typing import List
import os
import smtplib
from email.mime.text import MIMEText

from loguru import logger
from link import Link

class EmailMode(enum.Enum):
    ALWAYS = "always"
    ON_ERROR = "on_error"
    NEVER = "never"


class EmailReportSender:
    """Handles the generation and sending of crawler reports via email."""

    REQUIRED_ENV_VARS = [
        "BLC_SENDER_SMTP_ADDRESS",
        "BLC_SENDER_SMTP_PORT",
        "BLC_SENDER_EMAIL",
        "BLC_SENDER_EMAIL_PASSWORD"
    ]

    def __init__(self, recipient: str):
        """
        Initialize the email sender using environment variables.

        Args:
            recipient: Recipient email address.

        Raises:
            EnvironmentError: If any required environment variable is missing.
        """
        self._check_required_env_vars()

        self.sender_smtp_address = os.getenv("BLC_SENDER_SMTP_ADDRESS")
        self.sender_smtp_port = int(os.getenv("BLC_SENDER_SMTP_PORT"))
        self.sender_email = os.getenv("BLC_SENDER_EMAIL")
        self.sender_password = os.getenv("BLC_SENDER_EMAIL_PASSWORD")
        self.recipient_email = recipient

    def _check_required_env_vars(self) -> None:
        """Validate that all required environment variables are defined."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if os.getenv(var) is None]
        if missing_vars:
            raise EnvironmentError(
                "Missing required environment variables: " + ", ".join(missing_vars)
            )

    def send_email_report(self, report_text: str) -> None:
        """
        Send the report via SMTP.

        Args:
            report_text: Plain text report content.
        """
        msg = MIMEText(report_text)
        msg['Subject'] = "Broken Links Crawler Report"
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email

        with smtplib.SMTP(self.sender_smtp_address, self.sender_smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

        logger.debug("Email sent successfully to {}", self.recipient_email)

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
            execution_time: Time taken by the crawler.
            visited_urls_num: Number of visited URLs.
            thread_num: Number of threads used.

        Returns:
            str: The full plain-text report.
        """
        lines = [
            "Subject: Crawler Report",
            "",
            "Crawler Report",
            "=" * 60,
            f"Generated at     : {datetime.utcnow().isoformat()}Z",
            f"Execution Time   : {execution_time}",
            f"Visited URLs     : {visited_urls_num}",
            f"Threads Used     : {thread_num}",
            "=" * 60,
            "",
            "Discovered Links:",
            "-" * 60
        ]

        for i, link in enumerate(links_list, start=1):
            lines.extend([
                f"[{i}] URL        : {link.url}",
                f"     Depth       : {link.depth}",
                f"     Appeared In : {link.first_found_on}",
                f"     Status      : {link.status.name.lower()}",
                f"     Error       : {link.error}",
                "-" * 60
            ])

        return "\n".join(lines)
