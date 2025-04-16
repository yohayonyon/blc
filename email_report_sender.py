import enum
import json
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger


class EmailMode(enum.Enum):
    ALWAYS = "always"
    ON_ERROR = "on_error"
    NEVER = "never"


class EmailReportSender:
    """Handles the generation and sending of crawler reports via email."""
    def __init__(self, recipient_email: str, report_type, config_path="email_config.json"):
        self.recipient_email = recipient_email
        self.report_type = report_type
        self.config_path = config_path

        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Email config file '{self.config_path}' not found.")

        with open(self.config_path, "r") as f:
            config = json.load(f)

        self.smtp_address = config.get("smtp_address")
        self.smtp_port = int(config.get("smtp_port", 587))
        self.sender_email = config.get("sender_email")
        self.sender_password = config.get("sender_password")

        missing = [k for k in ["smtp_address", "smtp_port", "sender_email", "sender_password"] if not config.get(k)]
        if missing:
            raise ValueError(f"Missing email config values: {', '.join(missing)}")

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

        with smtplib.SMTP(self.smtp_address, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

        logger.debug("Email sent successfully to {}", self.recipient_email)
