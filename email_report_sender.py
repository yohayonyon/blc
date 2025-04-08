import enum
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from loguru import logger


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

    def __init__(self, recipient: str, report_type: str):
        """
        Initialize the email sender using environment variables.

        Args:
            recipient: Recipient email address.
            report_type: Report format - 'human', 'html', or 'json'.
        """
        self._check_required_env_vars()

        self.sender_smtp_address = os.getenv("BLC_SENDER_SMTP_ADDRESS")
        self.sender_smtp_port = int(os.getenv("BLC_SENDER_SMTP_PORT"))
        self.sender_email = os.getenv("BLC_SENDER_EMAIL")
        self.sender_password = os.getenv("BLC_SENDER_EMAIL_PASSWORD")
        self.recipient_email = recipient
        self.report_type = report_type.lower()

    def _check_required_env_vars(self) -> None:
        """Validate that all required environment variables are defined."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if os.getenv(var) is None]
        if missing_vars:
            raise EnvironmentError(
                "Missing required environment variables: " + ", ".join(missing_vars)
            )

    def send_email_report(self, report_path: str) -> None:
        """
        Send the report via email. Uses the report path to determine format.

        Args:
            report_path: Path to the report file.
        """
        msg = MIMEMultipart()
        msg['Subject'] = "Broken Links Crawler Report"
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email

        match self.report_type:
            case "human":
                with open(report_path, "r", encoding="utf-8") as f:
                    report_text = f.read()
                msg.attach(MIMEText(report_text, "plain"))

            case "html":
                with open(report_path, "r", encoding="utf-8") as f:
                    report_html = f.read()
                msg.attach(MIMEText(report_html, "html"))

            case "json":
                with open(report_path, "rb") as f:
                    part = MIMEApplication(f.read(), _subtype="json")
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(report_path)
                    )
                    msg.attach(part)

            case _:
                raise ValueError(f"Unsupported report type: {self.report_type}")

        with smtplib.SMTP(self.sender_smtp_address, self.sender_smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

        logger.debug("Email sent successfully to {}", self.recipient_email)
